"""The three tools have separate jobs. Their descriptions explain the boundaries."""
from schemas import StatsArgs, QueryArgs, SpecArgs
ARG_TYPES = {'temperature_stats': StatsArgs, 'query_temperature': QueryArgs, 'get_machine_spec': SpecArgs}
DESCRIPTIONS = {
    'temperature_stats': 'Calculate the mean, maximum and share strictly above a given limit. Use actual observed Celsius readings and their registered limit. Does not read files or calculate duration.',
    'query_temperature': 'Read temperature measurements for a confirmed machine and timezone-aware time window [start,end). At most 24 hours and 100 rows. Does not return a reference limit.',
    'get_machine_spec': 'Read the reference temperature limit, source and version for a confirmed machine. This is a specification file, not a live measurement or maintenance log.'
}
def model_tools():
    tools = []
    for name, cls in ARG_TYPES.items():
        schema = cls.model_json_schema()
        schema['additionalProperties'] = False
        tools.append({'type': 'function', 'function': {'name': name,
                     'description': DESCRIPTIONS[name], 'parameters': schema}})
    return tools
