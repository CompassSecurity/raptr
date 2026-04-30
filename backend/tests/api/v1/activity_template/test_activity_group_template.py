from app.models.activity_group_template import ActivityGroupTemplate
from app.models.activity_template import ActivityTemplate


def test_get_activity_group_templates(
    client, session, test_admin_user, auth_headers_admin
):
    # 1. Create Data
    # Create Activity Templates
    a1 = ActivityTemplate(
        name="Activity 1",
        mitre_tactic="Tactic 1",
        mitre_technique="T1",
        provider="Test",
        created_by=test_admin_user.id,
    )
    a2 = ActivityTemplate(
        name="Activity 2",
        mitre_tactic="Tactic 1",
        mitre_technique="T1",
        provider="Test",
        created_by=test_admin_user.id,
    )
    session.add_all([a1, a2])
    session.flush()

    # Create Group
    g1 = ActivityGroupTemplate(name="Group 1")
    g1.activity_templates.append(a1)
    g1.activity_templates.append(a2)

    g2 = ActivityGroupTemplate(name="Group 2")
    g2.activity_templates.append(a2)

    session.add_all([g1, g2])
    session.commit()

    # 2. Call API
    response = client.get(
        "/api/v1/activity_group_template/", headers=auth_headers_admin
    )

    # 3. Verify
    # 3. Verify
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    items = data["items"]

    # Check Group 1 (Find in items)
    group1 = next((g for g in items if g["name"] == "Group 1"), None)
    assert group1 is not None

    # Assertions on Group 1
    assert str(g1.id) == group1["id"]
    assert len(group1["activity_template_ids"]) == 2
    # Convert list of UUIDs to strings for comparison
    activity_ids_1 = [str(aid) for aid in group1["activity_template_ids"]]
    assert str(a1.id) in activity_ids_1
    assert str(a2.id) in activity_ids_1

    # Check Group 2 (Find in items)
    group2 = next((g for g in items if g["name"] == "Group 2"), None)
    assert group2 is not None

    # Assertions on Group 2
    assert str(g2.id) == group2["id"]
    assert len(group2["activity_template_ids"]) == 1
    activity_ids_2 = [str(aid) for aid in group2["activity_template_ids"]]
    assert str(a2.id) in activity_ids_2
