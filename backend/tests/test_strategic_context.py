from app.strategic_context import compact_context,recent_history

def test_projection_preserves_authoritative_goals_conditions_and_selected_episode():
    context={'sources':{
        'personal_profiles':[{'content_markdown':'Proteggere il tempo per la scrittura'}],
        'plans':[{'id':'plan','brief':'Switch solo dopo test positivo','draft':{'condition':'Importatore validato'},
                  'source_snapshot':{'obsolete':'old'},'dialogue':['old transcript']}],
        'sales':[{'book_id':'book','sale_date':'2026-10-12','quantity':2},{'book_id':'book','sale_date':'2026-10-13','quantity':3}],
        'books':[{'id':'book','title':'Romanzo','synopsis':'Testo completo'}]},
        'diary_episode_requested':{'content_markdown':'L’importatore non è ancora validato'},'unavailable':['inbox']}
    result=compact_context(context)
    assert result['sources']['personal_profiles']==context['sources']['personal_profiles']
    assert result['sources']['plans'][0]['draft']==context['sources']['plans'][0]['draft']
    assert 'source_snapshot' not in result['sources']['plans'][0]
    assert result['diary_episode_requested']==context['diary_episode_requested']
    assert result['unavailable']==['inbox']
    assert result['sources']['sales'][0]['registered_copies']==5
    assert result['sources']['sales'][0]['registered_records']==2
    assert 'source_snapshot' in context['sources']['plans'][0] # Input is never mutated.

def test_explicitly_relevant_project_actions_keep_their_full_details():
    context={'sources':{'projects':[{'id':'fruit','code':'FRUIT','title':'Caso Fruit'}],
        'tasks':[{'id':'task','case_id':'fruit','title':'Modifica importatore','description':'Ripetere il test prima dello switch'}]}}
    result=compact_context(context,relevant_text='Mi serve consiglio su Fruit')
    assert result['sources']['tasks'][0]['description']=='Ripetere il test prima dello switch'

def test_history_budget_preserves_whole_recent_messages_without_cutting_text():
    messages=[{'role':'user','content':'a'*20},{'role':'assistant','content':'b'*20},
              {'role':'user','content':'c'*20}]
    assert recent_history(messages,40)==messages[-2:]
    assert messages[0]['content']=='a'*20
