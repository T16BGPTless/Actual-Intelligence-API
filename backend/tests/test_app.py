"""Smoke tests for the Flask app."""


def test_home_redirects(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
