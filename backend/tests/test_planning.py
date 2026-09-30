from datetime import date
import pytest
from pydantic import ValidationError
from app.planning_models import Draft, PlanInput
from app.planning import calculate_monitor


def make_draft(**changes):
    data = dict(title='Lancio', explanation='Piano motivato', assumptions=[],
        actions=[dict(kind='task', title='Newsletter', reason='Raggiungere lettori', date='2026-11-01')],
        start_date='2026-11-01', end_date='2026-12-31', target_copies=100,
        threshold_percent=30, threshold_reason='Soglia concordata', minimum_expected=20,
        milestones=[dict(date='2026-11-08', cumulative_copies=40),dict(date='2026-12-31', cumulative_copies=100)])
    data.update(changes)
    return Draft.model_validate(data)


def test_context_is_exclusive():
    with pytest.raises(ValidationError):
        PlanInput(brief='test')


def test_target_requires_final_checkpoint():
    with pytest.raises(ValidationError):
        make_draft(target_copies=200)


def test_expectations_cannot_decrease():
    with pytest.raises(ValidationError):
        make_draft(milestones=[dict(date='2026-11-08', cumulative_copies=110),dict(date='2026-12-31', cumulative_copies=100)])


def test_dependency_cannot_reference_itself():
    with pytest.raises(ValidationError):
        make_draft(actions=[dict(title='A', reason='R', depends_on=[0])])


def test_event_requires_date():
    with pytest.raises(ValidationError):
        make_draft(actions=[dict(kind='event', title='A', reason='R')])


def test_monitor_boundary_and_small_numbers():
    draft=make_draft()
    assert calculate_monitor(draft,date(2026,11,8),28)['status']=='below_threshold'
    assert calculate_monitor(draft,date(2026,11,8),29)['status']=='in_line'
    assert calculate_monitor(draft,date(2026,11,7),0)['status']=='insufficient_history'


def test_actions_outside_period_rejected():
    with pytest.raises(ValidationError):
        make_draft(actions=[dict(title='A',reason='R',date='2027-01-01')])
