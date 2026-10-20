from typing import Any, Mapping, Set

from . import config


def user_has_ti_role(user: Any) -> bool:
    try:
        ti_role_id = int(config.CARGO_TI_ID)
    except (TypeError, ValueError):
        return False

    return any(role.id == ti_role_id for role in getattr(user, "roles", []))


def roles_can_access_service(role_ids: Set[int], service_config: Mapping[str, Any]) -> bool:
    try:
        ti_role_id = int(config.CARGO_TI_ID)
    except (TypeError, ValueError):
        ti_role_id = None

    if ti_role_id in role_ids:
        return True

    allowed_role_ids = set()
    for role_id in service_config.get("grupos_permitidos") or []:
        try:
            allowed_role_ids.add(int(role_id))
        except (TypeError, ValueError):
            continue

    return bool(role_ids.intersection(allowed_role_ids))


def user_can_access_service(user: Any, service_config: Mapping[str, Any]) -> bool:
    role_ids = {role.id for role in getattr(user, "roles", [])}
    return roles_can_access_service(role_ids, service_config)
