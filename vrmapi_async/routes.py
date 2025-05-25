from dataclasses import dataclass


@dataclass(frozen=True)
class VRMPaths:
    """Holds all VRM API endpoint path templates."""

    AUTH_LOGIN: str = "/auth/login"
    AUTH_DEMO: str = "/auth/loginAsDemo"

    USERS_INSTALLATIONS: str = "/users/{user_id}/installations"

    INSTALLATIONS_STATS: str = "/installations/{inst_id}/stats"
    INSTALLATIONS_OVERALL_STATS: str = "/installations/{inst_id}/overallstats"
    INSTALLATIONS_DIAGNOSTICS: str = "/installations/{inst_id}/diagnostics"

    INSTALLATIONS_WIDGETS: str = "/installations/{inst_id}/widgets/{widget_type}"
