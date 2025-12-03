from typing import Any, Dict

from attackmate.variablestore import VariableStore

from attackmate_api_server.schemas import VariableStoreStateModel


def varstore_to_state_model(varstore: VariableStore) -> VariableStoreStateModel:
    """Converts AttackMate VariableStore to Pydantic VariableStoreStateModel."""
    combined_vars: Dict[str, Any] = {}
    combined_vars.update(varstore.variables)
    combined_vars.update(varstore.lists)
    return VariableStoreStateModel(variables=combined_vars)
