from typing import Any, Dict

from pydantic import BaseModel


class Msg(BaseModel):
    """
    MQTT message
    """

    topic: str
    payload: Dict[str, Any]
    qos: int = 0
