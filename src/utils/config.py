"""Configuration management for SWARM-LITE-."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class SwarmConfig:
    """Main configuration for SWARM system."""
    # System settings
    system_name: str = "SWARM-LITE"
    environment: str = "development"
    debug: bool = False

    # Communication settings
    communication_timeout_seconds: float = 30.0
    message_queue_max_size: int = 1000
    message_ttl_seconds: int = 300
    heartbeat_interval_seconds: float = 10.0
    max_backpressure_size: int = 500

    # Agent settings
    agent_max_concurrent_tasks: int = 5
    agent_health_check_interval_seconds: float = 30.0
    agent_timeout_seconds: float = 300.0

    # Task settings
    task_default_timeout_seconds: float = 600.0
    task_max_retries: int = 3
    task_queue_max_size: int = 10000

    # Coordinator settings
    coordinator_scheduling_interval_seconds: float = 1.0
    coordinator_load_balancing_strategy: str = "least_loaded"
    coordinator_max_agents: int = 100

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    log_rotation_size_mb: int = 100
    log_retention_days: int = 7

    # Metrics settings
    metrics_enabled: bool = True
    metrics_collection_interval_seconds: float = 60.0
    metrics_retention_hours: int = 24

    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "SwarmConfig":
        """Load configuration from environment variables."""
        config = cls()

        # System settings
        config.system_name = os.getenv("SWARM_SYSTEM_NAME", config.system_name)
        config.environment = os.getenv("SWARM_ENVIRONMENT", config.environment)
        config.debug = os.getenv("SWARM_DEBUG", "false").lower() == "true"

        # Communication settings
        config.communication_timeout_seconds = float(
            os.getenv("SWARM_COMMUNICATION_TIMEOUT_SECONDS", str(config.communication_timeout_seconds))
        )
        config.message_queue_max_size = int(
            os.getenv("SWARM_MESSAGE_QUEUE_MAX_SIZE", str(config.message_queue_max_size))
        )
        config.message_ttl_seconds = int(
            os.getenv("SWARM_MESSAGE_TTL_SECONDS", str(config.message_ttl_seconds))
        )
        config.heartbeat_interval_seconds = float(
            os.getenv("SWARM_HEARTBEAT_INTERVAL_SECONDS", str(config.heartbeat_interval_seconds))
        )

        # Agent settings
        config.agent_max_concurrent_tasks = int(
            os.getenv("SWARM_AGENT_MAX_CONCURRENT_TASKS", str(config.agent_max_concurrent_tasks))
        )
        config.agent_health_check_interval_seconds = float(
            os.getenv("SWARM_AGENT_HEALTH_CHECK_INTERVAL_SECONDS", str(config.agent_health_check_interval_seconds))
        )

        # Task settings
        config.task_default_timeout_seconds = float(
            os.getenv("SWARM_TASK_DEFAULT_TIMEOUT_SECONDS", str(config.task_default_timeout_seconds))
        )
        config.task_max_retries = int(
            os.getenv("SWARM_TASK_MAX_RETRIES", str(config.task_max_retries))
        )

        # Logging settings
        config.log_level = os.getenv("SWARM_LOG_LEVEL", config.log_level)
        config.log_format = os.getenv("SWARM_LOG_FORMAT", config.log_format)
        config.log_file = os.getenv("SWARM_LOG_FILE")

        # Metrics settings
        config.metrics_enabled = os.getenv("SWARM_METRICS_ENABLED", "true").lower() == "true"
        config.metrics_collection_interval_seconds = float(
            os.getenv("SWARM_METRICS_COLLECTION_INTERVAL_SECONDS", str(config.metrics_collection_interval_seconds))
        )

        return config

    @classmethod
    def from_file(cls, path: str) -> "SwarmConfig":
        """Load configuration from JSON file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(config_path, "r") as f:
            data = json.load(f)

        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "system_name": self.system_name,
            "environment": self.environment,
            "debug": self.debug,
            "communication_timeout_seconds": self.communication_timeout_seconds,
            "message_queue_max_size": self.message_queue_max_size,
            "message_ttl_seconds": self.message_ttl_seconds,
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "max_backpressure_size": self.max_backpressure_size,
            "agent_max_concurrent_tasks": self.agent_max_concurrent_tasks,
            "agent_health_check_interval_seconds": self.agent_health_check_interval_seconds,
            "agent_timeout_seconds": self.agent_timeout_seconds,
            "task_default_timeout_seconds": self.task_default_timeout_seconds,
            "task_max_retries": self.task_max_retries,
            "task_queue_max_size": self.task_queue_max_size,
            "coordinator_scheduling_interval_seconds": self.coordinator_scheduling_interval_seconds,
            "coordinator_load_balancing_strategy": self.coordinator_load_balancing_strategy,
            "coordinator_max_agents": self.coordinator_max_agents,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_file": self.log_file,
            "log_rotation_size_mb": self.log_rotation_size_mb,
            "log_retention_days": self.log_retention_days,
            "metrics_enabled": self.metrics_enabled,
            "metrics_collection_interval_seconds": self.metrics_collection_interval_seconds,
            "metrics_retention_hours": self.metrics_retention_hours,
            "custom_settings": self.custom_settings,
        }

    def save_to_file(self, path: str) -> None:
        """Save configuration to JSON file."""
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []

        # Validate positive values
        if self.communication_timeout_seconds <= 0:
            errors.append("communication_timeout_seconds must be positive")
        if self.message_queue_max_size <= 0:
            errors.append("message_queue_max_size must be positive")
        if self.agent_max_concurrent_tasks <= 0:
            errors.append("agent_max_concurrent_tasks must be positive")
        if self.task_default_timeout_seconds <= 0:
            errors.append("task_default_timeout_seconds must be positive")

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of {valid_log_levels}")

        # Validate environment
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            errors.append(f"environment must be one of {valid_environments}")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        return True


# Global configuration instance
_config: Optional[SwarmConfig] = None


def get_config() -> SwarmConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = SwarmConfig.from_env()
    return _config


def set_config(config: SwarmConfig) -> None:
    """Set global configuration instance."""
    global _config
    config.validate()
    _config = config


def reset_config() -> None:
    """Reset global configuration instance."""
    global _config
    _config = None
