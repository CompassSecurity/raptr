import uuid

import pytest
from fastapi import HTTPException

from app.models.activity_template import ActivityTemplate
from app.schemas.activity_template import ActivityTemplateFilter
from app.services.activity_template.activity_template import (
    get_activity_template_by_id_service,
    get_all_activity_templates_service,
)


@pytest.fixture
def test_activity_templates(session, test_admin_user):
    t1 = ActivityTemplate(
        name="Phishing Attack",
        mitre_tactic="Initial Access",
        mitre_technique="T1566",
        provider="Custom",
        created_by=test_admin_user.id,
    )
    t2 = ActivityTemplate(
        name="Credential Dumping",
        mitre_tactic="Credential Access",
        mitre_technique="T1003",
        provider="Atomic Red Team",
        created_by=test_admin_user.id,
    )
    session.add_all([t1, t2])
    session.commit()
    return [t1, t2]


def test_get_all_activity_templates(session, test_admin_user, test_activity_templates):
    result = get_all_activity_templates_service(
        test_admin_user, session, ActivityTemplateFilter()
    )
    assert result.total >= 2


def test_get_all_activity_templates_with_filter(
    session, test_admin_user, test_activity_templates
):
    result = get_all_activity_templates_service(
        test_admin_user, session, ActivityTemplateFilter(name="Phishing")
    )
    assert result.total == 1
    assert result.items[0].name == "Phishing Attack"


def test_get_activity_template_by_id(session, test_admin_user, test_activity_templates):
    template = test_activity_templates[0]

    fetched = get_activity_template_by_id_service(template.id, test_admin_user, session)

    assert fetched.id == template.id
    assert fetched.name == "Phishing Attack"


def test_get_activity_template_by_id_not_found(session, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        get_activity_template_by_id_service(uuid.uuid4(), test_admin_user, session)
    assert exc.value.status_code == 404
