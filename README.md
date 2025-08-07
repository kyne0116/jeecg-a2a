# JEECG A2A Protocol Platform

A complete A2A (Agent-to-Agent) protocol platform implementation based on Google's A2A specification, providing enterprise-grade agent orchestration and communication capabilities.

## Features

### 🤖 Agent Registry Center

- **Agent Auto-Discovery**: Automatic agent discovery and registration
- **Agent Card Management**: Standard `/.well-known/agent.json` endpoint implementation
- **Metadata Management**: Comprehensive agent metadata and capability declaration
- **Health Monitoring**: Service health checks and status monitoring
- **Dynamic Registration**: Runtime agent registration and deregistration

### 🔄 Agent Scheduling Engine

- **AI-Powered Routing**: Intelligent task routing based on agent capabilities
- **Load Balancing**: Automatic load distribution across available agents
- **Fault Tolerance**: Automatic failover and error recovery
- **Multi-Agent Collaboration**: Workflow orchestration and agent coordination
- **Async Processing**: Task queue management and concurrent execution

### 💬 Chat User Interface

- **Modern Web UI**: Complete web-based chat interface
- **Real-time Communication**: WebSocket and Server-Sent Events support
- **Multi-media Messages**: Text, images, files, and structured data support
- **Session Management**: Conversation history and context persistence
- **State Management**: Advanced session state maintenance
- **Offline-Capable**: Self-contained with no external CDN dependencies

## 🌐 Self-Contained Architecture

The JEECG A2A Platform is designed to be completely self-contained and offline-capable:

- **No External CDN Dependencies**: All frontend resources (Bootstrap, Bootstrap Icons) are bundled locally
- **Offline Operation**: The platform works without internet connectivity to external services
- **Enterprise-Ready**: Suitable for air-gapped environments and secure deployments
- **Local Static Resources**: All CSS, JavaScript, and font files are served from `/static/vendor/`

### Included Local Resources

- **Bootstrap 5.3.0**: Complete CSS and JavaScript bundle
- **Bootstrap Icons 1.10.0**: Full icon font with WOFF/WOFF2 formats
- **Self-Hosted Fonts**: No external font loading dependencies

## Quick Start

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Installation & Running

#### Option 1: Quick Start Script (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup virtual environment and install dependencies
python quick_start.py --install

# Or start in development mode
python quick_start.py --dev

# For help
python quick_start.py --help
```

#### Option 2: Manual Setup with uv (Recommended)

```bash
# 1. Create virtual environment
uv venv

# 2. Install dependencies
uv sync

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Run the platform
uv run main.py
```

#### Option 3: Traditional pip Setup

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Run the platform
python main.py
```

#### Option 4: Using Scripts

```bash
# Linux/Mac
./scripts/start.sh --install

# Windows
scripts\start.bat --install
```

#### Option 5: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

The platform will be available at: **http://localhost:9000**

## Virtual Environment Management

### Using uv (Recommended)

uv provides fast and reliable Python package management with automatic virtual environment handling:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Install dependencies
uv sync

# Run commands in the virtual environment
uv run main.py
uv run python test_platform.py
uv run pytest

# Add new dependencies
uv add package-name

# Remove dependencies
uv remove package-name

# Update dependencies
uv sync --upgrade
```

### Using traditional venv

If you prefer traditional Python virtual environments:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install project in development mode
pip install -e .

# Deactivate when done
deactivate
```

### Environment Variables

The platform uses environment variables for configuration. Copy the example file and customize:

```bash
cp .env.example .env
```

Key configuration options:

- `PORT`: Server port (default: 9000)
- `HOST`: Server host (default: 127.0.0.1)
- `DEBUG`: Enable debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: INFO)
- `MAX_CONCURRENT_TASKS`: Maximum concurrent tasks (default: 100)

### API Endpoints

- **Agent Card**: `GET /.well-known/agent.json`
- **Agent Registration**: `POST /api/agents/register`
- **Task Submission**: `POST /api/tasks`
- **Health Check**: `GET /health`
- **Chat Interface**: `GET /` (Web UI)

## Architecture

```
jeecg-a2a/
├── core/                   # Core A2A protocol implementation
│   ├── agent_registry/     # Agent registration and discovery
│   ├── scheduler/          # Task scheduling and routing
│   └── protocol/           # A2A protocol handlers
├── ui/                     # Web chat interface
│   ├── components/         # UI components
│   ├── static/             # Static assets
│   └── templates/          # HTML templates
├── api/                    # REST API endpoints
├── config/                 # Configuration management
├── utils/                  # Utility functions
└── tests/                  # Test suites
```

## Configuration

The platform supports configuration through environment variables and config files:

- `PORT`: Server port (default: 9000)
- `HOST`: Server host (default: 127.0.0.1)
- `LOG_LEVEL`: Logging level (default: INFO)
- `AGENT_TIMEOUT`: Agent response timeout (default: 30s)
- `MAX_CONCURRENT_TASKS`: Maximum concurrent tasks (default: 100)

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy .
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker.
