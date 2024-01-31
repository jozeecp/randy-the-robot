import numpy as np
import spatialmath as sm

from libs.utils import get_logger
from models.example_options import (
    SpiralExampleOptions,
    SquareExampleOptions,
    SwingExampleOptions,
)

logger = get_logger(__name__)


class BaseExample:
    def __init__(self) -> None:
        pass

    def get_path(self, *args, **kwargs):
        raise NotImplementedError


class ExampleFactory:
    def __init__(self) -> None:
        pass

    def get_example(self, example_type: str) -> BaseExample:
        if example_type == "spiral":
            return SpiralExample()
        elif example_type == "swing":
            return SwingExample()
        elif example_type == "square":
            return SquareExample()
        else:
            raise ValueError(f"Invalid example type: {example_type}")


class SpiralExample(BaseExample):
    def __init__(self) -> None:
        super().__init__()

    def get_path(self, *args, **kwargs):
        logger.debug(f"kwargs: {kwargs}")
        options = SpiralExampleOptions(**kwargs)
        logger.debug(f"options: {options}")
        return self.generate_spiral_path(options)

    def generate_spiral_path(
        self, options: SpiralExampleOptions, offset: float = 0.2
    ) -> list[sm.SE3]:
        path = []
        t = np.linspace(0, 2 * np.pi * options.amount_of_turns, options.amount_of_steps)
        z = np.linspace(0, options.height, options.amount_of_steps)

        for t, z_ in zip(t, z):
            x = options.radius * np.sin(t) + offset
            y = options.radius * np.cos(t) + offset
            zf = z_ + offset
            path.append(
                sm.SE3(x, y, zf)
                * sm.SE3.RPY(
                    0 + (np.cos(t) * 30), 180 + (np.sin(t) * 30), 0, unit="deg"
                )
            )

        return path


class SwingExample(BaseExample):
    def __init__(self) -> None:
        super().__init__()

    def get_path(self, *args, **kwargs):
        logger.debug(f"kwargs: {kwargs}")
        options = SwingExampleOptions(**kwargs)
        logger.debug(f"options: {options}")
        return self.generate_swing_path(options)

    def generate_swing_path(
        self, options: SwingExampleOptions, offset: float = 0.2
    ) -> list[sm.SE3]:
        logger.debug(f"options: {options}")
        path = []
        # move back and forth in x, staying at the same height and at the same y
        t = np.linspace(
            0, 2 * np.pi * options.amount_of_swings, options.amount_of_steps
        )
        logger.debug(f"t: {t}")
        for t_ in t:
            x = options.radius * np.sin(t_) + offset
            y = options.radius * np.cos(t_) * 0.5 + offset
            z = options.height - abs(options.height * np.cos(t_) * 0.5)
            path.append(
                sm.SE3(x, y, z) * sm.SE3.RPY(0, 180, 90 * np.sin(t_), unit="deg")
            )

        return path


class SquareExample(BaseExample):
    def __init__(self) -> None:
        super().__init__()

    def get_path(self, *args, **kwargs):
        logger.debug(f"kwargs: {kwargs}")
        options = SquareExampleOptions(**kwargs)
        logger.debug(f"options: {options}")
        return self.generate_square_path(options)

    def generate_square_path(
        self, options: SquareExampleOptions, offset: float = 0.2
    ) -> list[sm.SE3]:
        path = []
        # divide the square into 4 segments

        # segment 1, move along x ->
        x_array = np.linspace(0, options.side_length, options.amount_of_steps // 4)
        for x in x_array:
            path.append(
                sm.SE3(x + offset, 0 + offset, options.height)
                * sm.SE3.RPY(0, 180, 0, unit="deg")
            )

        # segment 2, move along y ^
        y_array = np.linspace(0, options.side_length, options.amount_of_steps // 4)
        for y in y_array:
            path.append(
                sm.SE3(options.side_length + offset, y + offset, options.height)
                * sm.SE3.RPY(0, 180, 0, unit="deg")
            )

        # segment 3, move along x <-
        x_array = np.linspace(options.side_length, 0, options.amount_of_steps // 4)
        for x in x_array:
            path.append(
                sm.SE3(x + offset, options.side_length + offset, options.height)
                * sm.SE3.RPY(0, 180, 0, unit="deg")
            )

        # segment 4, move along y v
        y_array = np.linspace(options.side_length, 0, options.amount_of_steps // 4)
        for y in y_array:
            path.append(
                sm.SE3(0 + offset, y + offset, options.height)
                * sm.SE3.RPY(0, 180, 0, unit="deg")
            )

        return path
