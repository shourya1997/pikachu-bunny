from __future__ import annotations

import os
from typing import Any

import httpx

POCKETBASE_URL = os.environ.get("POCKETBASE_URL", "http://localhost:8090")
PB_ADMIN_EMAIL = os.environ["PB_ADMIN_EMAIL"]
PB_ADMIN_PASSWORD = os.environ["PB_ADMIN_PASSWORD"]


class PocketBaseClient:
    def __init__(self, base_url: str = POCKETBASE_URL):
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._admin_token: str | None = None

    async def __aenter__(self) -> "PocketBaseClient":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        await self._authenticate_admin()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _authenticate_admin(self) -> None:
        assert self._client
        r = await self._client.post(
            "/api/admins/auth-with-password",
            json={"identity": PB_ADMIN_EMAIL, "password": PB_ADMIN_PASSWORD},
        )
        r.raise_for_status()
        self._admin_token = r.json()["token"]
        self._client.headers["Authorization"] = f"Bearer {self._admin_token}"

    async def get(self, collection: str, record_id: str, user_id: str) -> dict | None:
        assert self._client
        r = await self._client.get(
            f"/api/collections/{collection}/records/{record_id}",
            params={"filter": f"(user_id='{user_id}')"},
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def list(self, collection: str, user_id: str, filter_extra: str = "") -> list[dict]:
        assert self._client
        filt = f"(user_id='{user_id}')"
        if filter_extra:
            filt = f"{filt} && {filter_extra}"
        r = await self._client.get(
            f"/api/collections/{collection}/records",
            params={"filter": filt, "sort": "-created"},
        )
        r.raise_for_status()
        return r.json().get("items", [])

    async def create(self, collection: str, data: dict, user_id: str) -> dict:
        assert self._client
        data["user_id"] = user_id
        r = await self._client.post(
            f"/api/collections/{collection}/records",
            json=data,
        )
        r.raise_for_status()
        return r.json()

    async def update(self, collection: str, record_id: str, data: dict, user_id: str) -> dict:
        assert self._client
        r = await self._client.patch(
            f"/api/collections/{collection}/records/{record_id}",
            json=data,
            params={"filter": f"(user_id='{user_id}')"},
        )
        r.raise_for_status()
        return r.json()

    async def delete(self, collection: str, record_id: str, user_id: str) -> None:
        assert self._client
        r = await self._client.delete(
            f"/api/collections/{collection}/records/{record_id}",
            params={"filter": f"(user_id='{user_id}')"},
        )
        r.raise_for_status()
