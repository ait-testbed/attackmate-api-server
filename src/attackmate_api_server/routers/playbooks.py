import logging
import uuid
from typing import Optional
import yaml
from attackmate.schemas.playbook import Playbook
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from pydantic import ValidationError
from attackmate.attackmate import AttackMate
from attackmate_api_server.auth_utils import API_KEY_HEADER_NAME, get_current_user
from attackmate_api_server.schemas import PlaybookResponseModel
from attackmate_api_server.utils import varstore_to_state_model
from attackmate_api_server.log_utils import instance_logging
from attackmate_api_server.state import attackmate_config
from attackmate_api_server.config import settings

router = APIRouter(prefix='/playbooks', tags=['Playbooks'])
logger = logging.getLogger('attackmate_api')


@router.post('/execute/yaml', response_model=PlaybookResponseModel)  # type: ignore[misc]
async def execute_playbook_from_yaml(
    playbook_yaml: str = Body(..., media_type='application/yaml'),
    debug: bool = Query(
        False,
        description=(
            "Enable DEBUG log level for the AttackMate instance executing this playbook. "
            "File logging on the API server is controlled by WRITE_PLAYBOOK_LOGS_TO_DISK in .env."
        )
    ),
    current_user: str = Depends(get_current_user),
    x_auth_token: Optional[str] = Header(None, alias=API_KEY_HEADER_NAME)
) -> PlaybookResponseModel:
    """Executes a playbook provided as YAML content in the request body. Uses a
    transient AttackMate instance.

    - `debug` (query param): controls the AttackMate instance log level (DEBUG vs INFO)
    - `WRITE_PLAYBOOK_LOGS_TO_DISK` (.env setting): instance logs saved to disk on the server
    """
    logger.info('Received request to execute playbook from YAML content.')
    instance_id = str(uuid.uuid4())

    # debug (query param)  -> AttackMate instance log level
    instance_log_level = logging.DEBUG if debug else logging.INFO
    write_logs_to_disk = settings.write_playbook_logs_to_disk

    am_instance = None
    return_code = 1
    final_state = None
    attackmate_log: Optional[str] = None
    output_log: Optional[str] = None
    json_log: Optional[str] = None

    with instance_logging(
        instance_id,
        write_playbook_logs_to_disk=write_logs_to_disk,
        log_level=instance_log_level
    ) as log_ctx:
        try:
            playbook_dict = yaml.safe_load(playbook_yaml)
            if not playbook_dict:
                raise ValueError('Received empty or invalid playbook YAML content.')
            playbook = Playbook.model_validate(playbook_dict)
            logger.info(f'Creating transient AttackMate instance, ID: {instance_id}')
            am_instance = AttackMate(playbook=playbook, config=attackmate_config, varstore=None)
            return_code = await am_instance.main()
            final_state = varstore_to_state_model(am_instance.varstore)
            logger.info(f'Transient playbook execution finished. Return code: {return_code}')
        except (yaml.YAMLError, ValidationError, ValueError) as e:
            logger.error(f'Playbook validation/parsing error: {e}')
            raise HTTPException(status_code=422, detail=f'Invalid playbook YAML: {e}')
        except Exception as e:
            logger.error(f'Unexpected error during playbook execution: {e}', exc_info=True)
            raise HTTPException(status_code=500, detail=f'Server error during playbook execution: {e}')
        finally:
            if am_instance:
                logger.info('Cleaning up transient playbook instance.')
                try:
                    await am_instance.clean_session_stores()
                    am_instance.pm.kill_or_wait_processes()
                except Exception as cleanup_e:
                    logger.error(f'Error cleaning transient instance: {cleanup_e}', exc_info=True)

        # Always return logs from in-memory capture (always sent back to client)
        mem = log_ctx['mem_handlers']
        attackmate_log = '\n'.join(mem['playbook'].get_logs()) or None
        output_log = '\n'.join(mem['output'].get_logs()) or None
        json_log = '\n'.join(mem['json'].get_logs()) or None

        # Optionally include file paths in logs if written to disk
        if write_logs_to_disk:
            log_files = log_ctx['log_files']
            logger.info(f'Instance logs written to disk: {log_files}')

    return PlaybookResponseModel(
        success=(return_code == 0),
        message='Playbook execution finished.',
        final_state=final_state,
        instance_id=instance_id,
        attackmate_log=attackmate_log,
        output_log=output_log,
        json_log=json_log,
        current_token=x_auth_token
    )
