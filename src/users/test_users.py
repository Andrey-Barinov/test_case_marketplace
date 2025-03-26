from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User


async def test_register_user_success(
    mocker, async_client: AsyncClient, test_session: AsyncSession
):
    # Мокаем функцию send_email_after_successful_registration.delay
    mock_send_email = mocker.patch(
        "src.users.router.send_email_after_successful_registration.delay"
    )

    # Данные для регистрации пользователя
    new_user_data = {
        "email": "test@example.com",
        "phone_number": "+79994567890",
        "name": "Test_User",
        "password": "Password123!",
        "password_confirm": "Password123!",
    }

    response = await async_client.post(
        "users/registration/", json=new_user_data
    )

    assert response.status_code == 200

    query = select(User).where(User.email == "test@example.com")
    result = await test_session.execute(query)
    db_new_user = result.scalar_one_or_none()

    assert db_new_user.name == "Test_User"
    assert db_new_user.phone_number == "+79994567890"

    mock_send_email.assert_called_once_with("test@example.com")


async def test_register_user_protect_from_email_duplication(
    mocker, async_client: AsyncClient, test_session: AsyncSession
):
    # Мокаем функцию send_email_after_successful_registration.delay
    mock_send_email = mocker.patch(
        "src.users.router.send_email_after_successful_registration.delay"
    )

    # Данные для регистрации пользователя c уже существующим email
    new_user_data_with_existing_email = {
        "email": "test@example.com",
        "phone_number": "+79994567890",
        "name": "Test_User",
        "password": "Password123!",
        "password_confirm": "Password123!",
    }

    response = await async_client.post(
        "users/registration/", json=new_user_data_with_existing_email
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Такой email уже существует"

    query = select(User).where(User.email == "test@example.com")
    result = await test_session.execute(query)
    users = result.scalars().all()

    assert len(users) == 1

    mock_send_email.assert_not_called()


async def test_register_user_protect_from_phone_number_duplication(
    mocker, async_client: AsyncClient, test_session: AsyncSession
):
    # Мокаем функцию send_email_after_successful_registration.delay
    mock_send_email = mocker.patch(
        "src.users.router.send_email_after_successful_registration.delay"
    )

    # Данные для регистрации пользователя c уже существующим phone_number
    new_user_data_with_existing_phone_number = {
        "email": "test@example1.com",
        "phone_number": "+79994567890",
        "name": "Test_User",
        "password": "Password123!",
        "password_confirm": "Password123!",
    }

    response = await async_client.post(
        "users/registration/", json=new_user_data_with_existing_phone_number
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Такой телефон уже существует"

    query = select(User).where(User.phone_number == "+79994567890")
    result = await test_session.execute(query)
    users = result.scalars().all()

    assert len(users) == 1

    mock_send_email.assert_not_called()


async def test_register_user_with_incorrect_phone_numbers(
    mocker, async_client: AsyncClient, test_session: AsyncSession
):
    # Мокаем функцию send_email_after_successful_registration.delay
    mock_send_email = mocker.patch(
        "src.users.router.send_email_after_successful_registration.delay"
    )

    new_user_data_with_incorrect_phone_number = {
        "email": "test@example2.com",
        "phone_number": "999456789",  # короткий номер (9 цифр вместо 10)
        "name": "Test_User",
        "password": "Password123!",
        "password_confirm": "Password123!",
    }

    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_phone_number
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, Номер невалиден"

    query = select(User).where(User.phone_number == "999456789")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None
    # длинный номер 12 цифр вмсето 11
    new_user_data_with_incorrect_phone_number["phone_number"] = "+799988877661"
    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_phone_number
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, Номер невалиден"

    query = select(User).where(User.phone_number == "+799988877661")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    # номер с неправльныи кодом оператора
    new_user_data_with_incorrect_phone_number["phone_number"] = "+71239998877"
    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_phone_number
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, Номер невалиден"

    query = select(User).where(User.phone_number == "+71239998877")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    mock_send_email.assert_not_called()


async def test_register_user_with_incorrect_password(
    mocker, async_client: AsyncClient, test_session: AsyncSession
):
    # Мокаем функцию send_email_after_successful_registration.delay
    mock_send_email = mocker.patch(
        "src.users.router.send_email_after_successful_registration.delay"
    )

    new_user_data_with_incorrect_password = {
        "email": "test@example2.com",
        "phone_number": "+79994567893",
        "name": "Test_User",
        "password": "password123!",  # отсутствует заглавная буква
        "password_confirm": "password123!",
    }

    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_password
    )

    assert response.status_code == 422
    msg = "Value error, Пароль должен содержать хотя бы одну заглавную букву"
    assert response.json()["detail"][0]["msg"] == msg

    query = select(User).where(User.email == "test@example2.com")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    # отсутствует строчная буква
    new_user_data_with_incorrect_password["password"] = "PASSWORD123!"
    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_password
    )

    assert response.status_code == 422
    msg = "Value error, Пароль должен содержать хотя бы одну строчную букву"
    assert response.json()["detail"][0]["msg"] == msg

    query = select(User).where(User.email == "test@example2.com")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    # отсутствует цифра
    new_user_data_with_incorrect_password["password"] = "Passworddd!"
    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_password
    )

    assert response.status_code == 422
    msg = "Value error, Пароль должен содержать хотя бы одну цифру"
    assert response.json()["detail"][0]["msg"] == msg

    query = select(User).where(User.email == "test@example2.com")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    # отсутствует спецсимвол
    new_user_data_with_incorrect_password["password"] = "Password123"
    response = await async_client.post(
        "users/registration/", json=new_user_data_with_incorrect_password
    )

    assert response.status_code == 422
    msg = "Value error, Пароль должен содержать хотя бы один спецсимвол"
    assert response.json()["detail"][0]["msg"] == msg

    query = select(User).where(User.email == "test@example2.com")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    mock_send_email.assert_not_called()


async def test_register_user_with_mismatch_passwords(
    mocker, async_client: AsyncClient, test_session: AsyncSession
):
    # Мокаем функцию send_email_after_successful_registration.delay
    mock_send_email = mocker.patch(
        "src.users.router.send_email_after_successful_registration.delay"
    )

    new_user_data_with_mismatch_passwords = {
        "email": "test@example2.com",
        "phone_number": "+79994567893",
        "name": "Test_User",
        "password": "Password123!",
        "password_confirm": "Password456!",
    }

    response = await async_client.post(
        "users/registration/", json=new_user_data_with_mismatch_passwords
    )

    assert response.status_code == 422
    msg = "Value error, Пароли не совпадают"
    assert response.json()["detail"][0]["msg"] == msg

    query = select(User).where(User.email == "test@example2.com")
    result = await test_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is None

    mock_send_email.assert_not_called()
