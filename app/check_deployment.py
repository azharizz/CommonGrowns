"""Live deployment check using only fictional fixtures and disposable databases."""
import json
import logging
import tempfile
from pathlib import Path

from commongrown.ai import AgentModel
from commongrown.config import ROOT, read_json
from commongrown.exchange import Exchange
from commongrown.models import Opportunity
from commongrown.state import State
from commongrown.worker import Worker


def main():
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='commongrown-check-') as directory:
        root = Path(directory)
        state = State(root / 'accounts.db')
        state.seed_accounts()
        exchange = Exchange.open(root / 'chroma')
        for data in read_json(ROOT / 'seeds' / 'opportunities.json'):
            opp = Opportunity.from_dict(data)
            exchange.upsert(opp, state.account(opp.company)['verified_level'])
            state.register_opportunity(opp)
        assert exchange.collection.count() == 12
        candidates = exchange.candidates(exchange.get('A1'))
        assert any(row['opportunity']['opp_id'] == 'B1' for row in candidates)
        print('PASS: persistent Chroma seed, embeddings, forward/reverse retrieval', flush=True)
        config = {'users': {'rina': 'NusaConf', 'budi': 'CloudKita'}, 'rooms': {
            'private-a': {'kind': 'private', 'company': 'NusaConf'},
            'private-b': {'kind': 'private', 'company': 'CloudKita'},
            'exchange': {'kind': 'exchange'},
            'deal': {'kind': 'deal', 'opportunities': ['A1', 'B1']}}}
        worker = Worker(state, exchange, AgentModel(), config, root)
        counter = 0

        def send(body, sender='rina', room='private-a'):
            nonlocal counter
            counter += 1
            return worker.handle({'room_id': room, 'payload': {'sender': sender,
                'addressed': True, 'message_id': f'check-{counter}', 'body': body}})

        try:
            send('/balance', sender='budi')
            raise AssertionError('Cross-company access was accepted')
        except ValueError:
            pass
        draft = send('/draft ' + json.dumps(exchange.get('A1').to_dict()))
        send('/approve ' + draft['approval'])
        print('PASS: company authorization and exact-draft approval/publication', flush=True)
        result = send('/brief B1 A1 full', sender='budi', room='private-b')
        assert result['locked']
        result = send('/brief A1 B1 full')
        assert result['company'] == 'CloudKita' and set(result['fits']) == {'business','commercial','capability','strategic'}
        assert state.account('NusaConf')['credits'] == 9
        assert worker.llm.last_run['accepted']
        print('PASS: deployed SDK tools, real match brief and zero-credit gate', flush=True)
        assert not send('/interest A1 B1')['mutual']
        assert send('/interest A1 B1', sender='budi', room='private-b')['mutual']
        state.bind_room('A1', 'B1', 'deal')
        for sender, room, position in [('rina','private-a','Discuss sponsorship deliverables at the published range.'),
                                        ('budi','private-b','Discuss brand exposure and attendee seniority.')]:
            shared = send('/share A1 B1 ' + json.dumps({'position':position, 'questions':['What deliverables are included?']}), sender, room)
            send('/approve-share A1 B1 ' + shared['approval'], sender, room)
            send('/range-consent A1 B1', sender, room)
        send('/private ' + json.dumps({'notes':'Fictional test only','ranges':{'A1':{'min':40000,'max':100000}}}))
        send('/private ' + json.dumps({'notes':'Fictional test only','ranges':{'B1':{'min':60000,'max':90000}}}), 'budi','private-b')
        overlap = send('/brief A1 B1 range')
        assert overlap == {'compatible':True, 'overlap':'broad'}
        prepared = send('/prepare A1 B1', room='deal')
        assert prepared['status'] == 'draft_for_human_review' and prepared['agenda']
        assert state.account('NusaConf')['credits'] == 7
        print('PASS: mutual consent, private range and live meeting preparation', flush=True)
        send('/withdraw A1 B1')
        try:
            send('/prepare A1 B1', room='deal')
            raise AssertionError('Withdrawn access was accepted')
        except ValueError:
            pass
        print('PASS: withdrawal blocks further deal access; disposable test data removed on exit', flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('FAIL:', type(exc).__name__, '(details suppressed to protect configuration)', flush=True)
        raise SystemExit(1)
