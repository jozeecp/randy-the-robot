import asyncio
from engine import Engine
from libs.mqtt_client import MQTTClient
from fastapi import FastAPI
from aiomqtt import Client
from contextlib import asynccontextmanager
from libs.utils import get_logger
from libs.db_client import DBClient
from models.responses import RequestResponse, SimpleMsg
from models.spatial import RigidBodyPose
from typing import Set
import time

logger = get_logger(__name__)

app = FastAPI()
mqtt_client = MQTTClient()
db_client = DBClient()
engine = Engine(mqtt_client, db_client)

tasks: Set[asyncio.Task] = set()
mqtt_client_start_task = asyncio.create_task(mqtt_client.start())
tasks.add(mqtt_client_start_task)
engine_start_task = asyncio.create_task(engine.start())
tasks.add(engine_start_task)



@app.post(path="/move_to", response_model=RequestResponse)
async def move_to(pose: RigidBodyPose):
    success, reason = await engine.move_to(pose)
    return RequestResponse(success=success, message=reason)


@app.get("/", response_model=SimpleMsg)
async def index():
    return SimpleMsg(message="Hello, world!")


@app.get("/health", response_model=SimpleMsg)
async def health():
    return SimpleMsg(message="OK")
