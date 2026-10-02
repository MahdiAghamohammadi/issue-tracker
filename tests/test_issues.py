from httpx import AsyncClient

from tests.conftest import register_and_login


async def create_issue(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    title: str = "Broken login",
    description: str = "Users cannot sign in",
    priority: str = "medium",
):
    return await client.post(
        "/api/v1/issues/",
        headers=headers,
        json={
            "title": title,
            "description": description,
            "priority": priority,
        },
    )


async def test_issue_crud_flow(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await create_issue(client, auth_headers, priority="high")
    assert created.status_code == 201
    issue = created.json()
    assert issue["status"] == "open"
    assert issue["priority"] == "high"
    assert issue["owner_id"]
    assert issue["created_at"] == issue["updated_at"]

    fetched = await client.get(f"/api/v1/issues/{issue['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == issue["id"]

    updated = await client.patch(
        f"/api/v1/issues/{issue['id']}",
        headers=auth_headers,
        json={"title": "Login fixed", "status": "closed"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Login fixed"
    assert updated.json()["status"] == "closed"
    assert updated.json()["created_at"] == issue["created_at"]
    assert updated.json()["updated_at"] >= issue["updated_at"]

    deleted = await client.delete(f"/api/v1/issues/{issue['id']}", headers=auth_headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"/api/v1/issues/{issue['id']}", headers=auth_headers)
    ).status_code == 404


async def test_issue_endpoints_require_authentication(client: AsyncClient) -> None:
    responses = [
        await client.get("/api/v1/issues/"),
        await client.post(
            "/api/v1/issues/",
            json={"title": "An issue", "description": "Valid description"},
        ),
        await client.get("/api/v1/issues/not-an-id"),
        await client.patch("/api/v1/issues/not-an-id", json={"status": "closed"}),
        await client.delete("/api/v1/issues/not-an-id"),
    ]

    assert all(response.status_code == 401 for response in responses)


async def test_issue_validation(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    invalid_create = await client.post(
        "/api/v1/issues/",
        headers=auth_headers,
        json={"title": "x", "description": "bad", "priority": "urgent"},
    )
    created = await create_issue(client, auth_headers)
    invalid_update = await client.patch(
        f"/api/v1/issues/{created.json()['id']}",
        headers=auth_headers,
        json={"title": "x"},
    )

    assert invalid_create.status_code == 422
    assert invalid_update.status_code == 422


async def test_users_cannot_access_each_others_issues(client: AsyncClient) -> None:
    owner_headers = await register_and_login(client, "owner@example.com")
    other_headers = await register_and_login(client, "other@example.com")
    issue = (await create_issue(client, owner_headers)).json()

    other_list = await client.get("/api/v1/issues/", headers=other_headers)
    other_get = await client.get(f"/api/v1/issues/{issue['id']}", headers=other_headers)
    other_update = await client.patch(
        f"/api/v1/issues/{issue['id']}",
        headers=other_headers,
        json={"status": "closed"},
    )
    other_delete = await client.delete(
        f"/api/v1/issues/{issue['id']}", headers=other_headers
    )

    assert other_list.json()["total"] == 0
    assert other_get.status_code == 404
    assert other_update.status_code == 404
    assert other_delete.status_code == 404
    assert (
        await client.get(f"/api/v1/issues/{issue['id']}", headers=owner_headers)
    ).status_code == 200


async def test_filter_search_sort_and_pagination(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    first = await create_issue(
        client,
        auth_headers,
        title="Login failure",
        description="OAuth login is broken",
        priority="high",
    )
    second = await create_issue(
        client,
        auth_headers,
        title="Dark mode",
        description="Add a dark theme",
        priority="low",
    )
    third = await create_issue(
        client,
        auth_headers,
        title="Login audit",
        description="Record successful sessions",
        priority="medium",
    )
    assert all(response.status_code == 201 for response in (first, second, third))
    await client.patch(
        f"/api/v1/issues/{second.json()['id']}",
        headers=auth_headers,
        json={"status": "closed"},
    )

    filtered = await client.get(
        "/api/v1/issues/",
        headers=auth_headers,
        params={
            "status": "open",
            "search": "LOGIN",
            "sort_by": "priority",
            "sort_direction": "desc",
            "limit": 1,
            "offset": 0,
        },
    )
    second_page = await client.get(
        "/api/v1/issues/",
        headers=auth_headers,
        params={"sort_by": "title", "sort_direction": "asc", "limit": 1, "offset": 1},
    )

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 2
    assert filtered.json()["items"][0]["title"] == "Login failure"
    assert filtered.json()["limit"] == 1
    assert filtered.json()["offset"] == 0
    assert second_page.json()["total"] == 3
    assert second_page.json()["items"][0]["title"] == "Login audit"


async def test_list_query_validation(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    assert (
        await client.get("/api/v1/issues/?limit=0", headers=auth_headers)
    ).status_code == 422
    assert (
        await client.get("/api/v1/issues/?offset=-1", headers=auth_headers)
    ).status_code == 422
    assert (
        await client.get("/api/v1/issues/?sort_by=unknown", headers=auth_headers)
    ).status_code == 422


async def test_malformed_and_missing_issue_ids_return_not_found(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    missing_id = "00000000-0000-0000-0000-000000000099"

    for issue_id in ("not-a-uuid", missing_id):
        assert (
            await client.get(f"/api/v1/issues/{issue_id}", headers=auth_headers)
        ).status_code == 404
