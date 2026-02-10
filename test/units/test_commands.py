# mypy: ignore-errors
from typing import Any, Dict, Generator
import pytest
from contextlib import ExitStack
from fastapi import FastAPI
from unittest.mock import patch, MagicMock, AsyncMock
from attackmate.result import Result as AttackMateResult
from attackmate.schemas.base import BaseCommand


@pytest.fixture
def mock_command_dependencies() -> Generator[Dict[str, Any], None, None]:
    """Mocks dependencies for the command router endpoints.

    Uses ExitStack for safe context manager grouping in Python 3.10.
    """
    with ExitStack() as stack:
        mock_get_current_user = stack.enter_context(
            patch('attackmate_api_server.routers.commands.get_current_user', return_value='testuser')
        )
        mock_get_persistent_instance = stack.enter_context(
            patch('attackmate_api_server.routers.commands.get_persistent_instance')
        )
        mock_varstore_to_state_model = stack.enter_context(
            patch(
                'attackmate_api_server.routers.commands.varstore_to_state_model',
                return_value={
                    'state': 'data'}))

        yield {
            'get_current_user': mock_get_current_user,
            'get_persistent_instance': mock_get_persistent_instance,
            'varstore_to_state_model': mock_varstore_to_state_model
        }


@pytest.fixture
def mock_command_app(mock_command_dependencies) -> FastAPI:
    from fastapi import FastAPI
    from attackmate_api_server.routers import commands
    app = FastAPI()
    app.include_router(commands.router)
    return app


@pytest.mark.asyncio
async def test_run_command_on_instance_success() -> None:
    from attackmate_api_server.routers.commands import run_command_on_instance

    mock_instance = AsyncMock()
    mock_command = MagicMock(spec=BaseCommand, type='test_command')
    mock_result = AttackMateResult(returncode=0, stdout='Success output')
    mock_instance.run_command.return_value = mock_result

    result = await run_command_on_instance(mock_instance, mock_command)

    assert result == mock_result
    mock_instance.run_command.assert_called_once_with(mock_command)
    assert result.returncode == 0
