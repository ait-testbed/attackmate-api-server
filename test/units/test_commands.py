import pytest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock
from attackmate.result import Result as AttackMateResult
from attackmate.schemas.base import BaseCommand
# Mock the AttackMate dependencies and the router


@pytest.fixture
def mock_command_dependencies():
    """
    Mocks dependencies for the command router endpoints.
    Uses ExitStack for safe context manager grouping in Python 3.10.
    """
    with ExitStack() as stack:
        # Patch dependencies in the module where they are looked up (routers.commands)
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

        # Yield the mocked objects to the tests for configuration (e.g., setting return_value)
        yield {
            'get_current_user': mock_get_current_user,
            'get_persistent_instance': mock_get_persistent_instance,
            'varstore_to_state_model': mock_varstore_to_state_model
        }

# Define a mock application that includes the commands router


@pytest.fixture
def mock_command_app(mock_command_dependencies):
    from fastapi import FastAPI
    from attackmate_api_server.routers import commands
    app = FastAPI()
    app.include_router(commands.router)
    return app


@pytest.mark.asyncio
async def test_run_command_on_instance_success():
    from attackmate_api_server.routers.commands import run_command_on_instance

    mock_instance = MagicMock()
    mock_command = MagicMock(spec=BaseCommand, type='test_command')
    mock_result = AttackMateResult(returncode=0, stdout='Success output')
    mock_instance.run_command.return_value = mock_result

    result = await run_command_on_instance(mock_instance, mock_command)

    assert result == mock_result
    mock_instance.run_command.assert_called_once_with(mock_command)
    assert result.returncode == 0
