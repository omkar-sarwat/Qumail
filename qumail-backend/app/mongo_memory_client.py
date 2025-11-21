"""Embedded MongoDB-compatible client built on top of Mongita.

This provides a minimal subset of the AsyncIOMotorClient surface that the
backend relies on so the application can run in development environments where
MongoDB Atlas or a local mongod instance are not available.
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, Optional, Tuple

from mongita import MongitaClientMemory


async def _to_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


class AsyncMongitaCursor:
    """Async wrapper around a synchronous Mongita cursor."""

    def __init__(self, cursor):
        self._cursor = cursor

    def sort(self, key_or_list, direction=None):  # type: ignore[override]
        self._cursor = self._cursor.sort(key_or_list, direction)
        return self

    def skip(self, count: int):
        self._cursor = self._cursor.skip(count)
        return self

    def limit(self, count: int):
        self._cursor = self._cursor.limit(count)
        return self

    async def to_list(self, length: Optional[int] = None):
        def _collect() -> list[dict[str, Any]]:
            docs = []
            for idx, doc in enumerate(self._cursor):
                docs.append(doc)
                if length is not None and idx + 1 >= length:
                    break
            return docs

        return await asyncio.to_thread(_collect)


class AsyncMongitaCollection:
    """Async helper exposing the subset of collection APIs our repositories use."""

    def __init__(self, collection):
        self._collection = collection

    async def insert_one(self, document: dict[str, Any]):
        return await _to_thread(self._collection.insert_one, document)

    async def find_one(self, *args, **kwargs):
        return await _to_thread(self._collection.find_one, *args, **kwargs)

    def find(self, *args, **kwargs) -> AsyncMongitaCursor:
        return AsyncMongitaCursor(self._collection.find(*args, **kwargs))

    async def update_one(self, *args, **kwargs):
        return await _to_thread(self._collection.update_one, *args, **kwargs)

    async def delete_one(self, *args, **kwargs):
        return await _to_thread(self._collection.delete_one, *args, **kwargs)

    async def create_index(self, *args, **kwargs):
        return await _to_thread(self._collection.create_index, *args, **kwargs)


class AsyncMongitaDatabase:
    """Expose collections via attribute access similar to Motor databases."""

    def __init__(self, database):
        self._database = database
        self.name = database.name

    def __getattr__(self, item: str) -> AsyncMongitaCollection:
        return AsyncMongitaCollection(self._database[item])

    def __getitem__(self, item: str) -> AsyncMongitaCollection:
        return AsyncMongitaCollection(self._database[item])


class AsyncMongitaClient:
    """Tiny facade mimicking the Motor client surface we rely on."""

    def __init__(self):
        self._client = MongitaClientMemory()

    def __getitem__(self, name: str) -> AsyncMongitaDatabase:
        return AsyncMongitaDatabase(self._client[name])

    def close(self):
        close_fn = getattr(self._client, "close", None)
        if callable(close_fn):
            close_fn()


def create_async_memory_client(db_name: str) -> Tuple[AsyncMongitaClient, AsyncMongitaDatabase]:
    """Create an AsyncMongita client/database pair for embedded mode."""
    client = AsyncMongitaClient()
    database = client[db_name]
    return client, database
