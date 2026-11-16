from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BaseContract(BaseModel):
    """
    Frozen base contract model for all domain entities.
    Contracts are immutable value objects ensuring cross-module referential stability.
    """
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

