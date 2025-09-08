from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env/.storage.env",
        env_prefix="REDIS_",
        case_sensitive=False,
        env_file_encoding="utf-8", 
        extra="ignore"
    )
    
    # Basic Connection
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: Optional[SecretStr] = Field(default=None, description="Redis password")
    db: int = Field(default=0, ge=0, description="Redis database number")
    username: Optional[str] = Field(default=None, description="Redis username")
    
    # SSL Configuration
    ssl: bool = Field(default=False, description="Enable SSL connection")
    ssl_cert_reqs: str = Field(default="required", description="SSL certificate requirements")
    
    # Connection Pool
    max_connections: int = Field(default=50, description="Maximum connections in pool")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(default=5, description="Socket connect timeout in seconds")
    
    # Cluster Configuration
    cluster_enabled: bool = Field(default=False, description="Enable Redis cluster mode")
    cluster_nodes: List[str] = Field(default_factory=lambda: ["localhost:7000", "localhost:7001", "localhost:7002"], description="Redis cluster nodes")
    cluster_skip_full_coverage_check: bool = Field(default=False, description="Skip full coverage check for cluster")
    
    # Sentinel Configuration
    sentinel_enabled: bool = Field(default=False, description="Enable Redis Sentinel")
    sentinel_hosts: List[str] = Field(default_factory=lambda: ["localhost:26379"], description="Redis Sentinel hosts")
    sentinel_service_name: str = Field(default="mymaster", description="Sentinel service name")
    sentinel_password: Optional[SecretStr] = Field(default=None, description="Sentinel password")
    
    @property
    def connection_url(self) -> str:
        """Generate Redis connection URL."""
        scheme = "rediss" if self.ssl else "redis"
        auth = ""
        
        if self.username and self.password:
            auth = f"{self.username}:{self.password.get_secret_value()}@"
        elif self.password:
            auth = f":{self.password.get_secret_value()}@"
        
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"
    
    @property
    def connection_kwargs(self) -> dict:
        """Get connection parameters as kwargs."""
        kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "max_connections": self.max_connections,
        }
        
        if self.password:
            kwargs["password"] = self.password.get_secret_value()
        if self.username:
            kwargs["username"] = self.username
        if self.ssl:
            kwargs["ssl"] = True
            kwargs["ssl_cert_reqs"] = self.ssl_cert_reqs
            
        return kwargs