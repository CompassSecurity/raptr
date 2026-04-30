from fastapi.testclient import TestClient

from app.models.user import User


def test_assessment_acl_lifecycle_flow(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    auth_headers_regular: dict[str, str],
    test_regular_user: User,
):
    """
    End-to-End flow:
    1. Admin creates Assessment.
    2. User checks -> sees nothing.
    3. Admin grants ACL.
    4. User checks -> sees assessment.
    5. Admin revokes ACL.
    6. User checks -> sees nothing.
    """

    # 1. Admin creates Assessment
    response = client.post(
        "/api/v1/assessment/",
        headers=auth_headers_admin,
        json={
            "name": "E2E Assessment",
            "description": "E2E Desc",
            "assessment_type": "PurpleTeam",
        },
    )
    assert response.status_code == 200
    assessment_id = response.json()["id"]

    # 2. User checks -> sees nothing
    response = client.get("/api/v1/assessment/", headers=auth_headers_regular)
    assert response.status_code == 200
    assessments = response.json()["items"]
    assert not any(a["id"] == assessment_id for a in assessments)

    # 3. Admin grants ACL
    response = client.post(
        "/api/v1/acl/",
        headers=auth_headers_admin,
        json={
            "user_id": str(test_regular_user.id),
            "assessment_id": assessment_id,
            "assessment_role": "spectator",
        },
    )
    assert response.status_code == 200
    acl_id = response.json()["id"]

    # 4. User checks -> sees assessment
    # List
    response = client.get("/api/v1/assessment/", headers=auth_headers_regular)
    assert response.status_code == 200
    assessments = response.json()["items"]
    assert any(a["id"] == assessment_id for a in assessments)

    # Get by ID
    response = client.get(
        f"/api/v1/assessment/{assessment_id}", headers=auth_headers_regular
    )
    assert response.status_code == 200
    assert response.json()["id"] == assessment_id

    # 5. Admin revokes ACL
    response = client.delete(f"/api/v1/acl/{acl_id}", headers=auth_headers_admin)
    assert response.status_code == 200

    # 6. User checks -> sees nothing
    # List
    response = client.get("/api/v1/assessment/", headers=auth_headers_regular)
    assert response.status_code == 200
    assessments = response.json()["items"]
    assert not any(a["id"] == assessment_id for a in assessments)

    # Get by ID
    response = client.get(
        f"/api/v1/assessment/{assessment_id}", headers=auth_headers_regular
    )
    # Depending on implementation, filtered list usually returns empty, get by ID might return 404 or None result
    # In our implementation: `assessment = session.execute(statement).scalar_one_or_none()`
    # If None, the API likely returns 404 or null.
    # We implemented 404 raise in service.
    assert response.status_code == 404
