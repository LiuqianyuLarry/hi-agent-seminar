"""Application-controlled dispatcher. Supports one remote spec tool, never arbitrary code."""
import json,inspect,time
from dataclasses import dataclass
from typing import Callable
from pydantic import ValidationError
from schemas import ToolResult,StatsData,SpecData,QueryData,ToolFailure,fail
from tool_definitions import ARG_TYPES
from tools.calculation import temperature_stats
from tools.engineering import get_machine_spec
from tools.sql_query import query_temperature

HANDLERS={'temperature_stats':temperature_stats,'query_temperature':query_temperature,
          'get_machine_spec':get_machine_spec}
RESULT_TYPES={'temperature_stats':StatsData,'query_temperature':QueryData,'get_machine_spec':SpecData}

@dataclass(frozen=True)
class AccessPolicy:
    allowed_tools:frozenset=frozenset(HANDLERS)
    # None means all machine IDs in the classroom query scope. This is not production authentication.
    allowed_machines:frozenset|None=None

class Executor:
    def __init__(self,policy=None,handlers=None,remote_spec=None):
        self.policy=policy or AccessPolicy()
        self.handlers=handlers or dict(HANDLERS)
        self.remote_spec=remote_spec
        self.events=[]
        self.invocations=0

    async def execute(self,name:str,raw_arguments:str)->dict:
        event={'tool':name,'raw_arguments':raw_arguments,'validation':'not_run',
               'permission':'not_run','invoked':False,
               'route':'mcp' if name=='get_machine_spec' and self.remote_spec else 'local'}
        started=time.perf_counter()
        stage='arguments'
        try:
            if name not in self.handlers or name not in ARG_TYPES:
                raise ToolFailure('UNKNOWN_TOOL','Tool is not registered. No code was executed.')
            if name not in self.policy.allowed_tools:
                raise ToolFailure('PERMISSION_DENIED','This application does not permit this tool.')
            if not isinstance(raw_arguments,str) or len(raw_arguments.encode('utf-8'))>32768:
                raise ToolFailure('INVALID_ARGUMENT','Arguments must be a bounded JSON string.')
            def no_constant(value): raise ValueError('Non-standard numeric constant')
            parsed=json.loads(raw_arguments,parse_constant=no_constant)
            if not isinstance(parsed,dict):raise ValueError('Arguments must be a JSON object')
            args=ARG_TYPES[name].model_validate(parsed)
            event['validation']='passed';event['validated_arguments']=args.model_dump()
            machine=getattr(args,'machine_id',None)
            if machine is not None and self.policy.allowed_machines is not None:
                if machine not in self.policy.allowed_machines:
                    raise ToolFailure('PERMISSION_DENIED','Access to this machine is denied.')
            event['permission']='passed'
            stage='execution';event['invoked']=True;self.invocations+=1
            if name=='get_machine_spec' and self.remote_spec:
                result=await self.remote_spec(args.machine_id)
            else:
                result=self.handlers[name](**args.model_dump())
                if inspect.isawaitable(result):result=await result
            stage='result'
            envelope=ToolResult.model_validate(result)
            if envelope.status=='ok':
                content=RESULT_TYPES[name].model_validate(envelope.data)
                # This checks input-output consistency, NOT the user's natural-language intent.
                if machine is not None and content.machine_id!=machine:
                    raise ToolFailure('INVALID_RESULT','Result machine ID differs from the requested argument.')
                envelope=envelope.model_copy(update={'data':content.model_dump()})
            result=envelope.model_dump()
        except ToolFailure as exc:
            result=fail(exc.code,exc.safe_message)
        except (ValidationError,ValueError,TypeError) as exc:
            if stage=='arguments':
                event['validation']='failed'
                result=fail('INVALID_ARGUMENT','Invalid type, range, time or JSON structure.')
            elif stage=='result':
                result=fail('INVALID_RESULT','Tool output violates the result contract.')
            else:
                result=fail('TOOL_EXCEPTION','Tool execution failed. No verified data was produced.')
            event['error_type']=type(exc).__name__
        except NotImplementedError:
            result=fail('NOT_IMPLEMENTED','The student TODO is not complete.')
        except Exception as exc:
            # Do not leak file paths, credentials or raw exception traces to the model.
            result=fail('TOOL_EXCEPTION','Tool raised an exception. No new data was confirmed.')
            event['error_type']=type(exc).__name__
        event.update(result=result,elapsed_seconds=time.perf_counter()-started)
        self.events.append(event)
        return result
