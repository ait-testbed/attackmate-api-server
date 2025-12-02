import logging

from fastapi import APIRouter, Depends
from attackmate.attackmate import AttackMate

from auth_utils import get_current_user
from schemas import VariableStoreStateModel
from utils import varstore_to_state_model

from state import get_instance_by_id, get_persistent_instance

router = APIRouter(tags=['Instances'])
logger = logging.getLogger('attackmate_api')


@router.get('/{instance_id}/state', response_model=VariableStoreStateModel)
async def get_instance_state(
    instance: AttackMate = Depends(get_instance_by_id),
    current_user: str = Depends(get_current_user)
):
    return varstore_to_state_model(instance.varstore)


@router.get('/state', response_model=VariableStoreStateModel)
async def get_persistent_instance_state(
    instance: AttackMate = Depends(get_persistent_instance),
    current_user: str = Depends(get_current_user)
):
    return varstore_to_state_model(instance.varstore)
