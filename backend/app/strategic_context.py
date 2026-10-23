"""Transient projections of official data; never a second persistent database."""
from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta

FIELDS = {
    'tasks': ('id','title','status','priority','due_date','due_time','project_id','case_id','book_id','plan_id','strategy_id'),
    'events': ('id','title','status','event_date','start_time','end_time','location','event_type','project_id','case_id','book_id','plan_id','strategy_id'),
    # Audience and positioning must survive even when the user does not name the book:
    # they enable semantic connections from people/opportunities in unrelated domains.
    'books': ('id','code','title','status','author_profile_id','publication_date','planned_release_date','release_plan_note',
              'genre','themes','target_reader','positioning','differentiators','promotion_status'),
    'book_editions': ('id','book_id','format_code','list_price','is_active'),
    'balance_checks': ('id','account_id','balance_date','balance','notes'),
}

def recent_history(messages, character_budget=24000):
    # Service failures are not strategic assessments and must not contaminate later advice.
    messages = [m for m in messages if not (m['role'] == 'assistant' and
                ('Consulente non disponibile' in m['content'] or 'Assistente LLM non disponibile' in m['content']))]
    selected = []
    size = 0
    for message in reversed(messages[-30:]):
        length = len(message['content'])
        if size + length > character_budget:
            break
        selected.append(message)
        size += length
    return list(reversed(selected))

def compact_context(context, *, memory_check=False, relevant_text=''):
    result = deepcopy(context)
    sources = result['sources']
    needle = relevant_text.casefold()
    related_ids = set()
    for source in ('projects','cases','books'):
        for row in sources.get(source, []):
            terms = [str(row.get(key) or '').casefold() for key in ('code','title')]
            if any(len(term) >= 3 and term in needle for term in terms):
                related_ids.add(str(row.get('id')))
                if row.get('book_id'):
                    related_ids.add(str(row['book_id']))
    if not memory_check and context.get('date'):
        cutoff = (date.fromisoformat(str(context['date'])[:10]) - timedelta(days=30)).isoformat()
        omitted = {}
        def related(row):
            return any(str(row.get(key)) in related_ids for key in ('id','project_id','case_id','book_id'))
        for source in ('tasks', 'events'):
            original = sources.get(source, [])
            def keep(row):
                if related(row):return True
                when = str(row.get('completed_at') or row.get('due_date') or row.get('event_date') or '')[:10]
                if source == 'tasks':
                    if row.get('status') == 'cancelled':return False
                    return row.get('status') != 'completed' or not when or when >= cutoff
                return not when or when >= cutoff
            sources[source] = [row for row in original if keep(row)]
            omitted[source] = len(original) - len(sources[source])
        result['historical_context_scope'] = {
            'cutoff':cutoff,'omitted_counts':omitted,
            'note':'Attività aperte conservate anche se scadute; storico precedente a 30 giorni e attività annullate esclusi salvo collegamenti espliciti alla domanda. Le omissioni non significano assenza di attività o eventi. Correzioni e fonti personali conservate.'}
    for source, fields in FIELDS.items():
        if memory_check and source == 'books':
            # Memory deduplication needs the book descriptions, not only their catalog titles.
            continue
        def relevant(row):
            return any(str(row.get(key)) in related_ids for key in ('id','project_id','case_id','book_id'))
        sources[source] = [row if relevant(row) else {key: row[key] for key in fields if key in row}
                           for row in sources.get(source, [])]
    if not memory_check:
        # Plans carry the operative conditions in brief/draft. Historical source snapshots
        # and planning transcripts are redundant with the current official sources.
        sources['plans'] = [{key: value for key, value in row.items()
                             if key not in ('source_snapshot','dialogue','user_id','created_at','updated_at')}
                            for row in sources.get('plans', [])]
        sales = defaultdict(lambda: {'registered_records': 0, 'registered_copies': 0,
                                    'first_registered_sale': None, 'last_registered_sale': None})
        for row in sources.get('sales', []):
            group = sales[str(row.get('book_id'))]
            group['registered_records'] += 1
            group['registered_copies'] += row.get('quantity') or 0
            when = str(row['sale_date']) if row.get('sale_date') else None
            if when:
                group['first_registered_sale'] = min(group['first_registered_sale'] or when, when)
                group['last_registered_sale'] = max(group['last_registered_sale'] or when, when)
        sources['sales'] = [{'book_id': book, **summary} for book, summary in sales.items()]
        result['projection_note'] = ('Vendite aggregate dai registri ufficiali per libro; non è un dato di ricavo. '
            'Libri e calendario sono proiezioni dei campi principali. I piani conservano brief e draft '
            'con le condizioni; sono esclusi i dialoghi di pianificazione e le vecchie copie del contesto. '
            'Non dedurre dettagli assenti da queste proiezioni.')
    return result
