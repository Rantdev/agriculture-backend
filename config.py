"""
Backend Configuration - Environment-based settings
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # API
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Database Configuration
ORACLE_CONFIG = {
    'user': os.getenv('ORACLE_USER', 'your_username'),
    'password': os.getenv('ORACLE_PASSWORD', 'your_password'),
    'dsn': os.getenv('ORACLE_DSN', 'localhost:1521/XE'),
    'min': int(os.getenv('ORACLE_POOL_MIN', 1)),
    'max': int(os.getenv('ORACLE_POOL_MAX', 10)),
    'increment': int(os.getenv('ORACLE_POOL_INCREMENT', 1)),
    'timeout': int(os.getenv('ORACLE_TIMEOUT', 30))
}

# ML Models Configuration
MODELS_CONFIG = {
    'suitability_model': 'models/suitability_pipeline.joblib',
    'yield_model': 'models/yield_pipeline.joblib',
    'metadata': 'models/metadata.json',
    'enable_cache': os.getenv('ENABLE_MODEL_CACHE', 'true').lower() == 'true'
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.getenv('LOG_FILE', 'logs/backend.log')
}

# Sentry Configuration (Error Tracking)
SENTRY_DSN = os.getenv('SENTRY_DSN', None)

# Feature Flags
FEATURES = {
    'oracle_database': os.getenv('ENABLE_ORACLE', 'true').lower() == 'true',
    'cache_results': os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
    'async_processing': os.getenv('ENABLE_ASYNC', 'false').lower() == 'true',
}

# Get configuration based on environment
def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    return DevelopmentConfig()
