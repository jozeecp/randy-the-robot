import json
import os
from typing import Any

import redis
from pydantic import BaseModel

from libs.utils import get_logger

logger = get_logger(__name__)
logger.setLevel("INFO")


class DBClient:
    def __init__(self) -> None:
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = os.getenv("REDIS_PORT", 6379)
        logger.debug(f"redis_host: {self.redis_host}")
        logger.debug(f"redis_port: {self.redis_port}")

    def get_client(self, db: int = 0):
        return redis.Redis(host=self.redis_host, port=self.redis_port, db=db)

    def get_latest(self, parse_type: Any) -> BaseModel:
        if not parse_type.__redis_db__:
            raise Exception("parse_type must have __redis_db__ attribute")
        keys = self.get_keys(parse_type)
        logger.debug(f"keys: {keys}")
        if len(keys) == 0:
            return None
        sorted_keys = sorted(
            keys
        )  # since these are timestamps, the first one is the oldest
        logger.debug(f"sorted_keys: {sorted_keys}")
        latest_key = sorted_keys[-1]
        logger.debug(f"latest_key: {latest_key}")
        return self.get(latest_key, parse_type)

    def get(self, key: str, parse_type: BaseModel) -> BaseModel:
        if not parse_type.__redis_db__:
            raise Exception("parse_type must have __redis_db__ attribute")
        db = parse_type.__redis_db__
        str_content = self.get_client(db).get(key)
        logger.debug(f"str_content: {str_content}")
        if str_content is None:
            logger.debug("str_content is None")
            return None
        data = json.loads(str_content)
        logger.debug(f"data: {data}")
        return parse_type.model_validate(data)

    def set(self, key: str, data: BaseModel):
        if not data.__redis_db__:
            raise Exception("data must have __redis_db__ attribute")
        db = data.__redis_db__
        value = json.dumps(data.model_dump())
        return self.get_client(db).set(key, value)

    def delete(self, key: str, parse_type: Any) -> None:
        if not parse_type.__redis_db__:
            raise Exception("parse_type must have __redis_db__ attribute")
        db = parse_type.__redis_db__
        return self.get_client(db).delete(key)

    def get_keys(self, parse_type: Any, pattern="*") -> list:
        if not parse_type.__redis_db__:
            raise Exception("parse_type must have __redis_db__ attribute")
        db = parse_type.__redis_db__
        return self.get_client(db).keys(pattern=pattern)
