import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError

from app.config import (
    AuthSettings,
    DocumentSettings,
    EmbeddingSettings,
    EnvironmentSettings,
    LLMSettings,
    LoggingSettings,
    RedisSettings,
    Settings,
    VectorSettings,
    EnvFileManager,
    SettingsValidator,
)



class TestEnvFileManager:
    """Test environment file management logic."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_dir = self.temp_dir / ".env"
        self.env_dir.mkdir()
        
        # Create some test env files
        (self.env_dir / ".core.env").touch()
        (self.env_dir / ".llm.env").touch()
        (self.env_dir / ".dev.env").touch()
        
        self.manager = EnvFileManager(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_base_files(self):
        """Test base file discovery."""
        files = self.manager.get_base_files()
        
        # Should find existing files
        assert any(".core.env" in f for f in files)
        assert any(".llm.env" in f for f in files)
        
        # Should not include non-existent files
        assert not any(".nonexistent.env" in f for f in files)
    
    def test_get_environment_files_development(self):
        """Test development environment file discovery."""
        files = self.manager.get_environment_files("development")
        
        # Should include .dev.env
        assert any(".dev.env" in f for f in files)
    
    def test_get_environment_files_production(self):
        """Test production environment file discovery."""
        # Create production file
        (self.env_dir / ".production.env").touch()
        
        files = self.manager.get_environment_files("production")
        
        # Should include .production.env
        assert any(".production.env" in f for f in files)
    
    def test_get_local_overrides(self):
        """Test local override file discovery."""
        # Create local override file
        (self.env_dir / ".local.env").touch()
        
        files = self.manager.get_local_overrides()
        
        assert any(".local.env" in f for f in files)
    
    def test_get_all_env_files(self):
        """Test complete environment file discovery."""
        # Create additional files
        (self.env_dir / ".local.env").touch()
        
        files = self.manager.get_all_env_files("development")
        
        # Should include base files
        assert any(".core.env" in f for f in files)
        assert any(".llm.env" in f for f in files)
        
        # Should include environment-specific files
        assert any(".dev.env" in f for f in files)
        
        # Should include local overrides
        assert any(".local.env" in f for f in files)


class TestSettingsValidator:
    """Test configuration validation logic."""
    
    def setup_method(self):
        """Setup test validator."""
        # Create mock settings
        self.mock_settings = MagicMock()
        self.mock_settings.environment.is_development = True
        self.mock_settings.environment.is_production = False
        self.validator = SettingsValidator(self.mock_settings)
    
    def test_validate_api_keys_success(self):
        """Test successful API key validation."""
        # Mock valid API key
        self.mock_settings.llm.openai_api_key.get_secret_value.return_value = "valid-key"
        
        # Should not raise
        self.validator.validate_api_keys()
    
    def test_validate_api_keys_empty(self):
        """Test API key validation with empty key."""
        # Mock empty API key
        self.mock_settings.llm.openai_api_key.get_secret_value.return_value = ""
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            self.validator.validate_api_keys()
    
    def test_validate_api_keys_whitespace(self):
        """Test API key validation with whitespace-only key."""
        # Mock whitespace-only API key
        self.mock_settings.llm.openai_api_key.get_secret_value.return_value = "   "
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            self.validator.validate_api_keys()
    
    def test_validate_production_security_dev_env(self):
        """Test production security validation in development."""
        # Should pass in development regardless of JWT secret
        self.mock_settings.auth.jwt_secret_key.get_secret_value.return_value = "your_jwt_secret_here"
        
        # Should not raise
        self.validator.validate_production_security()
    
    def test_validate_production_security_prod_env(self):
        """Test production security validation in production."""
        self.mock_settings.environment.is_production = True
        self.mock_settings.environment.is_development = False
        
        # Mock insecure JWT secret
        self.mock_settings.auth.jwt_secret_key.get_secret_value.return_value = "your_jwt_secret_here"
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="JWT secret key must be changed"):
            self.validator.validate_production_security()
    
    def test_validate_model_compatibility_success(self):
        """Test successful model compatibility validation."""
        self.mock_settings.embeddings.current_model_dimensions = 1536
        
        # Should not raise
        self.validator.validate_model_compatibility()
    
    def test_validate_model_compatibility_failure(self):
        """Test model compatibility validation failure."""
        self.mock_settings.embeddings.current_model_dimensions = -1
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid embedding dimensions"):
            self.validator.validate_model_compatibility()




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
    
    def test_upload_dir_creation(self):
        """Test upload directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = Path(temp_dir) / "uploads"
            settings = DocumentSettings(upload_dir=upload_path)
            
            assert upload_path.exists()




class TestLLMSettings:
    """Test LLM configuration."""
    
    def test_default_values(self):
        """Test default LLM values."""
        settings = LLMSettings(openai_api_key="test-key")
        
        assert settings.chat_model == "gpt-4o-mini"
        assert settings.chat_temperature == 0.7
        assert settings.chat_max_tokens == 1000
    
    def test_model_presets(self):
        """Test model presets."""
        settings = LLMSettings(openai_api_key="test-key")
        presets = settings.model_presets
        
        assert "fast" in presets
        assert "quality" in presets
        assert presets["fast"] == "gpt-4o-mini"
    
    def test_get_chat_params(self):
        """Test chat parameter generation."""
        settings = LLMSettings(
            openai_api_key="test-key",
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
    
    def test_search_weights_validation(self):
        """Test search weights sum to 1.0."""
        # Valid weights
        settings = VectorSettings(
            semantic_search_weight=0.6,
            keyword_search_weight=0.4
        )
        assert abs((settings.semantic_search_weight + settings.keyword_search_weight) - 1.0) < 0.001
        
        # Invalid weights should raise error
        with pytest.raises(ValueError, match="must sum to 1.0"):
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
    """Test master Settings class."""
    
    def test_settings_initialization(self):
        """Test all sub-settings are initialized."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            assert isinstance(settings.environment, EnvironmentSettings)
            assert isinstance(settings.auth, AuthSettings)
            assert isinstance(settings.documents, DocumentSettings)
            assert isinstance(settings.embeddings, EmbeddingSettings)
            assert isinstance(settings.vectors, VectorSettings)
            assert isinstance(settings.llm, LLMSettings)
            assert isinstance(settings.redis, RedisSettings)
            assert isinstance(settings.logging, LoggingSettings)
    
    def test_model_dump_config(self):
        """Test configuration export."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            config = settings.model_dump_config()
            
            assert "environment" in config
            assert "auth" in config
            assert "documents" in config
            
            # Sensitive data should be excluded
            assert "openai_api_key" not in str(config)
            assert "jwt_secret_key" not in str(config)
    
    def test_get_loaded_env_files(self):
        """Test loaded env files listing."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            files = settings.get_loaded_env_files()
            
            assert isinstance(files, list)
    
    def test_cache_settings(self):
        """Test cache configuration."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            cache_config = settings.cache_settings
            
            assert "backend" in cache_config
            assert "key_prefix" in cache_config
            assert "default_ttl" in cache_config
    
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            # Should pass with valid OpenAI key
            assert settings.validate_configuration() is True
    
    def test_reload_settings(self):
        """Test settings reload functionality."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            
            # Should not raise
            settings.reload_settings()
            
            # Settings should still be valid
            assert isinstance(settings.environment, EnvironmentSettings)

