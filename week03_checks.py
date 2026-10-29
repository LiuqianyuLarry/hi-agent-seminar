"""Saved formative checks between MCP explanations in the student course."""


def current_check(course, state, name):
    from tutor import require
    task=course.current(state);mode=state.get('study_mode')
    require(task and mode in {'review','practice'},'Choose a current task and study mode.')
    record=state['tasks'][task['id']]
    pending=course.pending_steps(task,record,mode)
    require(pending and pending[0]['id']==name,'Respond to the current teaching checkpoint.')
    check=pending[0].get('check')
    require(check and check.get('type','mcq')=='mcq','This step has no multiple-choice checkpoint.')
    saved=record.setdefault('path_checks',{}).setdefault(mode,{}).setdefault(name,
        {'attempts':[],'hints':[],'own_words':[],'passed':False})
    return check,saved


def checkpoint_action(course,action,name,text,verdict=None):
    from tutor import require,clean_text,now
    text=clean_text(text)
    require(text.strip().upper()!='SHOWCASE','Unsupported answer shortcut. Make a learning attempt or request a hint.')
    with course.lock():
        state=course.load();check,saved=current_check(course,state,name)
        if action=='answer':
            if saved.get('answer_explained'):
                require(text.strip().upper() not in check['options'],'Explain the idea in your own words, not an option letter.')
                require(len(text.split())>=4,'Use a short sentence in your own words.')
                saved['own_words'].append({'at':now(),'text':text})
                saved['passed']=False;saved.pop('assessment',None)
                result={'passed':False,'needs_assessment':True,'next':'Check this learner explanation before moving on.'}
            else:
                choice=text.strip().upper()
                require(choice in check['options'],'Choose a displayed option, or ask for a hint.')
                passed=choice==check['correct']
                saved['attempts'].append({'at':now(),'choice':choice,'passed':passed})
                saved['passed']=passed
                result={'passed':passed,'feedback':check['explanation'] if passed else
                    'Not yet. Revisit the last idea and try again, or ask for a hint.'}
        elif action=='hint':
            require(not saved['passed'],'This check is already understood; continue or ask an ordinary clarification question.')
            count=len(saved['hints'])
            hint=check.get('hint'+str(count+1)) if count<2 else None
            if hint is None:
                hint='Trace one CONV-3 request and say which program holds the information at this point. Then return to the question.'
            saved['hints'].append({'at':now(),'request':text,'text':hint})
            result={'hint_number':count+1,'hint':hint,'passed':False,
                    'next':'Wait for another attempt. After two hints, offer more hints or an answer explanation.'}
            if count>=1:result['support_choices']=['More hints','Explain the answer']
        elif action=='solution':
            require(len(saved['hints'])>=2,'Give two gradual hints with learner responses before offering the answer.')
            saved['answer_explained']={'at':now(),'learner_request':text}
            saved['passed']=False;saved['own_words']=[];saved.pop('assessment',None)
            result={'passed':False,'correct':check['correct'],'explanation':check['explanation'],
                    'next':'Explain this answer, then ask the learner to explain it in their own words. Do not advance yet.'}
        elif action=='assess':
            require(verdict in {'pass','retry'},'Provide pass or retry.')
            require(saved.get('answer_explained') and saved['own_words'],'Assess only an actual own-words response after explaining the answer.')
            require(saved.get('assessment',{}).get('response_index')!=len(saved['own_words'])-1,
                    'This response was already assessed. Save a new learner explanation before reassessing.')
            saved['assessment']={'at':now(),'verdict':verdict,'feedback':text,'response_index':len(saved['own_words'])-1}
            saved['passed']=verdict=='pass'
            result={'passed':saved['passed'],'feedback':text}
        else:raise ValueError('Unknown checkpoint action.')
        course.save(state)
    return {**result,'step_id':name,'progress_unchanged':True,'status':course.status()}
