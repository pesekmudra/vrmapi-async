from pydantic import Field, ConfigDict, model_validator
from typing import List, Optional, Dict, Any

from vrmapi_async.client.base.schema import BaseModel, BaseResponseModel


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

    pc: Optional[List[StatsRecord] | bool] = Field(None, alias="Pc")
    bc: Optional[List[StatsRecord] | bool] = Field(None, alias="Bc")
    gc: Any = Field(..., alias="Gc")  
    gc_lower: Any = Field(..., alias="gc")  

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


class ConsumptionStatsResponse(BaseResponseModel):
    """Response model for consumption/kwh stats."""

    success: bool
    records: ConsumptionData
    totals: Dict[str, Any]
