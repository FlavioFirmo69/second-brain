from uuid import uuid4

import pytest

from app.repository import Repository


class Result:
    def __init__(self, value):
        self.value = value

    def mappings(self):
        return self

    def one_or_none(self):
        return self.value

    def one(self):
        return self.value


class Session:
    def __init__(self, record):
        self.record = record
        self.statements = []
        self.committed = False

    def execute(self, statement, params):
        sql = str(statement)
        self.statements.append((sql, params))
        if 'RETURNING *' in sql:
            return Result({**self.record, 'status': 'confirmed', 'confirmed_at': 'now'})
        return Result(self.record)

    def commit(self):
        self.committed = True


def repository(monkeypatch, record):
    uid = uuid4()
    monkeypatch.setattr(Repository, 'user_id', lambda self: uid)
    monkeypatch.setattr(Repository, 'log', lambda *args: None)
    session = Session(record)
    return Repository(session), session, uid


@pytest.mark.parametrize('amount', [-50, 50])
def test_payment_and_income_confirmation(monkeypatch, amount):
    identity = uuid4()
    repo, session, uid = repository(monkeypatch, {'id': identity, 'status': 'planned', 'amount': amount})
    result = repo.confirm_transaction(identity)
    assert result['status'] == 'confirmed' and result['confirmed_at']
    assert result['amount'] == amount
    assert session.committed
    assert all(params['uid'] == uid for _, params in session.statements)
    assert not any('sb2_balance_checks' in sql for sql, _ in session.statements)


def test_repeated_confirmation_does_not_write_again(monkeypatch):
    identity = uuid4()
    repo, session, _ = repository(monkeypatch, {'id': identity, 'status': 'confirmed'})
    repo.confirm_transaction(identity)
    assert len(session.statements) == 1 and session.committed


@pytest.mark.parametrize('record,error', [(None, KeyError), ({'status': 'cancelled'}, ValueError)])
def test_unavailable_transaction_is_not_confirmed(monkeypatch, record, error):
    repo, session, _ = repository(monkeypatch, record)
    with pytest.raises(error):
        repo.confirm_transaction(uuid4())
    assert len(session.statements) == 1 and not session.committed


@pytest.mark.parametrize('linked', [False, True])
def test_completed_event_deleted_or_kept_in_context(monkeypatch, linked):
    identity = uuid4()
    repo, session, _ = repository(monkeypatch, {'id': identity, 'status': 'planned', 'case_id': uuid4() if linked else None})
    repo.complete_event(identity)
    sql = session.statements[-1][0]
    assert ('UPDATE sb2_events' if linked else 'DELETE FROM sb2_events') in sql
    assert session.committed
