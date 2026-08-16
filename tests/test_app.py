from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    """Create a TestClient while resetting the in-memory activity state."""
    original_activities = deepcopy(activities)

    with TestClient(app) as test_client:
        yield test_client

    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    """Arrange-Act-Assert: root endpoint should redirect to the static page."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seed_data(client):
    """Arrange-Act-Assert: activity listing should expose the seeded data."""
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_success(client):
    """Arrange-Act-Assert: a valid signup adds the student to the activity."""
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(f"/activities/{quote(activity_name)}/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_rejects_duplicate_participant(client):
    """Arrange-Act-Assert: duplicate signup should return a 400 error."""
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(f"/activities/{quote(activity_name)}/signup?email={email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_activity_rejects_missing_activity(client):
    """Arrange-Act-Assert: unknown activity names should return a 404 error."""
    response = client.post("/activities/Unknown%20Club/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success(client):
    """Arrange-Act-Assert: removing a signed-up participant updates the list."""
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    response = client.delete(f"/activities/{quote(activity_name)}/remove?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_missing_signup(client):
    """Arrange-Act-Assert: removing a participant who is not signed up returns a 400 error."""
    email = "notregistered@mergington.edu"
    activity_name = "Chess Club"

    response = client.delete(f"/activities/{quote(activity_name)}/remove?email={email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
