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

    async def move_to(self, pose: RigidBodyPose) -> Tuple[bool, str]:
        target_pose = sm.SE3.RPY(pose.roll, pose.pitch, pose.yaw, unit='deg') * sm.SE3.Tx(pose.x) * sm.SE3.Ty(pose.y) * sm.SE3.Tz(pose.z)
        return await self.robot_controller.move_to(target_pose)
    
    async def get_configuration(self) -> NamedConfiguration:
        return await self.robot_controller.get_configuration()
    
    async def publish_controller_alive(self):
        await self.mqtt_client.publish("robot/controller/alive", "1")
