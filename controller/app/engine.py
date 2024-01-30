import asyncio
from libs.mqtt_client import MQTTClient
from libs.robot_controller import RobotController
from libs.db_client import DBClient
from models.spatial import RigidBodyPose, NamedConfiguration
import spatialmath as sm
from typing import Tuple, Set
from libs.utils import get_logger


logger = get_logger(__name__)


class Engine:
    def __init__(self, mqtt_client: MQTTClient, db_client: DBClient):
        self.mqtt_client = mqtt_client
        self.db_client = db_client
        self.robot_controller = RobotController(mqtt_client=mqtt_client, db_client=db_client)
        self.tasks: Set[asyncio.Task] = set()

    async def start(self, logger = logger):
        logger.info("Starting engine ...")
        logger.info("Engine started")

    async def get_ee_pose(self) -> RigidBodyPose:
        ee_pose = await self.robot_controller.get_ee_pose()
        rb_pose = RigidBodyPose(
            x=round(ee_pose.t[0], 2),
            y=round(ee_pose.t[1], 2),
            z=round(ee_pose.t[2], 2),
            roll=round(sm.SE3.eul(ee_pose, unit='deg')[0], 2),
            pitch=round(sm.SE3.eul(ee_pose, unit='deg')[1], 2),
            yaw=round(sm.SE3.eul(ee_pose, unit='deg')[2], 2),
        )
        return rb_pose

    async def move_to(self, pose: RigidBodyPose, trajectory: bool = False) -> Tuple[bool, str]:
        target_pose = sm.SE3.Tx(pose.x) * sm.SE3.Ty(pose.y) * sm.SE3.Tz(pose.z) * sm.SE3.RPY(pose.roll, pose.pitch, pose.yaw, unit='deg')
        if not trajectory:
            return await self.robot_controller.move_to(target_pose)
        else:
            return await self.robot_controller.move_to_trajectory_single_target(target_pose)

    async def move_to_named_config(self, config: NamedConfiguration) -> Tuple[bool, str]:
        return await self.robot_controller.move_to_named_config(config)

    async def get_configuration(self) -> NamedConfiguration:
        return await self.robot_controller.get_configuration()
    
    async def publish_controller_alive(self):
        await self.mqtt_client.publish("robot/controller/alive", "1")
