from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """
    Base model for all VRM API schemas.
    Mainly used to override global configuration settings.
    """

    # VRM API doesn't change much, but there is no explicit guarantee so we'll
    # go with the ignore middle ground.
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    # TODO change this
