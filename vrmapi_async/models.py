# --- vrmapi_async/models.py
"""Pydantic models for VRM API responses."""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List, Optional, Dict, Any


class LoginResponse(BaseModel):
    """Response model for successful login."""

    token: str
    id_user: int = Field(..., alias="idUser")


class Site(BaseModel):
    """
    Model for a VRM Site (Non-Extended).
    Strictly defines fields expected in the non-extended response.
    """

    id_site: int = Field(..., alias="idSite")
    access_level: int = Field(..., alias="accessLevel")
    owner: bool
    is_admin: bool
    name: str
    identifier: str
    id_user: int = Field(..., alias="idUser")
    pv_max: Optional[float | int] = Field(None, alias="pvMax")
    timezone: Optional[str] = None
    phonenumber: Optional[str | int] = None
    notes: Optional[str] = None
    geofence: Optional[str] = None
    geofence_enabled: bool = Field(..., alias="geofenceEnabled")
    realtime_updates: bool = Field(..., alias="realtimeUpdates")
    has_mains: int = Field(..., alias="hasMains")
    has_generator: int = Field(..., alias="hasGenerator")
    no_data_alarm_timeout: Optional[int] = Field(None, alias="noDataAlarmTimeout")
    alarm_monitoring: int = Field(..., alias="alarmMonitoring")
    invalid_vrm_auth_token_used_in_log_request: int = Field(
        ..., alias="invalidVRMAuthTokenUsedInLogRequest"
    )
    syscreated: int
    is_paygo: int = Field(..., alias="isPaygo")
    paygo_currency: Optional[str] = Field(None, alias="paygoCurrency")
    paygo_total_amount: Optional[float] = Field(None, alias="paygoTotalAmount")
    id_currency: Optional[int] = Field(None, alias="idCurrency")
    currency_code: Optional[str] = Field(None, alias="currencyCode")
    currency_sign: Optional[str] = Field(None, alias="currencySign")
    currency_name: Optional[str] = Field(None, alias="currencyName")
    inverter_charger_control: int = Field(..., alias="inverterChargerControl")
    shared: bool
    device_icon: Optional[str] = Field(None, alias="device_icon")

    # only allow defined fields for the base model
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SiteExtended(Site):
    """
    Model for an Extended VRM Site. Inherits from Site and allows
    extra fields, capturing the 'extended' block.
    """

    # tags: Optional[List[Dict[str, Any]]] = None
    # extended: Optional[Dict[str, Any]] = None
    # Add any other specific top-level fields from extended you want to model
    alarm: Optional[int] = None
    last_timestamp: Optional[int] = Field(None, alias="last_timestamp")
    # ... etc.

    # Allow extra fields for the extended model
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class UserSitesResponse(BaseModel):
    """Response model for fetching non-extended user sites."""

    success: bool
    records: List[Site]


class UserSitesExtendedResponse(BaseModel):
    """Response model for fetching extended user sites."""

    success: bool
    records: List[SiteExtended]


class ErrorResponse(BaseModel):
    """Generic error response model."""

    success: bool
    errors: Dict[str, Any]


class StatsRecord(BaseModel):
    """
    Represents a single [timestamp, value] data point from a stats response.
    The timestamp is typically in milliseconds.
    """

    timestamp: int
    value: float | None  # Sometimes value can be null

    @model_validator(mode="before")
    @classmethod
    def transform_list_to_dict(cls, data: Any) -> Any:
        """
        Transforms a [timestamp, value] list into a dictionary
        before Pydantic validation.
        """
        if isinstance(data, list) and len(data) == 2:
            return {"timestamp": data[0], "value": data[1]}
        if isinstance(data, dict):
            return data
        # If it's not a list or dict, maybe it's the 'False' case -
        # but that should be handled by the Union in the parent model.
        # We raise here if it's not a list, as StatsRecord itself MUST be a list.
        raise ValueError(
            f"Unexpected data format for StatsRecord: Expected [ts, val], got {data!r}"
        )


class ConsumptionData(BaseModel):
    """Model for the 'records' part of consumption/kwh stats."""

    # Use Union to allow List of records OR a boolean False
    pc: Optional[List[StatsRecord] | bool] = Field(None, alias="Pc")
    bc: Optional[List[StatsRecord] | bool] = Field(None, alias="Bc")
    gc: Any = Field(..., alias="Gc")  # Keep as Any or bool if always False
    gc_lower: Any = Field(..., alias="gc")  # Keep as Any or bool if always False

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def handle_false_records(cls, data: Any) -> Any:
        """
        Pydantic needs help when a field can be List[Model] or bool.
        If a field is bool, Pydantic might try to validate it against StatsRecord.
        This validator isn't strictly necessary if Union works directly, but
        it can help clarify or pre-process if needed. For now, we trust Union.
        If Union fails, we might need a more complex validator here.
        Let's try without an extra validator first, relying on Union.
        """
        # If Union[List[StatsRecord], bool] works directly, this validator
        # might not be needed. Let's start without it and add it back
        # only if Pydantic struggles with the Union type during list validation.
        return data


class ConsumptionStatsResponse(BaseModel):
    """Response model for consumption/kwh stats."""

    success: bool
    records: ConsumptionData
    totals: Dict[str, Any]
