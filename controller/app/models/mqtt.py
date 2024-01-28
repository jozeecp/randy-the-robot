from pydantic import BaseModel
from typing import Any, Dict


class Msg(BaseModel):
    """
    MQTT message
    """

    topic: str
    payload: Dict[str, Any]
    qos: int = 0
