# mypy: ignore-errors
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from attackmate_api_server.main import app


@pytest.fixture
def patch_dependencies():
    with patch(
        'attackmate_api_server.main.get_user_hash'
    ) as mock_get_user_hash, patch(
        'attackmate_api_server.main.verify_password'
    ) as mock_verify_password, patch(
        'attackmate_api_server.main.create_access_token', return_value='mock_access_token'
    ) as mock_create_access_token, patch(
        'attackmate_api_server.routers.commands.get_persistent_instance'
    ) as mock_get_persistent_instance, patch(
        'attackmate_api_server.routers.commands.varstore_to_state_model',
        return_value={'state': 'data'}
    ) as mock_varstore_to_state:
        yield {
            'get_user_hash': mock_get_user_hash,
            'verify_password': mock_verify_password,
            'create_access_token': mock_create_access_token,
            'get_persistent_instance': mock_get_persistent_instance,
            'varstore_to_state_model': mock_varstore_to_state,
        }


@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/')
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_success(patch_dependencies) -> None:
    patch_dependencies['get_user_hash'].return_value = 'hashed_password'
    patch_dependencies['verify_password'].return_value = True

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post(
            '/login',
            data={'username': 'testuser', 'password': 'testpassword'}
        )

    assert response.status_code == 200
    assert response.json() == {'access_token': 'mock_access_token', 'token_type': 'bearer'}


@pytest.mark.asyncio
async def test_login_failure_user_not_found(patch_dependencies) -> None:
    patch_dependencies['get_user_hash'].return_value = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post(
            '/login',
            data={'username': 'unknownuser', 'password': 'anypassword'}
        )

    assert response.status_code == 401
    assert response.json()['detail'] == 'Incorrect username or password'
    patch_dependencies['get_user_hash'].assert_called_once_with('unknownuser')
    patch_dependencies['verify_password'].assert_not_called()


@pytest.mark.asyncio
async def test_login_failure_invalid_password(patch_dependencies) -> None:
    patch_dependencies['get_user_hash'].return_value = 'hashed_password'
    patch_dependencies['verify_password'].return_value = False

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post(
            '/login',
            data={'username': 'testuser', 'password': 'wrongpassword'}
        )

    assert response.status_code == 401
    assert response.json()['detail'] == 'Incorrect username or password'
    patch_dependencies['get_user_hash'].assert_called_once_with('testuser')
    patch_dependencies['verify_password'].assert_called_once_with('wrongpassword', 'hashed_password')
