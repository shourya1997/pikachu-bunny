import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.pocketbase_client import PocketBaseClient


@pytest.mark.asyncio
async def test_pocketbase_client_authenticate():
    with patch("app.pocketbase_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.post.return_value.json.return_value = {"token": "admin-token-123"}

        client = PocketBaseClient(base_url="http://localhost:8090")
        async with client:
            assert client._admin_token == "admin-token-123"


@pytest.mark.asyncio
async def test_pocketbase_client_get_record():
    with patch("app.pocketbase_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.post.return_value.json.return_value = {"token": "admin-token"}
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = {"id": "abc123", "user_id": "user-1", "data": "test"}

        client = PocketBaseClient()
        async with client:
            record = await client.get("audits", "abc123", "user-1")

        assert record["id"] == "abc123"
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_pocketbase_client_get_record_not_found():
    with patch("app.pocketbase_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.post.return_value.json.return_value = {"token": "admin-token"}
        mock_client.get.return_value.status_code = 404

        client = PocketBaseClient()
        async with client:
            record = await client.get("audits", "notfound", "user-1")

        assert record is None


@pytest.mark.asyncio
async def test_pocketbase_client_list_records():
    with patch("app.pocketbase_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.post.return_value.json.return_value = {"token": "admin-token"}
        mock_client.get.return_value.json.return_value = {"items": [{"id": "1"}, {"id": "2"}]}

        client = PocketBaseClient()
        async with client:
            records = await client.list("audits", "user-1")

        assert len(records) == 2
        assert records[0]["id"] == "1"


@pytest.mark.asyncio
async def test_pocketbase_client_create_record():
    with patch("app.pocketbase_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.post.return_value.json.side_effect = [
            {"token": "admin-token"},
            {"id": "new-123", "user_id": "user-1", "data": "test"},
        ]

        client = PocketBaseClient()
        async with client:
            record = await client.create("audits", {"data": "test"}, "user-1")

        assert record["id"] == "new-123"
        assert record["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_pocketbase_client_delete_record():
    with patch("app.pocketbase_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.post.return_value.json.return_value = {"token": "admin-token"}
        mock_client.delete.return_value.status_code = 204

        client = PocketBaseClient()
        async with client:
            await client.delete("audits", "abc123", "user-1")

        mock_client.delete.assert_called_once()
