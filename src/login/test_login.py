from httpx import AsyncClient

from src.users.models import User


async def test_login_success(async_client: AsyncClient, test_user: User):
    response = await async_client.post(
        "/login/",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"
    assert response.cookies.get("access_token") is not None


async def test_login_wrong_password(async_client: AsyncClient, test_user: User):
    response = await async_client.post(
        "/login/",
        data={"username": test_user.email, "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Неверный адрес электронной почты или пароль"
    )


async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post(
        "/login/",
        data={
            "username": "nonexistent@example.com",
            "password": "testpassword",
        },
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Неверный адрес электронной почты или пароль"
    )


async def test_logout_success(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/logout/")

    assert response.status_code == 200
    assert response.cookies.get("access_token") is None
