"""Pytest fixtures."""

import os

import pytest


@pytest.fixture
def client():
    os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")

    from app.app import app

    app.config.update(TESTING=True)
    return app.test_client()
