import os
from unittest.mock import patch
import pytest
from pydantic import ValidationError
from app.dependencies import get_settings
from app.config import (
    AuthSettings,
    DocumentSettings,
    EmbeddingSettings,
    EnvironmentSettings,
    LLMSettings,
    LoggingSettings,
    RedisSettings,
    Settings,
    VectorSettings
)


class TestEnvironmentSettings:
    """Test environment configuration."""
    
    def test_default_values(self):
        """Test default environment values."""
        settings = EnvironmentSettings()
        
        assert settings.environment == "development"
        assert settings.debug is True
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
    
    def test_is_development(self):
        """Test development environment detection."""
        settings = EnvironmentSettings(environment="development")
        assert settings.is_development is True
        assert settings.is_production is False
    
    def test_is_production(self):
        """Test production environment detection."""
        settings = EnvironmentSettings(environment="production")
        assert settings.is_production is True
        assert settings.is_development is False
    
    def test_server_config(self):
        """Test server configuration generation."""
        settings = EnvironmentSettings(
            api_host="127.0.0.1",
            api_port=9000,
            environment="development"
        )
        
        config = settings.server_config
        assert config["host"] == "127.0.0.1"
        assert config["port"] == 9000
        assert config["reload"] is True
        assert config["debug"] is True


class TestDocumentSettings:
    """Test document configuration."""
    
    def test_default_values(self):
        """Test default document values."""
        settings = DocumentSettings()
        
        assert settings.max_file_size_mb == 50
        assert settings.chunk_size == 1000
        assert settings.chunk_overlap == 200
        assert ".pdf" in settings.allowed_file_types
    
    def test_allowed_extensions_set(self):
        """Test allowed extensions as set."""
        settings = DocumentSettings()
        extensions = settings.allowed_extensions_set
        
        assert isinstance(extensions, set)
        assert ".pdf" in extensions
        assert ".txt" in extensions
    
    def test_max_file_size_bytes(self):
        """Test file size conversion to bytes."""
        settings = DocumentSettings(max_file_size_mb=10)
        
        assert settings.max_file_size_bytes == 10 * 1024 * 1024


class TestLLMSettings:
    """Test LLM configuration."""
    
    def test_default_values(self):
        """Test default LLM values."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = LLMSettings()
            
            assert settings.chat_model == "gpt-4o-mini"
            assert settings.chat_temperature == 0.7
            assert settings.chat_max_tokens == 1000
    
    def test_model_presets(self):
        """Test model presets."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = LLMSettings()
            presets = settings.model_presets
            
            assert "fast" in presets
            assert "quality" in presets
            assert presets["fast"] == "gpt-4o-mini"
    
    def test_get_chat_params(self):
        """Test chat parameter generation."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = LLMSettings(
                chat_model="gpt-4",
                chat_temperature=0.5
            )
            
            params = settings.get_chat_params()
            assert params["model"] == "gpt-4"
            assert params["temperature"] == 0.5
            assert "max_tokens" in params


class TestEmbeddingSettings:
    """Test embedding configuration."""
    
    def test_default_values(self):
        """Test default embedding values."""
        settings = EmbeddingSettings()
        
        assert settings.embedding_model == "text-embedding-3-small"
        assert settings.embedding_dimensions == 1536
        assert settings.embedding_batch_size == 100
    
    def test_model_configs(self):
        """Test embedding model configurations."""
        settings = EmbeddingSettings()
        configs = settings.model_configs
        
        assert "text-embedding-3-small" in configs
        assert "dimensions" in configs["text-embedding-3-small"]
    
    def test_get_model_info(self):
        """Test model info retrieval."""
        settings = EmbeddingSettings()
        info = settings.get_model_info("text-embedding-3-small")
        
        assert "dimensions" in info
        assert info["dimensions"] == 1536
    
    def test_current_model_dimensions(self):
        """Test current model dimensions."""
        settings = EmbeddingSettings(embedding_model="text-embedding-3-small")
        
        assert settings.current_model_dimensions == 1536


class TestVectorSettings:
    """Test vector database configuration."""
    
    def test_default_values(self):
        """Test default vector values."""
        settings = VectorSettings()
        
        assert settings.vector_db_type == "chroma"
        assert settings.chroma_collection_name == "documents"
        assert settings.default_search_results == 5
    
    def test_chroma_settings(self):
        """Test Chroma configuration generation."""
        settings = VectorSettings()
        config = settings.chroma_settings
        
        assert "persist_directory" in config
        assert "collection_name" in config
        assert config["collection_name"] == "documents"
    
    def test_search_config(self):
        """Test search configuration generation."""
        settings = VectorSettings()
        config = settings.search_config
        
        assert "default_results" in config
        assert "semantic_weight" in config
        assert config["default_results"] == 5
    
    def test_search_weights_validation(self):
        """Test search weights validation."""
        # Valid weights should work
        settings = VectorSettings(
            semantic_search_weight=0.6,
            keyword_search_weight=0.4
        )
        assert settings.semantic_search_weight == 0.6
        assert settings.keyword_search_weight == 0.4
        
        # Invalid weights should raise error during validation
        with pytest.raises(ValidationError):
            VectorSettings(
                semantic_search_weight=0.8,
                keyword_search_weight=0.5
            )


class TestRedisSettings:
    """Test Redis configuration."""
    
    def test_default_values(self):
        """Test default Redis values."""
        settings = RedisSettings()
        
        assert settings.host == "localhost"
        assert settings.port == 6379
        assert settings.db == 0
    
    def test_connection_url_no_auth(self):
        """Test connection URL without authentication."""
        settings = RedisSettings()
        url = settings.connection_url
        
        assert url.startswith("redis://")
        assert "localhost:6379" in url
    
    def test_connection_url_with_password(self):
        """Test connection URL with password."""
        from pydantic import SecretStr
        
        settings = RedisSettings(password=SecretStr("secret123"))
        url = settings.connection_url
        
        assert ":secret123@" in url
    
    def test_connection_kwargs(self):
        """Test connection kwargs generation."""
        settings = RedisSettings(
            host="redis.example.com",
            port=6380,
            max_connections=100
        )
        
        kwargs = settings.connection_kwargs
        assert kwargs["host"] == "redis.example.com"
        assert kwargs["port"] == 6380
        assert kwargs["max_connections"] == 100


class TestAuthSettings:
    """Test authentication configuration."""
    
    def test_default_values(self):
        """Test default auth values."""
        settings = AuthSettings()
        
        assert settings.api_key_required is False
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_expiration_hours == 24
    
    def test_jwt_config(self):
        """Test JWT configuration generation."""
        from pydantic import SecretStr
        
        settings = AuthSettings(jwt_secret_key=SecretStr("secret"))
        config = settings.jwt_config
        
        assert config["secret_key"] == "secret"
        assert config["algorithm"] == "HS256"
    
    def test_is_valid_api_key(self):
        """Test API key validation."""
        settings = AuthSettings(
            api_key_required=True,
            api_keys=["key1", "key2"]
        )
        
        assert settings.is_valid_api_key("key1") is True
        assert settings.is_valid_api_key("invalid") is False
        
        # Should return True if not required
        settings.api_key_required = False
        assert settings.is_valid_api_key("anything") is True


class TestLoggingSettings:
    """Test logging configuration."""
    
    def test_default_values(self):
        """Test default logging values."""
        settings = LoggingSettings()
        
        assert settings.level == "INFO"
        assert settings.format == "json"
        assert settings.console_enabled is True
    
    def test_loguru_format_templates(self):
        """Test Loguru format templates."""
        settings = LoggingSettings()
        templates = settings.loguru_format_templates
        
        assert "text" in templates
        assert "json" in templates
        assert "detailed" in templates
    
    def test_get_loguru_config(self):
        """Test Loguru configuration generation."""
        settings = LoggingSettings()
        config = settings.get_loguru_config()
        
        assert isinstance(config, list)
        assert len(config) > 0
        
        # Should have console handler
        console_handler = next((h for h in config if h["sink"] == "sys.stdout"), None)
        assert console_handler is not None


class TestMasterSettings:
    """Test the composed Settings class."""
    
    def test_settings_composition(self):
        """Test that all sub-settings are properly composed."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            # All sections should be available
            assert hasattr(settings, 'environment')
            assert hasattr(settings, 'auth')
            assert hasattr(settings, 'documents')
            assert hasattr(settings, 'embeddings')
            assert hasattr(settings, 'vectors')
            assert hasattr(settings, 'llm')
            assert hasattr(settings, 'redis')
            assert hasattr(settings, 'logging')
            
            # Should be correct types
            assert isinstance(settings.environment, EnvironmentSettings)
            assert isinstance(settings.auth, AuthSettings)
            assert isinstance(settings.documents, DocumentSettings)
            assert isinstance(settings.embeddings, EmbeddingSettings)
            assert isinstance(settings.vectors, VectorSettings)
            assert isinstance(settings.llm, LLMSettings)
            assert isinstance(settings.redis, RedisSettings)
            assert isinstance(settings.logging, LoggingSettings)
    
    def test_settings_access(self):
        """Test accessing settings through the composed interface."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            # Should be able to access nested settings
            assert settings.llm.chat_model == "gpt-4o-mini"
            assert settings.vectors.vector_db_type == "chroma"
            assert settings.environment.environment == "development"
    
    def test_get_settings_caching(self):
        """Test that get_settings() returns cached instance."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Clear the cache first
            get_settings.cache_clear()
            
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Should be the same instance
            assert settings1 is settings2
    
    def test_model_dump(self):
        """Test configuration export."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            config = settings.model_dump()
            
            # Should have all sections
            assert "environment" in config
            assert "auth" in config
            assert "documents" in config
            assert "embeddings" in config
            assert "vectors" in config
            assert "llm" in config
            assert "redis" in config
            assert "logging" in config
    
    def test_settings_isolation(self):
        """Test that each settings section loads from its own env file."""
        # This test would be more meaningful with actual env files,
        # but we can at least verify the structure
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            # Each section should have its own configuration
            assert settings.llm.chat_model  # From LLM config
            assert settings.vectors.vector_db_type  # From vector config
            assert settings.auth.jwt_algorithm  # From auth config


class TestEnvFileIntegration:
    """Test integration with actual env files."""
    
    def test_env_file_loading(self):
        """Test that env file paths are properly configured."""
        # Check that each settings class has env_file configured in their model_config
        # For Pydantic Settings, the env_file is stored in the SettingsConfigDict
        
        # Check LLMSettings
        assert hasattr(LLMSettings, 'model_config')
        llm_config = LLMSettings.model_config
        assert 'env_file' in llm_config
        assert '.llm.env' in str(llm_config['env_file'])
        
        # Check VectorSettings
        assert hasattr(VectorSettings, 'model_config')
        vector_config = VectorSettings.model_config
        assert 'env_file' in vector_config
        assert '.vectors.env' in str(vector_config['env_file'])
        
        # Check AuthSettings
        assert hasattr(AuthSettings, 'model_config')
        auth_config = AuthSettings.model_config
        assert 'env_file' in auth_config
        assert '.auth.env' in str(auth_config['env_file'])
    
    def test_missing_env_files(self):
        """Test behavior when env files don't exist."""
        # Should fall back to defaults when env files are missing
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            # Should use default values
            assert settings.llm.chat_model == "gpt-4o-mini"
            assert settings.vectors.vector_db_type == "chroma"