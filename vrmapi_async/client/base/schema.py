from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseTemplateModel(PydanticBaseModel):
    """
    Base model for all VRM API schemas.
    Mainly used to override global configuration settings.
    """
    pass

    # model_config = ConfigDict(extra="forbid", populate_by_name=True)

class BaseModel(BaseTemplateModel):
    
    """
    Base model for all VRM API schemas.
    Inherits from BaseTemplateModel to apply global configuration.
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    # This is the default behavior, but we can override it in specific models
    # if needed. For now, we keep it strict to avoid unexpected fields.

class BaseResponseModel(BaseTemplateModel):
    """
    Base model for all VRM API response schemas.
    Inherits from BaseTemplateModel to apply global configuration.
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
