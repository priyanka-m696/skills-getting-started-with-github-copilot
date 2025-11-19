import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src import app as application


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before each test."""
    # Make a deep copy of the original activities to restore later
    original = copy.deepcopy(application.activities)
    yield
    # Restore state
    application.activities.clear()
    application.activities.update(copy.deepcopy(original))


def test_get_activities():
    client = TestClient(application.app)
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect some known activity from the seed data
    assert "Soccer Team" in data
    assert "participants" in data["Soccer Team"]


def test_signup_and_unregister_flow():
    client = TestClient(application.app)

    activity = "Chess Club"
    email = "teststudent@mergington.edu"

    # Ensure starting state does not include our test email
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]

    # Sign up the student
    signup_url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(signup_url)
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify participant appears in activity
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email in resp.json()[activity]["participants"]

    # Duplicate signup should fail
    resp = client.post(signup_url)
    assert resp.status_code == 400

    # Unregister the student
    resp = client.delete(signup_url)
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify participant removed
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]


def test_signup_nonexistent_activity():
    client = TestClient(application.app)
    resp = client.post("/activities/ThisDoesNotExist/signup?email=a@b.com")
    assert resp.status_code == 404


def test_unregister_nonexistent_participant():
    client = TestClient(application.app)
    activity = "Debate Team"
    resp = client.delete(f"/activities/{urllib.parse.quote(activity)}/signup?email=nosuch@mergington.edu")
    assert resp.status_code == 404
