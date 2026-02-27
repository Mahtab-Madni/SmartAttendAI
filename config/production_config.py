"""
Production Configuration Loader
Handles environment variables and production settings
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ConfigLoader:
    """Load and validate configuration from environment variables"""
    
    @staticmethod
    def get_env(key: str, default: Any = None, required: bool = False, var_type: type = str) -> Any:
        """
        Get environment variable with type conversion and validation
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether this variable is required
            var_type: Type to convert the value to
        
        Returns:
            Converted value or default
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable '{key}' not found")
        
        if value is None:
            return default
        
        # Type conversion
        try:
            if var_type == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif var_type == int:
                return int(value)
            elif var_type == float:
                return float(value)
            elif var_type == list:
                return json.loads(value) if isinstance(value, str) else value
            elif var_type == dict:
                return json.loads(value) if isinstance(value, str) else value
            else:
                return var_type(value)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Warning: Could not convert {key}='{value}' to {var_type.__name__}: {e}")
            return default
    
    @staticmethod
    def validate_config():
        """Validate critical configuration settings"""
        errors = []
        
        # Check if we're in production
        env = ConfigLoader.get_env('ENVIRONMENT', 'development')
        if env == 'production':
            # In production, certain settings must be configured
            required_vars = [
                'JWT_SECRET_KEY',
                'ADMIN_PASSWORD',
                'DEFAULT_LATITUDE',
                'DEFAULT_LONGITUDE'
            ]
            
            for var in required_vars:
                if not ConfigLoader.get_env(var):
                    errors.append(f"Production environment requires {var} to be set")
        
        # Validate coordinates
        try:
            lat = ConfigLoader.get_env('DEFAULT_LATITUDE', var_type=float)
            lon = ConfigLoader.get_env('DEFAULT_LONGITUDE', var_type=float)
            
            if lat and (lat < -90 or lat > 90):
                errors.append("DEFAULT_LATITUDE must be between -90 and 90")
            
            if lon and (lon < -180 or lon > 180):
                errors.append("DEFAULT_LONGITUDE must be between -180 and 180")
        except ValueError:
            errors.append("DEFAULT_LATITUDE and DEFAULT_LONGITUDE must be valid numbers")
        
        if errors:
            print("Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

# Load production configuration
ENVIRONMENT = ConfigLoader.get_env('ENVIRONMENT', 'development')
DEBUG = ConfigLoader.get_env('DEBUG', True, var_type=bool)
LOG_LEVEL = ConfigLoader.get_env('LOG_LEVEL', 'INFO')

# Database Configuration
DATABASE_TYPE = ConfigLoader.get_env('DATABASE_TYPE', 'sqlite')
POSTGRES_CONFIG = {
    'host': ConfigLoader.get_env('POSTGRES_HOST', 'localhost'),
    'port': ConfigLoader.get_env('POSTGRES_PORT', 5432, var_type=int),
    'database': ConfigLoader.get_env('POSTGRES_DB', 'smartattendai'),
    'user': ConfigLoader.get_env('POSTGRES_USER', 'postgres'),
    'password': ConfigLoader.get_env('POSTGRES_PASSWORD', ''),
}

# Security Configuration
SECURITY_CONFIG = {
    'jwt_secret': ConfigLoader.get_env('JWT_SECRET_KEY', 'dev-secret-key'),
    'encryption_key': ConfigLoader.get_env('ENCRYPTION_KEY', 'dev-encryption-key'),
    'admin_password': ConfigLoader.get_env('ADMIN_PASSWORD', 'admin123'),
    'session_timeout': ConfigLoader.get_env('SESSION_TIMEOUT', 60, var_type=int),
}

# Enhanced API Configuration
ENHANCED_API_KEYS = {
    'TELEGRAM_BOT_TOKEN': ConfigLoader.get_env('TELEGRAM_BOT_TOKEN', ''),
    'TELEGRAM_CHAT_ID': ConfigLoader.get_env('TELEGRAM_CHAT_ID', ''),
    'TWILIO_ACCOUNT_SID': ConfigLoader.get_env('TWILIO_ACCOUNT_SID', ''),
    'TWILIO_AUTH_TOKEN': ConfigLoader.get_env('TWILIO_AUTH_TOKEN', ''),
    'TWILIO_PHONE_NUMBER': ConfigLoader.get_env('TWILIO_PHONE_NUMBER', ''),
}

# Enhanced Geofencing Configuration
ENHANCED_GEOFENCE_CONFIG = {
    'RADIUS_METERS': ConfigLoader.get_env('GEOFENCE_RADIUS', 100, var_type=int),
    'GPS_ACCURACY_THRESHOLD': ConfigLoader.get_env('GPS_ACCURACY_THRESHOLD', 50, var_type=int),
    'MOCK_LOCATION_DETECTION': ConfigLoader.get_env('MOCK_LOCATION_DETECTION', True, var_type=bool),
    'DEFAULT_LOCATION': {
        'lat': ConfigLoader.get_env('DEFAULT_LATITUDE', 40.7128, var_type=float),
        'lon': ConfigLoader.get_env('DEFAULT_LONGITUDE', -74.0060, var_type=float),
    },
    'CLASSROOM_LOCATIONS': {
        'Room_101': {
            'lat': ConfigLoader.get_env('ROOM_101_LAT', 40.7128, var_type=float),
            'lon': ConfigLoader.get_env('ROOM_101_LON', -74.0060, var_type=float),
        },
        'Room_102': {
            'lat': ConfigLoader.get_env('ROOM_102_LAT', 40.7138, var_type=float),
            'lon': ConfigLoader.get_env('ROOM_102_LON', -74.0050, var_type=float),
        },
        'Lab_A': {
            'lat': ConfigLoader.get_env('LAB_A_LAT', 40.7148, var_type=float),
            'lon': ConfigLoader.get_env('LAB_A_LON', -74.0040, var_type=float),
        },
    }
}

# Camera Configuration
CAMERA_CONFIG = {
    'DEFAULT_CAMERA_ID': ConfigLoader.get_env('DEFAULT_CAMERA_ID', 0, var_type=int),
    'CAMERA_WIDTH': ConfigLoader.get_env('CAMERA_WIDTH', 640, var_type=int),
    'CAMERA_HEIGHT': ConfigLoader.get_env('CAMERA_HEIGHT', 480, var_type=int),
    'CAMERA_FPS': ConfigLoader.get_env('CAMERA_FPS', 30, var_type=int),
    'MAX_UPLOAD_SIZE': ConfigLoader.get_env('MAX_UPLOAD_SIZE', 10, var_type=int),  # MB
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'ENABLED': ConfigLoader.get_env('MONITORING_ENABLED', True, var_type=bool),
    'SENTRY_DSN': ConfigLoader.get_env('SENTRY_DSN', ''),
    'METRICS_ENDPOINT': ConfigLoader.get_env('METRICS_ENDPOINT', ''),
    'LOG_FILE': ConfigLoader.get_env('LOG_FILE', 'logs/smartattendai.log'),
}

# Cloud Storage Configuration (Optional)
CLOUD_STORAGE_CONFIG = {
    'AWS': {
        'ACCESS_KEY_ID': ConfigLoader.get_env('AWS_ACCESS_KEY_ID', ''),
        'SECRET_ACCESS_KEY': ConfigLoader.get_env('AWS_SECRET_ACCESS_KEY', ''),
        'BUCKET_NAME': ConfigLoader.get_env('AWS_BUCKET_NAME', ''),
        'REGION': ConfigLoader.get_env('AWS_REGION', 'us-east-1'),
    },
    'GOOGLE_CLOUD': {
        'BUCKET_NAME': ConfigLoader.get_env('GOOGLE_CLOUD_STORAGE_BUCKET', ''),
        'CREDENTIALS_PATH': ConfigLoader.get_env('GOOGLE_APPLICATION_CREDENTIALS', ''),
    }
}

def get_production_config():
    """Get the complete production configuration"""
    
    # Validate configuration
    if not ConfigLoader.validate_config():
        if ENVIRONMENT == 'production':
            raise RuntimeError("Invalid configuration for production environment")
    
    config = {
        'environment': ENVIRONMENT,
        'debug': DEBUG,
        'log_level': LOG_LEVEL,
        'database_type': DATABASE_TYPE,
        'postgres': POSTGRES_CONFIG,
        'security': SECURITY_CONFIG,
        'api_keys': ENHANCED_API_KEYS,
        'geofence': ENHANCED_GEOFENCE_CONFIG,
        'camera': CAMERA_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'cloud_storage': CLOUD_STORAGE_CONFIG,
    }
    
    return config

# Print configuration status
def print_config_status():
    """Print configuration loading status"""
    print(f"Configuration loaded for environment: {ENVIRONMENT}")
    
    if DEBUG:
        print("Debug mode: ENABLED")
    else:
        print("Debug mode: DISABLED")
    
    # Check critical services
    notifications_configured = bool(ENHANCED_API_KEYS['TELEGRAM_BOT_TOKEN'] or 
                                   ENHANCED_API_KEYS['TWILIO_ACCOUNT_SID'])
    print(f"Notifications configured: {'YES' if notifications_configured else 'NO'}")
    
    monitoring_configured = bool(MONITORING_CONFIG['SENTRY_DSN'])
    print(f"Error monitoring configured: {'YES' if monitoring_configured else 'NO'}")
    
    if ENVIRONMENT == 'production' and (DEBUG or not notifications_configured):
        print("⚠️  WARNING: Production environment detected with incomplete configuration!")

if __name__ == "__main__":
    print_config_status()
    config = get_production_config()
    
    print("\nConfiguration loaded successfully!")
    print(f"Environment: {config['environment']}")
    print(f"Database: {config['database_type']}")
    print(f"Default location: {config['geofence']['DEFAULT_LOCATION']}")
    
    print("\nTo set up production configuration:")
    print("1. Copy .env.template to .env")
    print("2. Fill in your actual API keys and settings")
    print("3. Set ENVIRONMENT=production in .env")
    print("4. Run python config/production_config.py to validate")