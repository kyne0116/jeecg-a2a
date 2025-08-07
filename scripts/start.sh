#!/bin/bash

# JEECG A2A Platform - Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi

    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Found Python $python_version"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install uv first:"
        print_status "curl -LsSf https://astral.sh/uv/install.sh | sh"
        print_status "or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi

    uv_version=$(uv --version)
    print_status "Found $uv_version"
}

# Setup virtual environment
setup_virtual_environment() {
    print_status "Setting up virtual environment..."

    if [ -d ".venv" ]; then
        print_status "Virtual environment already exists"
    else
        uv venv
        print_success "Virtual environment created"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."

    if [ -f "pyproject.toml" ]; then
        uv sync
        print_success "Dependencies installed successfully"
    else
        print_error "pyproject.toml not found"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p uploads
    mkdir -p ui/static/uploads
    
    print_success "Directories created"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please edit .env file with your configuration"
        else
            print_warning ".env.example not found, please create .env manually"
        fi
    else
        print_status ".env file already exists"
    fi
}

# Check if port is available
check_port() {
    local port=${1:-6000}
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Port $port is already in use"
        print_status "You may need to stop the existing service or change the port in .env"
    else
        print_status "Port $port is available"
    fi
}

# Start the platform
start_platform() {
    print_status "Starting JEECG A2A Platform..."

    # Check if we should run in development mode
    if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
        print_status "Starting in development mode with auto-reload"
        uv run main.py --reload --debug
    else
        uv run main.py
    fi
}

# Main execution
main() {
    echo "=================================================="
    echo "🚀 JEECG A2A Platform Startup Script"
    echo "=================================================="
    echo ""
    
    # Change to script directory
    cd "$(dirname "$0")/.."
    
    print_status "Working directory: $(pwd)"
    
    # Run checks and setup
    check_python
    check_uv
    create_directories
    setup_environment

    # Install dependencies if --install flag is provided
    if [ "$1" = "--install" ] || [ "$1" = "-i" ]; then
        setup_virtual_environment
        install_dependencies
        shift
    fi
    
    # Check port availability
    check_port 8000
    
    echo ""
    print_status "All checks passed. Starting platform..."
    echo ""
    
    # Start the platform
    start_platform "$@"
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "JEECG A2A Platform Start Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Prerequisites:"
        echo "  - Python 3.9+"
        echo "  - uv package manager (https://docs.astral.sh/uv/)"
        echo ""
        echo "Options:"
        echo "  --install, -i    Setup virtual environment and install dependencies"
        echo "  --dev, -d        Start in development mode with auto-reload"
        echo "  --help, -h       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0               Start the platform"
        echo "  $0 --install     Setup and start"
        echo "  $0 --dev         Start in development mode"
        echo "  $0 -i -d         Setup and start in dev mode"
        echo ""
        echo "Manual setup:"
        echo "  uv venv          Create virtual environment"
        echo "  uv sync          Install dependencies"
        echo "  uv run main.py   Start platform"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
