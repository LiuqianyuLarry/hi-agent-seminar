"""Small teaching nodes and source-grounded excerpts for student learning."""
import ast
from pathlib import Path


def public(value):
    """Remove answers from material shown before the learner chooses to see them."""
    if isinstance(value, dict):
        return {k:public(v) for k,v in value.items()
                if k not in {'correct','rubric','feedback','worked_answer','worked_example','solutions','answer_guidance','hint1','hint2'}}
    if isinstance(value, list):return [public(v) for v in value]
    return value


def steps_for(task, mode):
    return task.get('paths',{}).get(mode,[])


def excerpt(reference, packs, offset=0):
    from tutor import child, require, fingerprint
    require(reference['pack'] in packs,'Unknown source pack.')
    root=Path(packs[reference['pack']])
    path=child(root,reference['file'])
    require(path.suffix=='.py' and path.is_file(),'Teaching source is missing. Preserve the snapshot and recover it.')
    source=path.read_text(encoding='utf-8');lines=source.splitlines()
    start,end=1,len(lines)
    symbol=reference.get('symbol')
    if symbol:
        scope=ast.parse(source).body
        for part in symbol.split('.'):
            def named(node):
                if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):return node.name==part
                if isinstance(node,ast.Assign):return any(isinstance(t,ast.Name) and t.id==part for t in node.targets)
                return isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id==part
            found=next((n for n in scope if named(n)),None)
            require(found is not None,'Source symbol was not found: '+symbol)
            scope=getattr(found,'body',[])
        start=found.lineno;end=found.end_lineno
        if getattr(found,'decorator_list',[]):start=min(n.lineno for n in found.decorator_list)
    require(isinstance(offset,int) and offset>=0,'Code offset must be non-negative.')
    first=start+int(reference.get('slice_start',0))+offset
    require(start<=first<=end,'Requested code window is outside the source symbol.')
    last=min(end,first+min(12,max(1,int(reference.get('max_lines',12))))-1)
    return {'pack':reference['pack'],'file':reference['file'],'path':str(path),'symbol':symbol,
            'start_line':first,'end_line':last,'symbol_end_line':end,'sha256':fingerprint(path),
            'numbered_code':'\n'.join(f'{n}: {lines[n-1]}' for n in range(first,last+1)),
            'more_available':last<end,'next_code_offset':offset+last-first+1 if last<end else None}


def render_step(step,packs,offset=0,code_index=0):
    from tutor import require,child
    result=public(step)
    # The check explanation would reveal the answer even after stripping correct.
    if isinstance(result.get('check'),dict):result['check'].pop('explanation',None)
    refs=step.get('code_refs',[])
    require(isinstance(code_index,int) and 0<=code_index<max(1,len(refs)),'Choose a listed code source.')
    result['snippets']=[excerpt(refs[code_index],packs,offset)] if refs else []
    result['code_sources']=[{'index':i,'pack':ref['pack'],'file':ref['file'],'symbol':ref.get('symbol')} for i,ref in enumerate(refs)]
    result['code_index']=code_index
    if step.get('slide_review',{}).get('image'):
        relative=Path(step['slide_review']['image'])
        require(relative.parts[0]=='slides','Unexpected slide image path.')
        path=child(Path(packs['slides']),*relative.parts[1:])
        require(path.is_file(),'The saved slide image is missing; recover the snapshot before continuing.')
        result['slide_image']=str(path)
        result['presentation']='In the final student-visible reply, show or link the actual slide, explain its figure and concept, then the code bridge. Do not leave teaching only in tool progress or dump this helper JSON.'
        return result
    result['presentation']='In the final student-visible reply, teach one idea, show one short code window, explain its inputs and result, and give one next action. Do not leave teaching only in tool progress or dump this helper JSON.'
    return result
