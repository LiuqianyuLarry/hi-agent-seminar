"""Current response instructions attached to CLI output, never to learner records."""
from pathlib import Path
import re


def saved_progress(value):
    """Use only status or catalogue progress, never experiment payload fields."""
    if not isinstance(value,dict):return None
    week=value.get('week');percent=value.get('core_percent')
    if (isinstance(week,str) and re.fullmatch(r'week\d{2}',week)
            and isinstance(percent,(int,float)) and not isinstance(percent,bool)
            and 0<=percent<=100):
        return {'week':week,'core_percent':percent}
    status=value.get('status')
    if isinstance(status,dict):
        result=saved_progress(status)
        if result is not None:return result
    active=value.get('active_week')
    if active:
        for course in value.get('courses',[]):
            if isinstance(course,dict) and course.get('id')==active and course.get('started'):
                return saved_progress({'week':active,'core_percent':course.get('core_percent')})
    return None


def response_output(result,root,status=None):
    """Wrap tool output without changing its nested values or saving any state."""
    if not isinstance(result,dict):return result
    progress=saved_progress(result)
    if progress is None and status is not None:progress=saved_progress(status)
    contract={
        'policy':str((Path(root)/'OUTPUT.md').resolve()),
        'final_reply_required':True,
        'required_content':['teaching','code_explanation','observed_results','saved_progress'],
        'when_applicable':True,
        'progress':progress,
        'tool_progress':'brief operational status only',
        'note':'Apply the current output policy even with an older lesson snapshot. '
               'Put all relevant teaching, code explanations, actual observations and the saved progress '
               'in the final student-visible reply. Tool logs or a saved acknowledgement are not that reply. '
               'Do not invent a code explanation or observed result when this action has none. '
               'Use the exact saved percentage; say progress unavailable if it cannot be read.',
    }
    return {**result,'response_contract':contract}
