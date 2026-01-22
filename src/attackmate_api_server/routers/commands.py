import logging
from typing import Optional

from attackmate.attackmate import AttackMate
from attackmate.schemas.base import BaseCommand
from fastapi import APIRouter, Depends, Header, HTTPException
from attackmate.execexception import ExecException
from attackmate.result import Result as AttackMateResult
from attackmate.schemas.command_subtypes import RemotelyExecutableCommand

from attackmate_api_server.auth_utils import API_KEY_HEADER_NAME, get_current_user
from attackmate_api_server.schemas import CommandResultModel, ExecutionResponseModel
from attackmate_api_server.utils import varstore_to_state_model
from attackmate_api_server.state import get_persistent_instance


router = APIRouter(prefix='/command', tags=['Commands'])
logger = logging.getLogger('attackmate_api')


async def run_command_on_instance(instance: AttackMate, command_data: BaseCommand) -> AttackMateResult:
    """Runs a command on a given AttackMate instance."""
    try:
        logger.info(f"Executing command type '{command_data.type}' on instance")  # type: ignore
        result = await instance.run_command(command_data)
        logger.info(f'Command execution finished. RC: {result.returncode}')
        return result
    except (ExecException, SystemExit) as e:
        logger.error(f'AttackMate execution error: {e}', exc_info=True)
        raise e
    except Exception as e:
        logger.error(f'Unexpected error during instance.run_command: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Internal server error during command execution: {e}')


@router.post('/execute', response_model=ExecutionResponseModel)
async def execute_unified_command(
    command_request: RemotelyExecutableCommand,
    instance: AttackMate = Depends(get_persistent_instance),
    current_user: str = Depends(get_current_user),
    x_auth_token: Optional[str] = Header(None, alias=API_KEY_HEADER_NAME)
):
    # command_request will be the correct Pydantic type based on discriminated
    # union in RemotelyExecutableCommand
    attackmate_result = await run_command_on_instance(instance, command_request)

    result_model = CommandResultModel(
        success=(attackmate_result.returncode == 0 if attackmate_result.returncode is not None else True),
        stdout=str(attackmate_result.stdout) if attackmate_result.stdout is not None else '',
        returncode=attackmate_result.returncode
    )
    state_model = varstore_to_state_model(instance.varstore)
    return ExecutionResponseModel(
        result=result_model,
        state=state_model,
        instance_id='default-context',
        current_token=x_auth_token
    )
