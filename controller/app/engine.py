import asyncio
from typing import Dict, Set, Tuple

import spatialmath as sm

from libs.db_client import DBClient
from libs.examples import ExampleFactory
from libs.mqtt_client import MQTTClient
from libs.robot_controller import RobotController
from libs.utils import get_logger
from models.spatial import NamedConfiguration, RigidBodyPose, TrajectoryOptions

logger = get_logger(__name__)


class Engine:
    def __init__(self, mqtt_client: MQTTClient, db_client: DBClient):
        self.mqtt_client = mqtt_client
        self.db_client = db_client
        self.robot_controller = RobotController(
            mqtt_client=mqtt_client, db_client=db_client
        )
        self.tasks: Set[asyncio.Task] = set()

    async def start(self, logger=logger):
        logger.info("Starting engine ...")
        logger.info("Engine started")

    async def patch_ee_pose(self, data: Dict[str, float]) -> Tuple[bool, str]:
        logger.debug(f"data: {data}")
        current_pose = await self.get_ee_pose()
        new_pose = current_pose
        logger.debug(f"current_pose: {current_pose}")
        for key, value in data.items():
            setattr(new_pose, key, value)
        logger.debug(f"new_pose: {new_pose}")

        logger.debug("Moving to new pose ...")
        return await self.move_to(new_pose, trajectory=True)

    async def get_ee_pose(self) -> RigidBodyPose:
        ee_pose = await self.robot_controller.get_ee_pose()
        rb_pose = RigidBodyPose(
            x=round(ee_pose.t[0], 2),
            y=round(ee_pose.t[1], 2),
            z=round(ee_pose.t[2], 2),
            roll=round(sm.SE3.rpy(ee_pose, unit="deg")[0], 2),
            pitch=round(sm.SE3.rpy(ee_pose, unit="deg")[1], 2),
            yaw=round(sm.SE3.rpy(ee_pose, unit="deg")[2], 2),
        )
        return rb_pose

    async def move_to(
        self, pose: RigidBodyPose, trajectory: bool = False
    ) -> Tuple[bool, str]:
        logger.info(f"Moving to pose: {pose}")
        target_pose = (
            sm.SE3.Tx(pose.x)
            * sm.SE3.Ty(pose.y)
            * sm.SE3.Tz(pose.z)
            * sm.SE3.RPY(pose.roll, pose.pitch, pose.yaw, unit="deg")
        )
        if not trajectory:
            logger.debug("Moving to target pose without trajectory")
            return await self.robot_controller.move_to(target_pose)
        else:
            logger.debug("Moving to target pose with trajectory")
            return await self.robot_controller.move_to_trajectory_single_target(
                target_pose
            )

    async def move_through_path(
        self,
        poses: list[RigidBodyPose],
        trajectory: bool = False,
        trajectory_options: TrajectoryOptions | None = None,
    ) -> Tuple[bool, str]:
        target_poses = [
            sm.SE3.Tx(pose.x)
            * sm.SE3.Ty(pose.y)
            * sm.SE3.Tz(pose.z)
            * sm.SE3.RPY(pose.roll, pose.pitch, pose.yaw, unit="deg")
            for pose in poses
        ]
        return await self.robot_controller.move_through_path(
            target_poses, trajectory, trajectory_options
        )

    async def run_example(self, example_type: str, *args, **kwargs) -> Tuple[bool, str]:
        """
        Run the given example.

        Args:
            example_type(str): The type of example to run.
            *args: Positional arguments to pass to the example.
            **kwargs: Keyword arguments to pass to the example.

        Returns:
            True, "OK" if the example ran successfully.
            False, <reason> if the example failed.
        """
        logger.debug(f"Running example: {example_type}")
        example = ExampleFactory().get_example(example_type)
        path = example.get_path(*args, **kwargs)
        logger.debug(
            f"received path with [ {len(path)} ] poses. Moving through path ..."
        )
        return await self.robot_controller.move_through_path(path)

    async def move_to_named_config(
        self, config: NamedConfiguration
    ) -> Tuple[bool, str]:
        return await self.robot_controller.move_to_named_config(config)

    async def get_configuration(self) -> NamedConfiguration:
        return await self.robot_controller.get_configuration()

    async def publish_controller_alive(self):
        await self.mqtt_client.publish("robot/controller/alive", "1")
