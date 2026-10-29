"""Typed contracts. Permissions are supplied by the application, never by model arguments."""
from datetime import datetime,timedelta,timezone
from typing import Annotated,Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator

TEACHING_TZ=timezone(timedelta(hours=8))
MachineID=Annotated[str,Field(pattern=r'^CONV-[0-9]{1,3}$')]
# Explicit classroom input limits; not manufacturer specifications.
Temperature=Annotated[float,Field(ge=-273.15,le=1000,allow_inf_nan=False)]

class StrictModel(BaseModel):
    model_config=ConfigDict(strict=True,extra='forbid',allow_inf_nan=False)

class SpecArgs(StrictModel):
    machine_id:MachineID

class StatsArgs(StrictModel):
    values_c:list[Temperature]=Field(min_length=1,max_length=1000)
    limit_c:Temperature

class QueryArgs(StrictModel):
    machine_id:MachineID
    start:str=Field(min_length=20,max_length=40)
    end:str=Field(min_length=20,max_length=40)

    @field_validator('start','end')
    @classmethod
    def normalize_time(cls,value):
        try: dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError as exc: raise ValueError('Use an ISO-8601 timestamp with timezone') from exc
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError('Timezone required; e.g. 2026-03-02T10:00:00+08:00')
        if dt.microsecond:
            raise ValueError('This dataset uses whole-second timestamps')
        return dt.astimezone(TEACHING_TZ).isoformat(timespec='seconds')

    @model_validator(mode='after')
    def check_window(self):
        start=datetime.fromisoformat(self.start);end=datetime.fromisoformat(self.end)
        if not start < end: raise ValueError('start must precede end')
        if end-start>timedelta(hours=24): raise ValueError('Classroom window limit is 24 hours')
        return self

class ErrorInfo(StrictModel):
    code:str
    message:str

class ToolResult(StrictModel):
    status:Literal['ok','error']
    data:dict|None=None
    source:str|None=None
    version:str|None=None
    error:ErrorInfo|None=None
    @model_validator(mode='after')
    def coherent_status(self):
        if self.status=='ok' and (self.data is None or self.error is not None):
            raise ValueError('Successful results require data and no error')
        if self.status=='error' and (self.data is not None or self.error is None):
            raise ValueError('Errors require error details and no data')
        return self

class StatsData(StrictModel):
    count:int=Field(ge=1,le=1000)
    mean_c:float
    max_c:float
    limit_c:float
    above_count:int=Field(ge=0,le=1000)
    above_fraction:float=Field(ge=0,le=1)
    comparison:Literal['strictly_greater_than']
    @model_validator(mode='after')
    def check_fraction(self):
        if self.above_count>self.count or abs(self.above_fraction-self.above_count/self.count)>1e-9:
            raise ValueError('Count and fraction disagree')
        return self

class SpecData(StrictModel):
    machine_id:MachineID
    temperature_limit_c:Temperature
    unit:Literal['C']

class TemperatureRow(StrictModel):
    ts:str
    temperature_c:Temperature

class QueryData(StrictModel):
    machine_id:MachineID
    start:str
    end:str
    interval:Literal['[start,end)']
    count:int=Field(ge=0,le=100)
    records:list[TemperatureRow]=Field(max_length=100)
    unit:Literal['C']
    @model_validator(mode='after')
    def check_count(self):
        if self.count!=len(self.records):raise ValueError('Count does not match records')
        return self

class ToolFailure(Exception):
    def __init__(self,code,message):
        super().__init__(message);self.code=code;self.safe_message=message

def success(data,source,version='classroom-v1'):
    return ToolResult(status='ok',data=data,source=source,version=version).model_dump()

def fail(code,message):
    return ToolResult(status='error',error=ErrorInfo(code=code,message=message)).model_dump()
