import roboticstoolbox as rtb
import spatialmath as sm
import numpy as np
from math import pi, degrees
from libs.utils import get_logger, get_unix_ts, custom_pformat as pf
from libs.mqtt_client import MQTTClient
from typing import Tuple
from models.spatial import NamedConfiguration, LastConfiguration
from libs.db_client import DBClient
import time

logger = get_logger(__name__)


class RobotController:
    """
    This class is responsible for controlling the robot.
    """

    def __init__(self, mqtt_client: MQTTClient, db_client: DBClient) -> None:
        self.mqtt_client = mqtt_client
        self.db_client = db_client
        self.robot = rtb.DHRobot(
            links=[
                rtb.RevoluteDH(alpha=pi/2),  # base
                rtb.RevoluteDH(a=0.381, offset=pi/2),  # shoulder
                rtb.RevoluteDH(alpha=pi/2, offset=pi/2),  # elbow
                rtb.RevoluteDH(d=0.254, alpha=pi/2),  # wrist0
                rtb.RevoluteDH(alpha=-pi/2),  # wrist1 a=0.0635
                rtb.RevoluteDH(d=0.0254 + 0.0635), # wrist2
            ], 
            name="DUM-Arm",
            # gravity=[0, 0, -9.81],
            base=sm.SE3(0.0, 0.0, 0.1016),
            # qr=[0, 0, 0, 0, 0, 0],
        )

    async def move_to(self, pose: sm.SE3) -> Tuple[bool, str]:
        """
        Move the robot to the given pose.

        Args:
            pose(spatialmath.SE3): The pose to move to.

        Returns:
            True, "OK" if the move was successful.
            False, <reason> if the move failed.
        """

        # get the current config
        logger.debug("Getting current config ...")
        current_config = await self.get_configuration()
        logger.debug(f"Current config:\n{pf(current_config)}")
        q0 = await self.named_config_to_q(current_config)
        logger.debug(f"Current config: {q0}")

        # get the final configuration via inverse kinematics
        logger.debug("Running IK ...")
        logger.debug(f"Target pose:\n{pf(pose.t)}\n{pf(pose.R)}")
        qf = self.robot.ikine_LM(pose, q0=q0)
        logger.debug(f"Final config: {qf.q}")
        if not qf.success:
            logger.error(f"IK failed: {qf.reason}")
            return False, qf.reason

        # validate the final configuration
        forward_kin_pose = self.robot.fkine(qf.q)
        logger.debug(f"Forward kinematics pose:\n{pf(forward_kin_pose.t)}\n{pf(forward_kin_pose.R)}")
        if not self.validate_pose_close_enough(pose, forward_kin_pose):
            logger.error(
                f"FK failed: {forward_kin_pose.t} != {pose.t} or {forward_kin_pose.R} != {pose.R}"
            )
            return False, "FK failed"

        # publish the final configuration (this is what actually moves the robot)
        logger.debug("Publishing final configuration ...")
        config = LastConfiguration.model_validate((await self.q_to_named_config(qf.q)).model_dump())
        logger.debug(f"Final configuration:\n{pf(config)}")
        await self.publish_configuration(config)
        logger.debug("Published final configuration")

        # save the final configuration
        self.db_client.set(get_unix_ts(), config)
        logger.debug("Saved final configuration")

        return True, "OK"

    async def get_pose(self) -> sm.SE3:
        last_configuration = await self.get_configuration()
        return self.q_to_pose(await self.named_config_to_q(last_configuration))
    
    async def get_configuration(self) -> NamedConfiguration:
        # save the current configuration
        ts_a = time.time()
        last_configuration = self.db_client.get_latest(LastConfiguration)
        ts_b = time.time()
        logger.debug(f"get_configuration took {ts_b - ts_a} seconds")
        if ts_b - ts_a > 0.1:
            logger.warning(f"get_configuration took {ts_b - ts_a} seconds")
        
        if last_configuration is None:
            logger.warning("No last configuration found, using default configuration")
            last_configuration = NamedConfiguration(
                base=0,
                shoulder=0,
                elbow=0,
                wrist0=0,
                wrist1=0,
                wrist2=0,
            )
        return last_configuration

    async def q_to_pose(self, q: np.ndarray) -> sm.SE3:
        return self.robot.fkine(q)

    async def q_to_named_config(self, q: np.ndarray) -> NamedConfiguration:
        return NamedConfiguration(
            base=q[0],
            shoulder=q[1],
            elbow=q[2],
            wrist0=q[3],
            wrist1=q[4],
            wrist2=q[5],
        )
    
    async def named_config_to_q(self, config: NamedConfiguration) -> np.ndarray:
        return np.array([
            config.base,
            config.shoulder,
            config.elbow,
            config.wrist0,
            config.wrist1,
            config.wrist2,
        ])

    async def publish_configuration(self, configuration: NamedConfiguration) -> None:
        """
        IMPORTANT: This is what moves "actually" moves the robot.
        """

        for k, v in configuration.model_dump().items():
            logger.debug(f"publishing {k}={degrees(v)}  ...")
            await self.mqtt_client.publish(f"robot/{k}/position", degrees(v))

    def validate_pose_close_enough(self, target_pose: sm.SE3, current_pose: sm.SE3) -> bool:
        """
        Validate that the current pose is close enough to the target pose.
        """
        return np.allclose(target_pose.t, current_pose.t, atol=0.01) and np.allclose(
            target_pose.R, current_pose.R, atol=0.01
        )

