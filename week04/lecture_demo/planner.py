"""Scripted planning is for runtime tests; only LivePlanner uses a model."""
import copy, json, os
from state import Decision
from verification import matching_sources, matching_stats
from prompts import RULES, tools_for_model


class ScriptedPlanner:
    mode='scripted'
    def __init__(self, scenario='normal'):
        self.scenario=scenario
        self.calls=0
        self.feedback=[]
    def observe(self,result):
        self.feedback.append(copy.deepcopy(result))
    def next(self,state,timeout):
        self.calls+=1
        t=state.task
        spec, query=matching_sources(state)
        if self.scenario=='early_finish':
            return Decision('finish',note='Injected fault: request finish before collecting enough evidence')
        if self.scenario=='invalid':
            return Decision('tool','get_machine_spec',{'machine_id':[t.machine_id]})
        if self.scenario=='wrong_object':
            return Decision('tool','get_machine_spec',{'machine_id':'CONV-7'})
        if self.scenario=='repeat':
            return Decision('tool','get_machine_spec',{'machine_id':t.machine_id},note='Injected fault: repeatedly request the same specification')
        if self.scenario=='human':
            return Decision('human',question='Please confirm the machine and time window covered by the data.')
        if t.goal in {'report','readings'} and not query:
            return Decision('tool','query_temperature',{'machine_id':t.machine_id,
                        'start':t.start,'end':t.end},note='Read temperatures in the confirmed window')
        if t.goal in {'report','spec'} and not spec:
            return Decision('tool','get_machine_spec',{'machine_id':t.machine_id},note='Read the reference limit for the same machine')
        if t.goal=='report' and not matching_stats(state,spec,query):
            values=[row.temperature_c for row in query[1].records]
            limit=spec[1].temperature_limit_c
            if self.scenario=='wrong_stats':
                values=[1.0,2.0]  # Fault injection, not observations.
            return Decision('tool','temperature_stats',{'values_c':values,'limit_c':limit},
                            note='Calculate using the values from the tool results')
        if self.scenario=='after_complete':
            return Decision('tool','get_machine_spec',{'machine_id':t.machine_id},note='This should not run: another request after the task is complete')
        return Decision('finish',note='Request completion')


def _get(obj,name,default=None):
    return obj.get(name,default) if isinstance(obj,dict) else getattr(obj,name,default)

def _dump(item):
    return item.model_dump(exclude_none=True) if hasattr(item,'model_dump') else copy.deepcopy(item)


from live_planner import LivePlanner, PlannerError
