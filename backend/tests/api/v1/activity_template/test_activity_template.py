from app.models.activity_template import ActivityTemplate


def create_activity_template(session, name="Test Template"):
    template = ActivityTemplate(
        name=name,
        mitre_tactic="Execution",
        mitre_technique="T1234",
        activity_rationale="Rationale",
        activity_actions="Actions",
        activity_requirements="Requirements",
        activity_notes="Notes",
        provider="Provider",
        expected_prevention=True,
        expected_alert_creation=True,
        expected_severity="High",
        priority="High",
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def test_get_activity_templates(client, session, auth_headers_regular):
    # Create templates
    t1 = create_activity_template(session, name="Template 1")
    t2 = create_activity_template(session, name="Template 2")

    response = client.get("/api/v1/activity_template/", headers=auth_headers_regular)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2

    ids = [item["id"] for item in data["items"]]
    assert str(t1.id) in ids
    assert str(t2.id) in ids


def test_get_activity_template_by_id(client, session, auth_headers_regular):
    t1 = create_activity_template(session, name="Template 1")

    response = client.get(
        f"/api/v1/activity_template/{t1.id}", headers=auth_headers_regular
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(t1.id)
    assert data["name"] == "Template 1"


def test_get_activity_template_not_found(client, session, auth_headers_regular):
    import uuid

    random_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/activity_template/{random_id}", headers=auth_headers_regular
    )
    assert response.status_code == 404
