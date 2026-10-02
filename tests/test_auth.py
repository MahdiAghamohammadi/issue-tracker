from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_register_login_and_get_current_user(client: AsyncClient) -> None:
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "USER@Example.com", "password": "strong-password"},
    )

    assert registration.status_code == 201
    assert registration.json()["email"] == "user@example.com"
    assert "password" not in registration.json()

    login = await client.post(
        "/api/v1/auth/token",
        data={"username": "USER@example.com", "password": "strong-password"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


async def test_duplicate_registration_returns_conflict(client: AsyncClient) -> None:
    payload = {"email": "duplicate@example.com", "password": "strong-password"}
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email is already registered"


async def test_registration_validates_email_and_password(client: AsyncClient) -> None:
    invalid_email = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "strong-password"},
    )
    short_password = await client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )

    assert invalid_email.status_code == 422
    assert short_password.status_code == 422


async def test_login_rejects_bad_credentials(client: AsyncClient) -> None:
    await register_and_login(client)

    wrong_password = await client.post(
        "/api/v1/auth/token",
        data={"username": "owner@example.com", "password": "wrong-password"},
    )
    missing_user = await client.post(
        "/api/v1/auth/token",
        data={"username": "missing@example.com", "password": "wrong-password"},
    )

    assert wrong_password.status_code == 401
    assert missing_user.status_code == 401
    assert wrong_password.headers["www-authenticate"] == "Bearer"


async def test_current_user_requires_valid_token(client: AsyncClient) -> None:
    missing = await client.get("/api/v1/auth/me")
    invalid = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
