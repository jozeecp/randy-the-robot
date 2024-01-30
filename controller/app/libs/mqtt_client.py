import asyncio
import json
from aiomqtt import Client, exceptions as error
import ssl
import logging
from random import randint
from libs.utils import get_logger, custom_pformat as pf
from typing import Any, Dict, AsyncGenerator, Callable, Set
from models.mqtt import Msg

logger = get_logger(__name__)
logger.setLevel("INFO")


class MQTTClient:
    def __init__(self):
        self.client: Client | None = None
        self.tasks: Set[asyncio.Task] = set()

    async def start(self, logger: logging.Logger = logger):
        logger.info("Starting MQTT client ...")
        self.client = await self.build_client(log_level="INFO")
        logger.debug(f"Built client: {pf(self.client.__dict__)}")
        logger.info("Started MQTT client")

    async def build_client(self, log_level = "INFO") -> Client:
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        logger.info("Building MQTT client ...")
        try:
            client = Client(
                hostname="192.168.4.154",
                port=1883,
                username="robot_controller",
                password="robot_controller",
                logger=logger,
                # client_id=f"robot_controller-{randint(0, 1000)}",
                transport="tcp",
                # tls_context=ssl.create_default_context(),
            )
        except Exception as e:
            logger.error(f"Error building MQTT client: {e}")
            raise e
        logger.debug(f"Built client: {pf(client.__dict__)}")
        logger.info("Built MQTT client")
        return client

    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0) -> None:
        """
        Publish message to topic

        Args:
            topic (str): topic to publish to
            payload (dict): message payload
            qos (int, optional): Quality of service. Defaults to 0.
        """
        if not self.client:
            logger.error("Event client not initialized")
            raise Exception("Event client not initialized")
        logger.debug(f"With topic [{topic}], publishing payload:\n{pf(payload)}")
        async with self.client as client:  # type: ignore
            try:
                await client.publish(topic=topic, payload=json.dumps(payload), qos=qos)
            except error.MqttError as e:
                logger.error(f"Error publishing message: {e}")
                raise e

    async def event_stream(
        self, client: Client, topic: str
    ) -> AsyncGenerator[Msg, None]:
        """
        Event stream generator

        Args:
            client (Client): mqtt client

        Yields:
            AsyncGenerator[MQTTEvent, None]: event stream generator
        """
        while True:
            try:
                async with client.messages(queue_maxsize=1000) as messages:
                    async for message in messages:
                        logger.debug(f"Received message: {pf(message)}")
                        yield Msg(topic=message.topic.value, payload=json.loads(message.payload))
            except error.MqttError as e:
                logger.error(f"Error receiving message: {e}")
                raise e

    async def subscribe(
        self, topic: str, async_handler: Callable, logger: logging.Logger
    ) -> None:
        """
        Subscribe to a topic and call handler when a message is received

        Args:
            topic (str): topic to subscribe to
            async_handler (Callable): async handler to call when message is received.
        """
        if not self.client:
            logger.error("Event client not initialized")
            return
        logger.info(f"Subscribing to topic: {topic}")
        new_client = await self.build_client()
        logger.debug(f"built new client: {pf(new_client.__dict__)}")
        await new_client.__aenter__()
        logger.debug(f"entered new client: {pf(new_client.__dict__)}")
        await new_client.subscribe(topic, qos=2)
        logger.debug(f"Subscribed to topic: {topic}")

        async def task_wrapper():
            logger.debug(f"Starting handler task for topic: {topic}")
            async for event in self.event_stream(new_client, topic):
                logger.debug(f"Received event: {pf(event)}")
                try:
                    if not event:
                        raise Exception("Event is None")
                    handler_task = asyncio.create_task(
                        async_handler(event), name=f"handler_task_{topic}_event_{event.topic}"
                    )
                    await handler_task.add_done_callback(
                        lambda t: logger.debug(f"Task done: {t}")
                    )
                    self.tasks.add(handler_task)
                except TypeError:
                    pass
                except Exception as e:
                    logger.error(f"Error handling event: {e}")

        logger.debug(f"Creating handler task for topic: {topic} ...")
        task = asyncio.create_task(task_wrapper(), name=f"handler_task_{topic}")
        logger.debug(f"Created handler task for topic: {topic}")
        task.add_done_callback(self.done_callback)
        self.tasks.add(task)

    def done_callback(self, task: asyncio.Task) -> None:
        """
        Remove task from tasks set when done

        Args:
            task (asyncio.Task): task to remove
        """
        logger.debug(f"Task done: {task}")
        self.tasks.remove(task)