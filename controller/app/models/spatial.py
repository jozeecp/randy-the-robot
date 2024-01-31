from pydantic import BaseModel


class RigidBodyPose(BaseModel):
    """
    Rigid body pose in 3D space

    Note: roll, pitch, yaw are in degrees, not radians
    """

    x: float
    y: float
    z: float
    roll: float  # deg
    pitch: float  # deg
    yaw: float  # deg


class NamedConfiguration(BaseModel):
    base: float
    shoulder: float
    elbow: float
    wrist0: float
    wrist1: float
    wrist2: float


class LastConfiguration(NamedConfiguration):
    __redis_db__ = 1


class TrajectoryOptions(BaseModel):
    """
    All options should have default values
    """

    amount_of_steps: int = 50
