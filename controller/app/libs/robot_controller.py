import asyncio
import hashlib
import pickle
import time
from math import degrees, pi
from typing import List, Set, Tuple

import numpy as np
import roboticstoolbox as rtb
import spatialmath as sm

from libs.db_client import DBClient
from libs.mqtt_client import MQTTClient
from libs.utils import custom_pformat as pf
from libs.utils import get_logger, get_unix_ts
from models.spatial import LastConfiguration, NamedConfiguration, TrajectoryOptions

logger = get_logger(__name__)
logger.setLevel("INFO")


class RobotController:
    """
    This class is responsible for controlling the robot.
    """

    def __init__(self, mqtt_client: MQTTClient, db_client: DBClient) -> None:
        self.mqtt_client = mqtt_client
        self.db_client = db_client

        self.tasks: Set[asyncio.Task] = set()
        self.inverse_kinematics_cache = {}
        self.robot = rtb.DHRobot(
            links=[
                rtb.RevoluteDH(alpha=pi / 2, offset=pi),  # base
                rtb.RevoluteDH(a=0.381, offset=pi / 2),  # shoulder
                rtb.RevoluteDH(alpha=pi / 2, offset=pi / 2),  # elbow
                rtb.RevoluteDH(d=0.254, alpha=pi / 2),  # wrist0
                rtb.RevoluteDH(alpha=-pi / 2),  # wrist1 a=0.0635
                rtb.RevoluteDH(d=0.0254 + 0.0635),  # wrist2
            ],
            name="DUM-Arm",
            gravity=[0, 0, -9.81],
            base=sm.SE3(0.0, 0.0, 0.1016),
        )

        logger.debug(f"robot: {self.robot}")
        self.robot.qlim = [
            [-pi / 2, -pi, -pi, -pi, -pi, -pi],
            [pi / 2, pi, pi, pi, pi, pi],
        ]
        logger.debug(f"qlim:\n{self.robot.qlim}")

    async def move_to_named_config(
        self, config: NamedConfiguration
    ) -> Tuple[bool, str]:
        last_configuration = await self.get_configuration()
        q0 = await self.named_config_to_q(last_configuration)

        qf = await self.named_config_to_q(config)
        logger.debug(f"qf: {qf}")
        await self.publish_configuration(config)

        self.db_client.set(
            get_unix_ts(), LastConfiguration.model_validate(config.model_dump())
        )

        return True, "OK"

    async def get_ee_pose(self) -> sm.SE3:
        last_configuration = await self.get_configuration()
        q0 = await self.named_config_to_q(last_configuration)
        return self.robot.fkine(q0)

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
        qr = [0.0, 0.0, pi / 2, 0.0, pi / 2, 0.0]
        qf = self.robot.ikine_NR(pose, q0=qr)
        logger.debug(f"Final config: {qf.q}")
        if not qf.success:
            logger.error(f"IK failed: {qf.reason}")
            return False, qf.reason

        # validate the final configuration
        forward_kin_pose = self.robot.fkine(qf.q)
        logger.debug(
            f"Forward kinematics pose:\n{pf(forward_kin_pose.t)}\n{pf(forward_kin_pose.R)}"
        )
        if not self.validate_pose_close_enough(pose, forward_kin_pose):
            logger.error(
                f"FK failed: {forward_kin_pose.t} != {pose.t} or {forward_kin_pose.R} != {pose.R}"
            )
            return False, "FK failed"

        # publish the final configuration (this is what actually moves the robot)
        logger.debug("Publishing final configuration ...")
        config = LastConfiguration.model_validate(
            (await self.q_to_named_config(qf.q)).model_dump()
        )
        logger.debug(f"Final configuration:\n{pf(config)}")
        await self.publish_configuration(config)
        logger.debug("Published final configuration")

        # save the final configuration
        self.db_client.set(get_unix_ts(), config)
        logger.debug("Saved final configuration")

        return True, "OK"

    async def move_through_path(
        self,
        path: List[sm.SE3],
        trajectory: bool = False,
        trajectory_options: TrajectoryOptions | None = None,
    ) -> Tuple[bool, str]:
        """
        Move the robot through the given path.

        Args:
            path(list): The path to move through. List of spatialmath.SE3 target poses.
            trajectory(bool): Whether to move through the path as a trajectory or not.
            trajectory_options(TrajectoryOptions): The options for the trajectory.

        Returns:
            True, "OK" if the move was successful.
            False, <reason> if the move failed.
        """

        # get the current config
        logger.debug("Getting current config ...")
        time_a = time.time()
        current_config = await self.get_configuration()
        time_b = time.time()
        logger.info(f"get_configuration took {time_b - time_a} seconds")
        logger.debug(f"Current config:\n{pf(current_config)}")
        q0 = await self.named_config_to_q(current_config)
        logger.debug(f"Current config: {q0}")

        # get the final configurations via inverse kinematics
        qr = [0.0, 0.0, pi / 2, 0.0, pi / 2, 0.0]

        # if not trajectory, just publish the final configurations
        if not trajectory:
            time_a = time.time()
            qfs = await self.async_inverse_kinematics(path, q0)
            time_b = time.time()
            logger.info(
                f"Inverse kinematics took {time_b - time_a} seconds to compute."
            )

            time_a = time.time()
            await self.move_to_q0(qfs[0])
            time_b = time.time()
            logger.info(f"move_to_q0 took {time_b - time_a} seconds to compute.")

            logger.debug("Trajectory is False, publishing final configurations ...")
            time_a = time.time()
            async_task = asyncio.create_task(self.move_through_q_path(qfs))
            self.tasks.add(async_task)
            time_b = time.time()
            logger.info(
                f"move_through_q_path took {time_b - time_a} seconds to compute."
            )

            return True, "OK"

        # calucalate "filler" poses
        logger.debug("Trajectory is True, calculating filler poses ...")
        total_steps = trajectory_options.amount_of_steps
        steps_per_segment = total_steps // len(path)
        padded_path = []
        t0 = self.robot.fkine(q0)
        for i in range(len(path)):
            t1 = path[i]
            padded_path.append(t0)
            generated_poses = rtb.ctraj(t0, t1, steps_per_segment)
            for pose in generated_poses:
                padded_path.append(pose)
            t0 = t1

        # calculate qt by running inverse kinematics on the padded path
        logger.debug("Calculating qt ...")
        qt = []
        for t in padded_path:
            logger.debug(f"Running IK for target pose:\n{pf(t.t)}\n{pf(t.R)}")
            q = self.robot.ikine_LM(t, q0=qr)
            logger.debug(f"Final config: {q.q}")
            if not q.success:
                logger.error(f"IK failed: {q.reason}")
                return False, q.reason
            qt.append(q.q)
            q0 = q.q

        async_task = asyncio.create_task(self.move_through_q_path(qt))
        async_task.add_done_callback(
            lambda t: logger.debug(f"task is done: {t}") or self.tasks.remove(t)
        )
        self.tasks.add(async_task)

        return True, "OK"

    async def async_inverse_kinematics(
        self, path: List[sm.SE3], q0: np.ndarray
    ) -> List[np.ndarray]:
        hashed_path = self.path_to_hash(path)
        cached_qt = self.db_client.get_inv_kin_cache(hashed_path)
        if cached_qt is not None:
            logger.info(f"Using cached inverse kinematics for path: {hashed_path}")
            return cached_qt
        logger.info(f"Calculating inverse kinematics for path: {hashed_path}")

        async def async_pose_generator():
            for pose in path:
                yield pose

        async def background_process(pose: sm.SE3, q0: np.ndarray = q0):
            logger.debug("Running IK ...")
            logger.debug(f"Target pose:\n{pf(pose.t)}\n{pf(pose.R)}")
            qf = self.robot.ikine_GN(pose, q0=q0)
            logger.debug(f"Final config: {qf.q}")
            qfs.append(qf.q)
            q0 = qf.q
            if not qf.success:
                logger.error(f"IK failed: {qf.reason}")
                return []

        _tasks: Set[asyncio.Task] = set()
        qfs = []
        logger.debug("Running async inverse kinematics ...")
        async for pose in async_pose_generator():
            async_task = asyncio.create_task(background_process(pose=pose))
            _tasks.add(async_task)
        logger.debug("Waiting for all IK tasks to finish ...")
        while len(qfs) < len(path):
            logger.debug(f"inv kin count: [ {len(qfs)} ]")
            await asyncio.sleep(0.1)
        logger.debug("All IK tasks finished")

        # save to cache
        self.db_client.save_inv_kin_cache(hashed_path, qfs)

        return qfs

    async def move_to_q0(self, q0: np.ndarray) -> Tuple[bool, str]:
        """
        Move the robot to the given configuration.

        Args:
            q0(np.ndarray): The configuration to move to.

        Returns:
            True, "OK" if the move was successful.
            False, <reason> if the move failed.
        """

        # get the current config
        logger.debug("Getting current config ...")
        current_config = await self.get_configuration()
        logger.debug(f"Current config:\n{pf(current_config)}")
        q0_current = await self.named_config_to_q(current_config)
        logger.debug(f"Current config: {q0_current}")

        # poses
        t0 = self.robot.fkine(q0_current)
        t1 = self.robot.fkine(q0)
        distance = np.linalg.norm(t1.t - t0.t)
        if distance < 0.01:
            logger.debug(f"distance: {distance}")
            return True, "OK"
        logger.debug(f"distance: {distance}")
        number_of_steps = int(distance * 100)

        # generate trajectory
        logger.debug("Generating trajectory ...")
        path = rtb.ctraj(t0, t1, number_of_steps)
        # logger.debug(f"path: {path}")
        logger.debug("trajectory generated")

        # move through trajectory
        logger.debug("Moving through trajectory ...")
        qt = []
        for t in path:
            logger.debug(f"Running IK for target pose:\n{pf(t.t)}\n{pf(t.R)}")
            q = self.robot.ikine_LM(t, q0=q0_current)
            logger.debug(f"Final config: {q.q}")
            if not q.success:
                logger.error(f"IK failed: {q.reason}")
                return False, q.reason
            qt.append(q.q)
            q0_current = q.q

        await self.move_through_q_path(qt)

        last_configuration = LastConfiguration.model_validate(
            (await self.q_to_named_config(q0)).model_dump()
        )
        self.db_client.set(get_unix_ts(), last_configuration)

        return True, "OK"

    async def move_to_trajectory_single_target(self, pose: sm.SE3) -> Tuple[bool, str]:
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
        qr = [0.0, 0.0, pi / 2, 0.0, pi / 2, 0.0]
        qf = self.robot.ikine_LM(pose, q0=qr)
        logger.debug(f"Final config: {qf.q}")
        if not qf.success:
            logger.error(f"IK failed: {qf.reason}")
            return False, qf.reason

        # validate the final configuration
        forward_kin_pose = self.robot.fkine(qf.q)
        logger.debug(
            f"Forward kinematics pose:\n{pf(forward_kin_pose.t)}\n{pf(forward_kin_pose.R)}"
        )
        if not self.validate_pose_close_enough(pose, forward_kin_pose):
            logger.error(
                f"FK failed: {forward_kin_pose.t} != {pose.t} or {forward_kin_pose.R} != {pose.R}"
            )
            return False, "FK failed"

        # get qt - list of lists of joint angles
        qt = rtb.jtraj(q0, qf.q, 50)

        # publish the final configuration (this is what actually moves the robot)
        async_task = asyncio.create_task(self.move_through_q_path(qt.q))
        self.tasks.add(async_task)

        return True, "OK"

    async def move_through_q_path(self, qt: List[List[np.ndarray]]) -> None:
        # publish the final configuration (this is what actually moves the robot)
        for q in qt:
            logger.debug("Publishing configuration ...")
            logger.debug(f"q: {q}")
            named_config = await self.q_to_named_config(q)
            logger.debug(f"named_config:\n{pf(named_config)}")
            config = LastConfiguration.model_validate(named_config.model_dump())
            logger.debug(f"configuration:\n{pf(config)}")
            await self.publish_configuration(config)
            logger.debug("Published configuration")
            # await asyncio.sleep(0.1)

        # save the final configuration
        named_config = await self.q_to_named_config(qt[-1])
        last_configuration = LastConfiguration.model_validate(named_config.model_dump())
        self.db_client.set(get_unix_ts(), last_configuration)
        logger.debug("Saved final configuration")

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
        return np.array(
            [
                config.base,
                config.shoulder,
                config.elbow,
                config.wrist0,
                config.wrist1,
                config.wrist2,
            ]
        )

    async def publish_configuration(self, configuration: NamedConfiguration) -> None:
        """
        IMPORTANT: This is what moves "actually" moves the robot.
        """

        async def async_generator():
            for k, v in configuration.model_dump().items():
                yield k, degrees(v)

        time_a = time.time()
        async for k, v in async_generator():
            await self.mqtt_client.publish(f"robot/{k}/position", v)
        time_b = time.time()
        logger.debug(f"publish_configuration took {time_b - time_a} seconds")

    def validate_pose_close_enough(
        self, target_pose: sm.SE3, current_pose: sm.SE3
    ) -> bool:
        """
        Validate that the current pose is close enough to the target pose.
        """
        return np.allclose(target_pose.t, current_pose.t, atol=0.01) and np.allclose(
            target_pose.R, current_pose.R, atol=0.01
        )

    def path_to_hash(self, path: List[sm.SE3]) -> str:
        hasher = hashlib.sha256()
        for se3 in path:
            # Serialize the SE3 object to a byte stream
            serialized_se3 = pickle.dumps(se3)
            # Update the hasher with the serialized SE3 object
            hasher.update(serialized_se3)
        # Return the hexadecimal representation of the hash
        return hasher.hexdigest()
