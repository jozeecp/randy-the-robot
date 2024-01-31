import math
from typing import List

from pydantic import BaseModel

from models.spatial import NamedConfiguration, RigidBodyPose, TrajectoryOptions


class MoveToNamedConfigRequest(NamedConfiguration):
    @property
    def radian_config(self):
        return NamedConfiguration(
            base=math.radians(self.base),
            shoulder=math.radians(self.shoulder),
            elbow=math.radians(self.elbow),
            wrist0=math.radians(self.wrist0),
            wrist1=math.radians(self.wrist1),
            wrist2=math.radians(self.wrist2),
        )


class MoveThroughPathRequest(BaseModel):
    poses: List[RigidBodyPose]
    trajectory: bool = False
    trajectory_options: TrajectoryOptions = TrajectoryOptions()
