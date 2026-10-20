from typing import Any, Mapping


def is_service_owner(service_config: Mapping[str, Any], user: Any) -> bool:
    usage_data = service_config.get("usage_data")
    owner_id = None
    if isinstance(usage_data, dict):
        owner_id = usage_data.get("user_id")

    if owner_id is not None:
        return str(owner_id) == str(user.id)

    return service_config.get("usuario") == user.name
