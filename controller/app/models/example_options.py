from pydantic import BaseModel


class BaseExampleOptions(BaseModel):
    """
    Base options for examples
    """

    amount_of_steps: int = 50


class SpiralExampleOptions(BaseExampleOptions):
    """
    Options for spiral example
    """

    radius: float = 0.1
    height: float = 0.1
    amount_of_turns: int = 5
    clockwise: bool = True


class SwingExampleOptions(BaseExampleOptions):
    amount_of_swings: int = 5
    height: float = 0.1
    radius: float = 0.1


class SquareExampleOptions(BaseExampleOptions):
    side_length: float = 0.1
    height: float = 0.1
