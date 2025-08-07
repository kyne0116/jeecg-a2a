#!/usr/bin/env python3
"""
JEECG A2A Platform - Quick Start Script

This script provides a simple way to start the platform with all necessary setup.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_banner():
    """Print startup banner."""
    print("=" * 60)
    print("🚀 JEECG A2A Platform - Quick Start")
    print("=" * 60)
    print()


def check_python():
    """Check Python version."""
    print("📋 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)

    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")


def check_uv():
    """Check if uv is installed."""
    print("📦 Checking uv package manager...")

    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ uv {version} detected")
            return True
        else:
            print("❌ uv is not working properly")
            return False
    except FileNotFoundError:
        print("❌ uv is not installed")
        print("   Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   or visit: https://docs.astral.sh/uv/getting-started/installation/")
        return False


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "data", 
        "uploads",
        "ui/static/uploads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")


def setup_environment():
    """Setup environment file."""
    print("⚙️  Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("   ✅ Created .env from .env.example")
            print("   ⚠️  Please edit .env with your configuration")
        else:
            print("   ⚠️  .env.example not found")
    else:
        print("   ✅ .env file already exists")


def setup_virtual_environment():
    """Setup virtual environment with uv."""
    print("🔧 Setting up virtual environment...")

    try:
        # Check if .venv already exists
        venv_path = Path(".venv")
        if venv_path.exists():
            print("   ✅ Virtual environment already exists")
            return True

        # Create virtual environment
        subprocess.run(["uv", "venv"], check=True, capture_output=True)
        print("   ✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install Python dependencies using uv."""
    print("📦 Installing dependencies...")

    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        print("   ❌ pyproject.toml not found")
        return False

    try:
        # Install dependencies using uv
        subprocess.run(["uv", "sync"], check=True, capture_output=True)
        print("   ✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install dependencies: {e}")
        return False


def check_port(port=8000):
    """Check if port is available."""
    print(f"🔍 Checking port {port}...")
    
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result == 0:
                print(f"   ⚠️  Port {port} is already in use")
                return False
            else:
                print(f"   ✅ Port {port} is available")
                return True
    except Exception as e:
        print(f"   ⚠️  Could not check port: {e}")
        return True


def start_platform(dev_mode=False):
    """Start the platform using uv."""
    print("🚀 Starting JEECG A2A Platform...")
    print()

    # Use the simple start.py script to avoid Click issues
    cmd = ["uv", "run", "start.py"]
    if dev_mode:
        print("   🔧 Development mode enabled")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Platform stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Platform failed to start: {e}")
        print("\n🔧 Alternative startup methods:")
        print("1. python start.py")
        print("2. uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload")
        sys.exit(1)


def main():
    """Main function."""
    print_banner()
    
    # Parse command line arguments
    install_deps = "--install" in sys.argv or "-i" in sys.argv
    dev_mode = "--dev" in sys.argv or "-d" in sys.argv
    help_requested = "--help" in sys.argv or "-h" in sys.argv
    
    if help_requested:
        print("JEECG A2A Platform Quick Start")
        print()
        print("Usage: python quick_start.py [OPTIONS]")
        print()
        print("Prerequisites:")
        print("  - Python 3.9+")
        print("  - uv package manager (https://docs.astral.sh/uv/)")
        print()
        print("Options:")
        print("  --install, -i    Setup virtual environment and install dependencies")
        print("  --dev, -d        Start in development mode")
        print("  --help, -h       Show this help message")
        print()
        print("Examples:")
        print("  python quick_start.py           # Start the platform")
        print("  python quick_start.py --install # Setup and start")
        print("  python quick_start.py --dev     # Start in dev mode")
        print()
        print("Manual setup:")
        print("  uv venv                         # Create virtual environment")
        print("  uv sync                         # Install dependencies")
        print("  uv run main.py                  # Start platform")
        return
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📍 Working directory: {os.getcwd()}")
    print()
    
    # Run setup steps
    check_python()

    # Check uv availability
    if not check_uv():
        sys.exit(1)

    create_directories()
    setup_environment()

    if install_deps:
        if not setup_virtual_environment():
            print("\n❌ Virtual environment setup failed.")
            sys.exit(1)

        if not install_dependencies():
            print("\n❌ Dependency installation failed.")
            sys.exit(1)
    
    check_port(6000)
    
    print()
    print("✅ All checks passed!")
    print()
    
    # Start the platform
    start_platform(dev_mode)


if __name__ == "__main__":
    main()
