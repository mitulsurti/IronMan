from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from ironman.config import get_settings


@dataclass(frozen=True)
class Actor:
    actor_id: str
    actor_type: str


# Development boundary only. Production authentication provider is intentionally flexible.
def get_current_actor(x_ironman_actor: str | None = Header(default=None)) -> Actor:
    settings = get_settings()
    if settings.auth_mode == "development":
        return Actor(settings.single_user_id, "human")
    if not x_ironman_actor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return Actor(x_ironman_actor, "human")
