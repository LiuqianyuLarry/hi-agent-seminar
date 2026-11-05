import pytest,json
from pathlib import Path
from state import Task,State
from controls import Config
from gateway import ToolRunner
from state import Decision

@pytest.fixture
def task():
    return Task.model_validate_json(Path('tasks/normal.json').read_text(encoding='utf-8'))

@pytest.fixture
def config():
    return Config(total_seconds=40,tool_timeout=5)

@pytest.fixture
def source_state(task,config):
    s=State(task,'scripted');runner=ToolRunner()
    runner.execute(s,Decision('tool','query_temperature',{
        'machine_id':task.machine_id,'start':task.start,'end':task.end}),config)
    runner.execute(s,Decision('tool','get_machine_spec',{'machine_id':task.machine_id}),config)
    return s
