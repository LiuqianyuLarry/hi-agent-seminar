"""Short, answerable MCP checks inside the existing 28-minute teaching block."""
import copy


CHECKS = {
    't08.mcp_roles': {
        'id': 'mcp_roles_check',
        'type': 'mcq',
        'activity': 'Trace the next hand-off',
        'prompt': 'DeepSeek proposes get_machine_spec for CONV-3. On the MCP route, which sequence reaches the Python function?',
        'options': {
            'A': 'DeepSeek connects directly to the server through stdio.',
            'B': 'The host checks the request, then its MCP client calls the server tool.',
            'C': 'The parameter schema runs the function as soon as the model reads it.',
        },
        'correct': 'B',
        'explanation': 'The model proposes a request. The host checks it and owns the MCP client. The server receives the client request and runs its registered function.',
        'hint1': 'Separate the model-to-application connection from the application-to-tool connection.',
        'hint2': 'In app.py, the host opens MCPBackend. The model API does not open that local connection.',
        'estimated_seconds': 60,
        'required': True,
    },
    't08.mcp_discovery': {
        'id': 'mcp_discovery_check',
        'type': 'mcq',
        'activity': 'Predict the available information',
        'prompt': 'The client has completed only await client.list_tools(). It sees get_machine_spec and its machine_id input. What has it obtained so far?',
        'options': {
            'A': 'The tool interface; it still needs call_tool with CONV-3 to request the registered value.',
            'B': 'The CONV-3 registered value, because listing a tool also runs it.',
            'C': 'Every machine record, because discovery loads all tool data.',
        },
        'correct': 'A',
        'explanation': 'Discovery describes an available capability. It does not supply its result. A separate call_tool request carries the chosen tool name and machine_id.',
        'hint1': 'Think of a catalogue entry and an item you have actually requested.',
        'hint2': 'list_tools has no machine_id argument here. call_tool supplies {"machine_id": "CONV-3"}.',
        'estimated_seconds': 60,
        'required': True,
    },
    't08.mcp_results': {
        'id': 'mcp_result_check',
        'type': 'mcq',
        'activity': 'Inspect a failure response',
        'prompt': 'An MCP reply has is_error=True. Its text mentions "85 C", but no valid structured result was confirmed. What should our client do?',
        'options': {
            'A': 'Extract 85 and report a successful specification lookup.',
            'B': 'Ask the model to guess whether the number is probably correct.',
            'C': 'Keep the failure and report that no specification value was confirmed.',
        },
        'correct': 'C',
        'explanation': 'unpack_result checks is_error before using data. An error message containing a number is not evidence of a successful tool result. Preserve the failure for diagnosis.',
        'hint1': 'Which field tells the client whether the operation reported a failure?',
        'hint2': 'The first branch of unpack_result raises ToolFailure when is_error is true. It never reaches structured-content validation on that path.',
        'estimated_seconds': 60,
        'required': True,
    },
    't08.mcp_resource': {
        'id': 'mcp_context_check',
        'type': 'mcq',
        'activity': 'Find the missing connection',
        'prompt': 'The host reads the CONV-3 reference-note resource successfully, but sends DeepSeek only the original user question. Why can the model still lack the note?',
        'options': {
            'A': 'Reading any resource automatically updates the model weights.',
            'B': 'The host must select the relevant content and include it in a model request.',
            'C': 'The server must rename the resource as a tool before any model can use its text.',
        },
        'correct': 'B',
        'explanation': 'The resource response reaches the host. It is not automatically added to a model request. The host must decide what content belongs in that request; successful retrieval alone does not establish model context.',
        'hint1': 'Follow where the resource text is stored after read_resource returns.',
        'hint2': 'Compare what the host received with the messages it sent to DeepSeek. Content absent from those messages has not been supplied by this read.',
        'estimated_seconds': 60,
        'required': True,
    },
}


TIMING_BLOCKS = [
    {'id': 'purpose_and_roles', 'title': 'Why MCP and who connects to whom', 'minutes': 3,
     'kind': 'teaching', 'steps': ['t08.mcp_need', 't08.mcp_roles']},
    {'id': 'roles_check', 'title': 'Trace the next hand-off', 'minutes': 1,
     'kind': 'checkpoint', 'check_id': 'mcp_roles_check'},
    {'id': 'process_and_discovery', 'title': 'Local messages and tool discovery', 'minutes': 4,
     'kind': 'teaching', 'steps': ['t08.mcp_process', 't08.mcp_discovery']},
    {'id': 'discovery_check', 'title': 'Predict what discovery returns', 'minutes': 1,
     'kind': 'checkpoint', 'check_id': 'mcp_discovery_check'},
    {'id': 'wrapper_and_results', 'title': 'The server wrapper and result checks', 'minutes': 4,
     'kind': 'teaching', 'steps': ['t08.mcp_wrapper', 't08.mcp_results']},
    {'id': 'result_check', 'title': 'Inspect a failure response', 'minutes': 1,
     'kind': 'checkpoint', 'check_id': 'mcp_result_check'},
    {'id': 'adapter_and_context', 'title': 'Select interfaces and resource context', 'minutes': 3,
     'kind': 'teaching', 'steps': ['t08.mcp_bridge', 't08.mcp_resource']},
    {'id': 'context_check', 'title': 'Find the missing context connection', 'minutes': 1,
     'kind': 'checkpoint', 'check_id': 'mcp_context_check'},
    {'id': 'implementation', 'title': 'Complete the wrapper, run tests and read the output',
     'minutes': 7, 'kind': 'exercise'},
    {'id': 'transfer', 'title': 'Explain the full chain and check an unsupported conclusion',
     'minutes': 3, 'kind': 'final_checks'},
]


def apply_checkpoints(lesson):
    """Add four saved checks to both modes without adding time or completion weight."""
    task = next(item for item in lesson['tasks'] if item['id'] == 't08')
    for mode in ('review', 'practice'):
        steps = task['paths'][mode]
        by_id = {item['id']: item for item in steps}
        for step_id, check in CHECKS.items():
            if step_id not in by_id:
                raise ValueError('MCP checkpoint has no teaching step: ' + step_id)
            by_id[step_id]['check'] = copy.deepcopy(check)
        task.setdefault('path_timing', {})[mode] = copy.deepcopy(TIMING_BLOCKS)
    task['timing_blocks'] = copy.deepcopy(TIMING_BLOCKS)
    task['timing_summary'] = {
        'teaching_minutes': 14,
        'checkpoint_minutes': 4,
        'exercise_minutes': 7,
        'final_check_minutes': 3,
        'total_minutes': 28,
        'note': 'Planning targets for both routes. Checks replace uninterrupted lecture time; allow extra support when needed rather than skipping an unresolved check.',
    }
    task['checkpoint_policy'] = {
        'maximum_concepts_between_checks': 2,
        'count': 4,
        'required_before_exercise': True,
        'student_rule': 'Wait for an actual response and save it. An incorrect answer cannot pass a student checkpoint. Give two gradual hints, then offer more hints or an answer explanation. After an answer explanation, require the learner to explain the idea in their own words and verify it.',
        'progress_rule': 'These are checks within task t08. They do not add completion weight or change the core total.',
    }
    task['questions'][1] = {
        'id': 'q2', 'type': 'mcq',
        'prompt': 'The MCP test returns a valid CONV-3 reference of 85 C. The final assistant says, "CONV-3 is currently 85 C, so there is no fault." Which review is correct?',
        'options': {
            'A': 'The conclusion is proved because the MCP request succeeded.',
            'B': 'The returned reference proves the current temperature, but not the absence of a fault.',
            'C': 'The lookup succeeded, but the reference proves neither the current temperature nor the absence of a fault.',
        },
        'correct': 'C',
        'feedback': 'Check the meaning of the returned field as well as transport success. A registered reference is not a sensor measurement. A successful MCP exchange does not validate the model\'s engineering conclusion.',
    }
    task['code_walkthrough'][0] = (
        'Teach the eight MCP concepts in four pairs. After each pair, pause for its saved mini-check: '
        'roles, discovery, failure handling and model context. Resolve that check before the next pair. '
        'Then complete and test the wrapper; the final two questions connect the pieces.'
    )
    if sum(block['minutes'] for block in TIMING_BLOCKS) != task['minutes']:
        raise ValueError('MCP activities must fit the existing 28-minute task.')
    if task['practice_minutes'] != task['minutes']:
        raise ValueError('Both MCP routes must retain the same teaching time.')
