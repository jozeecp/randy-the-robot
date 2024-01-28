from pydantic import BaseModel

class RequestResponse(BaseModel):
    """
    MQTT message
    """
    success: bool
    message: str
    data: dict = {}


class SimpleMsg(BaseModel):
    message: str
    data: dict = {}