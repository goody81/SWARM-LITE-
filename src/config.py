from typing import Dict, Any
import os

class Config:
    """System configuration with environment variable support"""
    DEFAULTS = {
        'AGENT_HEARTBEAT_INTERVAL': 5,  # seconds
        'MAX_TASK_QUEUE_SIZE': 100,
        'MAX_MESSAGE_QUEUE_SIZE': 1000,
        'METRIC_UPDATE_INTERVAL': 1,  # seconds
        'DEFAULT_TASK_TIMEOUT': 300,  # seconds
        'MAX_RETRY_ATTEMPTS': 3,
    }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get config value with environment override support"""
        env_key = f"SWARM_LITE_{key}"
        return os.getenv(env_key, cls.DEFAULTS.get(key, default))
