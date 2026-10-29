"""Pure adapter tests with constructed objects: NOT real MCP transport tests."""
from types import SimpleNamespace
import pytest
from mcp_backend import unpack_result,adapt_spec_tool
from schemas import ToolFailure

def test_mcp_error_not_treated_as_success():
    with pytest.raises(ToolFailure):unpack_result(SimpleNamespace(is_error=True,structured_content=None))

def test_mcp_requires_structured_result():
    with pytest.raises(ToolFailure):unpack_result(SimpleNamespace(is_error=False,structured_content=None))

def test_adapter_retains_constraints():
    tool=SimpleNamespace(name='get_machine_spec',description='Read spec',input_schema={
        'type':'object','properties':{'machine_id':{'type':'string','pattern':'^CONV-[0-9]{1,3}$'}},'required':['machine_id']})
    converted=adapt_spec_tool(tool)
    assert converted['function']['parameters']['properties']['machine_id']['pattern']=='^CONV-[0-9]{1,3}$'
    assert converted['function']['parameters']['additionalProperties'] is False

def test_unknown_schema_not_silently_rewritten():
    tool=SimpleNamespace(name='get_machine_spec',description='',input_schema={'type':'object','properties':{'x':{}}})
    with pytest.raises(ValueError):adapt_spec_tool(tool)
