#!/usr/bin/env python3
"""
SmartAttendAI Setup Script
Automates installation and configuration
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
import urllib.request
import tarfile

class SmartAttendAISetup:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.models_dir = self.root_dir / "models"
        self.data_dir = self.root_dir / "data"
        
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")
    
    def print_step(self, step_num, total, description):
        """Print step information"""
        print(f"[{step_num}/{total}] {description}...")
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        self.print_step(1, 7, "Checking Python version")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("  ✗ Python 3.8+ required")
            print(f"  Current version: {version.major}.{version.minor}.{version.micro}")
            sys.exit(1)
        
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    
    def create_directories(self):
        """Create necessary directories"""
        self.print_step(2, 7, "Creating directory structure")
        
        directories = [
            "models",
            "data/faces",
            "data/logs",
            "data/fraud_attempts",
            "config",
            "src/liveness",
            "src/face_recognition",
            "src/geofencing",
            "src/emotion_analysis",
            "src/fraud_detection",
            "src/voice_verification",
            "src/utils",
            "tests",
            "docs"
        ]
        
        for directory in directories:
            path = self.root_dir / directory
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created {directory}/")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_step(3, 7, "Installing dependencies")
        
        requirements_file = self.root_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("  ✗ requirements.txt not found")
            return False
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            print("  ✓ Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error installing dependencies: {e}")
            return False
    
    def download_dlib_model(self):
        """Download dlib facial landmarks predictor"""
        self.print_step(4, 7, "Downloading dlib model")
        
        model_path = self.models_dir / "shape_predictor_68_face_landmarks.dat"
        
        if model_path.exists():
            print("  ✓ Model already exists")
            return True
        
        url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
        compressed_path = self.models_dir / "shape_predictor_68_face_landmarks.dat.bz2"
        
        try:
            print("  Downloading (may take a few minutes)...")
            urllib.request.urlretrieve(url, compressed_path)
            
            print("  Extracting...")
            import bz2
            with bz2.open(compressed_path, 'rb') as source:
                with open(model_path, 'wb') as dest:
                    dest.write(source.read())
            
            # Remove compressed file
            compressed_path.unlink()
            
            print("  ✓ Model downloaded and extracted")
            return True
        except Exception as e:
            print(f"  ✗ Error downloading model: {e}")
            print("  Please download manually from: http://dlib.net/files/")
            return False
    
    def create_env_template(self):
        """Create .env template"""
        self.print_step(5, 7, "Creating configuration template")
        
        env_template = self.root_dir / ".env.template"
        env_file = self.root_dir / ".env"
        
        template_content = """# SmartAttendAI Configuration

# Telegram Bot (for notifications)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional: Database
# DATABASE_TYPE=sqlite  # or firebase
# FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
"""
        
        with open(env_template, 'w') as f:
            f.write(template_content)
        
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(template_content)
        
        print("  ✓ Configuration template created")
        print("  Please edit .env file with your API keys")
    
    def initialize_database(self):
        """Initialize SQLite database"""
        self.print_step(6, 7, "Initializing database")
        
        try:
            from src.utils.database import AttendanceDatabase
            
            db = AttendanceDatabase()
            print("  ✓ Database initialized")
            return True
        except Exception as e:
            print(f"  ✗ Error initializing database: {e}")
            return False
    
    def create_sample_data(self):
        """Create sample configuration files"""
        self.print_step(7, 7, "Creating sample files")
        
        # Sample CSV for bulk student import
        sample_csv = self.root_dir / "data" / "sample_students.csv"
        csv_content = """name,id,roll_number,email,phone,image_path
John Doe,STU001,22001,john@example.com,+1234567890,data/faces/john_doe.jpg
Jane Smith,STU002,22002,jane@example.com,+1234567891,data/faces/jane_smith.jpg
"""
        
        with open(sample_csv, 'w') as f:
            f.write(csv_content)
        
        print("  ✓ Sample files created")
        print(f"  Sample CSV: {sample_csv}")
    
    def print_next_steps(self):
        """Print next steps for user"""
        self.print_header("Setup Complete!")
        
        print("✓ SmartAttendAI has been successfully set up!\n")
        print("Next Steps:\n")
        print("1. Edit .env file with your API credentials:")
        print("   - Telegram Bot Token (for notifications)")
        print()
        print("2. Register students:")
        print("   python -c \"from src.face_recognition.recognizer import *\"")
        print()
        print("3. Configure classroom locations in config/settings.py")
        print()
        print("4. Run the application:")
        print("   python main.py")
        print()
        print("5. For web interface (coming soon):")
        print("   python app.py")
        print()
        print("For detailed documentation, see README.md")
        print()
    
    def run(self):
        """Run complete setup"""
        self.print_header("SmartAttendAI Setup")
        print("Welcome to SmartAttendAI installation!\n")
        
        try:
            self.check_python_version()
            self.create_directories()
            self.install_dependencies()
            self.download_dlib_model()
            self.create_env_template()
            self.initialize_database()
            self.create_sample_data()
            self.print_next_steps()
            
        except KeyboardInterrupt:
            print("\n\nSetup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n✗ Setup failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    setup = SmartAttendAISetup()
    setup.run()