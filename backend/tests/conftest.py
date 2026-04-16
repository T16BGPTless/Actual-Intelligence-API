"""Shared pytest fixtures and tiny chainable fakes."""

from types import SimpleNamespace

import pytest

from app.app import app


class QueryChain:
    """Minimal chainable object to fake Supabase request builders."""

    def __init__(self, data=None):
        self._data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def is_(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def update(self, *_args, **_kwargs):
        return self

    def insert(self, *_args, **_kwargs):
        return self

    def delete(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def maybe_single(self, *_args, **_kwargs):
        return self

    def single(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
