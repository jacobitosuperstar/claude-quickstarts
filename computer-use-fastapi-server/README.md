# Computer Use FastAPI Server

A production-ready FastAPI backend for Claude's Computer Use capability with session management, real-time streaming, and a simple web UI.

## Features

- **Session Management**: Create, list, and manage multiple agent sessions
- **Real-time Streaming**: WebSocket-based live updates of agent actions
- **Concurrent Execution**: Run multiple agent sessions simultaneously without blocking
- **Chat History**: SQLite persistence for all messages and tool interactions
- **VNC Integration**: Built-in noVNC viewer to watch the agent work
- **Simple Web UI**: HTML/JS interface - no complex frontend frameworks

## How the Sandbox Works

**Important**: The agent does NOT control your actual computer. It runs in a completely isolated virtual desktop inside the Docker container.

```
┌─────────────────────────────────────────────┐
│  Docker Container                           │
│  ┌───────────────────────────────────────┐  │
│  │  Virtual Desktop (Xvfb)               │  │
│  │  - Isolated Linux environment         │  │
│  │  - Firefox, terminal, file manager    │  │
│  │  - Agent clicks/types only here       │  │
│  └───────────────────────────────────────┘  │
│              │                              │
│              ▼ VNC stream                   │
│  ┌───────────────────────────────────────┐  │
│  │  noVNC (port 6080)                    │──┼──► You watch in browser
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

- **Xvfb**: A virtual X server that creates a fake display in memory
- **x11vnc**: Captures the virtual desktop and streams it
- **noVNC**: Web-based VNC viewer so you can watch the agent work

This means:
- Your real computer is completely safe
- The agent cannot access your files or screen
- If something goes wrong, just restart the container

**Concurrency note:** The API supports multiple sessions (database records, WebSocket connections, async tasks), but they all share the **same virtual desktop**. If you run two sessions simultaneously, both agents would control the same screen and interfere with each other. For true isolation, you would need to run multiple containers or implement multiple Xvfb displays (not included in this quickstart).

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-quickstarts
   cd claude-quickstarts/computer-use-fastapi-server
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

3. **Run with Docker Compose**:
   ```bash
   docker compose up --build
   ```

4. **Access the application**:
   - Web UI: http://localhost:8000/ui/
   - VNC Viewer: http://localhost:6080/vnc.html
   - API Docs: http://localhost:8000/docs

### Local Development

1. **Install dependencies** (requires [uv](https://docs.astral.sh/uv/)):
   ```bash
   uv sync
   ```

2. **Set environment variables**:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Run the server**:
   ```bash
   uv run python main.py
   ```

## API Endpoints

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sessions/` | Create a new session |
| `GET` | `/sessions/` | List all sessions |
| `GET` | `/sessions/{id}` | Get session details |
| `PATCH` | `/sessions/{id}/finish` | Mark session as finished |
| `DELETE` | `/sessions/{id}` | Delete session and messages |
| `GET` | `/sessions/{id}/messages` | Get session message history |
| `WS` | `/sessions/{id}/ws` | WebSocket for real-time interaction |

### WebSocket Protocol

Connect to `/sessions/{session_id}/ws` and send:
```json
{
  "message": "Your task for the agent",
  "api_key": "optional_api_key_override"
}
```

Receive real-time updates:
```json
{
  "type": "text|tool_use|tool_result|thinking|completed|error",
  "content": { ... },
  "timestamp": "2024-01-01T00:00:00"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `DATABASE_URL` | SQLite database path | `sqlite:///./db.sqlite3` |
| `MESSAGE_BATCH_SIZE` | Messages to buffer before DB write | `10` |

### Session Options

When creating a session, you can configure screenshot storage:
```json
{
  "store_screenshots": true,
  "screenshot_scale": 2,
  "screenshot_quality": 70
}
```

- `store_screenshots`: Whether to save screenshots in message history
- `screenshot_scale`: Integer scaling factor (1=full, 2=half, 4=quarter)
- `screenshot_quality`: JPEG quality (10-100)

## Architecture

```
computer-use-fastapi-server/
├── app/
│   ├── base/           # Base utilities and test infrastructure
│   ├── sessions/       # Session management module
│   │   ├── models.py   # SQLAlchemy models
│   │   ├── schemas.py  # Pydantic schemas
│   │   ├── services.py # Business logic
│   │   └── views.py    # API endpoints
│   ├── ui/             # Web UI views
│   ├── templates/      # Jinja2 HTML templates
│   ├── database.py     # Database configuration
│   └── settings.py     # Application settings
├── computer_use_demo/  # Anthropic's computer use agent
├── main.py             # FastAPI application entry
├── Dockerfile          # Container with X server & VNC
└── docker-compose.yml  # Easy deployment
```

## How It Works

1. **Session Creation**: Each session gets a unique ID and tracks its status
2. **WebSocket Connection**: Client connects and sends a task message
3. **Agent Execution**: The computer use agent runs asynchronously, streaming updates
4. **Tool Execution**: Mouse clicks, typing, screenshots are captured and streamed
5. **Persistence**: All messages are batched and stored in SQLite
6. **Concurrent Sessions**: Multiple sessions run in parallel using asyncio tasks

## License

MIT License - see [LICENSE](../LICENSE) for details.
