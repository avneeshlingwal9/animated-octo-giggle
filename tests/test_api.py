import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    # snapshot + restore to keep tests isolated
    original = copy.deepcopy(activities_store)
    yield
    activities_store.clear()
    activities_store.update(original)


def test_get_activities_contains_expected_structure():
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant_and_reflects_in_get():
    activity = "Chess Club"
    email = "tester@mergington.edu"

    # sign up
    r = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert r.status_code == 200
    assert "Signed up" in r.json()["message"]

    # verify participant present
    r2 = client.get("/activities")
    assert email in r2.json()[activity]["participants"]


def test_signup_duplicate_returns_400():
    activity = "Chess Club"
    existing = activities_store[activity]["participants"][0]

    r = client.post(f"/activities/{activity}/signup", params={"email": existing})
    assert r.status_code == 400


def test_delete_participant_removes_and_reflects_in_get():
    activity = "Chess Club"
    email = "to_remove@mergington.edu"

    # add then remove
    client.post(f"/activities/{activity}/signup", params={"email": email})
    r = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert r.status_code == 200
    assert "Removed" in r.json()["message"]

    # verify removed
    r2 = client.get("/activities")
    assert email not in r2.json()[activity]["participants"]


def test_delete_nonexistent_participant_returns_400():
    activity = "Chess Club"
    r = client.delete(f"/activities/{activity}/participants", params={"email": "noone@x.com"})
    assert r.status_code == 400


def test_delete_nonexistent_activity_returns_404():
    r = client.delete("/activities/NoSuchActivity/participants", params={"email": "a@b.c"})
    assert r.status_code == 404
