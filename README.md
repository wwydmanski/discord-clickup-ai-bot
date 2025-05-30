# Discord ClickUp Bot 🤖

Advanced Discord bot that creates and manages ClickUp tasks using AI-powered semantic analysis and intelligent context filtering.

## Features 🚀

### 🎯 Task Creation
- **AI-Powered Task Titles**: Generates intelligent, actionable task titles using OpenAI GPT-4o
- **Smart Context Analysis**: Filters channel history to include only relevant messages for context
- **Intelligent List Routing**: 
  - Messages containing "backlog" → Backlog list
  - Other messages → Newest Sprint list (from specified folder)
- **Rich Task Descriptions**: Includes Discord context, author info, and message links

### 🔄 Task Management  
- **Semantic Task Matching**: Find and update tasks using AI-powered similarity matching
- **Status Updates**: Update task statuses with natural language commands
- **Sprint Integration**: Automatically works with the newest sprint list

### 🧠 AI Features
- **Context Filtering**: AI analyzes channel history and selects only relevant messages
- **Semantic Understanding**: Matches tasks based on meaning, not just keywords
- **Smart Title Generation**: Creates concise, actionable task titles from descriptions
- **Natural Language Processing**: Understands various status formats and synonyms

## Commands 📋

### Core Commands

#### Create Tasks
Simply mention the bot with your task description:
```
@bot Review the new authentication system
@bot backlog Create API documentation
@bot Fix login bug with special characters
```

#### Smart Command Detection
The bot uses AI to intelligently recognize when you're giving it a command vs. describing a task:
```
# Commands - Bot analyzes conversation context:
@bot dodaj taska             # AI recognizes: command to create task
@bot wrzuć to do backlog     # AI recognizes: command to add to backlog 
@bot task z tego             # AI recognizes: command to create from context
@bot create task             # AI recognizes: direct command
@bot save this as a task     # AI recognizes: natural language command
@bot can you make a task?    # AI recognizes: polite request command

# Task descriptions - Used directly:
@bot Implement user authentication system    # AI recognizes: specific task
@bot Fix bug with password validation        # AI recognizes: specific task
@bot Review API documentation               # AI recognizes: specific task
```

**Key Benefits:**
- **Natural Language**: No need to memorize specific phrases
- **Multilingual**: Works with Polish and English expressions
- **Context-Aware**: Understands intent, not just keywords
- **Flexible**: Recognizes various ways of expressing the same intent

#### Update Tasks
Use semantic matching to find and update existing tasks:
```
!update integracja bota z clickupem review
!update fix login bug in progress  
!update dokumentacja api closed
!update authentication system resolved
```

#### View Tasks
```
!tasks                    # Show tasks in newest sprint list
!lists                    # Show available sprint lists
```

#### Bot Management
```
!help                     # Show detailed help information
!status                   # Check bot status and connections
!health                   # Simple health check
```

## Valid Task Statuses 📊

The bot accepts various status formats and automatically normalizes them:

| Input Formats | Normalized Status |
|---------------|------------------|
| `to do`, `todo`, `backlog` | `to do` |
| `in progress`, `progress`, `working`, `started` | `in progress` |
| `in review`, `review`, `reviewing` | `in review` |
| `done`, `complete`, `completed`, `finished` | `complete` |
| `closed`, `close`, `resolved`, `fixed` | `closed` |

## Setup Instructions 🔧

### 1. Prerequisites
- Docker and Docker Compose (recommended)
- OR Python 3.8+ for local development
- Discord Bot Token
- ClickUp API Token
- OpenAI API Key (recommended for AI features)

### 2. Project Structure
```
discord-bot/
├── src/                    # Source code
│   ├── bot.py             # Main bot application
│   ├── run.py             # Development runner
│   ├── test_clickup.py    # ClickUp API testing
│   └── minimal_test.py    # Basic functionality tests
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── docker-run.sh          # Docker management script
├── requirements.txt       # Python dependencies
├── env.example            # Environment template
├── .dockerignore          # Docker ignore patterns
└── README.md              # This file
```

### 3. Quick Start with Docker (Recommended) 🐳

#### Step 1: Clone and Configure
```bash
cd misc/discord-bot
cp env.example .env
# Edit .env with your credentials
```

#### Step 2: Run the bot
```bash
# Make the script executable
chmod +x docker-run.sh

# Start the bot
./docker-run.sh run
```

#### Step 3: Monitor
```bash
# Check status
./docker-run.sh status

# View logs
./docker-run.sh logs

# Restart if needed
./docker-run.sh restart
```

### 4. Docker Management Commands

The `docker-run.sh` script provides easy management:

```bash
./docker-run.sh build      # Build Docker image
./docker-run.sh run        # Start the bot
./docker-run.sh stop       # Stop the bot
./docker-run.sh restart    # Restart the bot
./docker-run.sh logs       # Show bot logs
./docker-run.sh status     # Show bot status
./docker-run.sh clean      # Clean up Docker resources
./docker-run.sh update     # Update and restart bot
./docker-run.sh help       # Show help
```

### 5. Manual Docker Commands

If you prefer manual Docker management:

```bash
# Build the image
docker build -t discord-clickup-bot .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f discord-bot

# Stop
docker-compose down
```

### 6. Local Development Setup

For local development without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python src/bot.py

# Or use the runner script
python src/run.py
```

## Environment Configuration 🔧

Create a `.env` file based on `env.example`:

```env
# Discord (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# ClickUp (Required)
CLICKUP_API_TOKEN=your_clickup_api_token_here
CLICKUP_LIST_ID=your_backlog_list_id_here
CLICKUP_TEAM_ID=your_team_id_here
CLICKUP_FOLDER_ID=90155097400

# OpenAI (Recommended - enables AI features)
OPENAI_API_KEY=your_openai_api_key_here
```

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | ✅ | Discord bot authentication token | - |
| `CLICKUP_API_TOKEN` | ✅ | ClickUp API authentication token | - |
| `CLICKUP_LIST_ID` | ✅ | Default backlog list ID | - |
| `CLICKUP_TEAM_ID` | ✅ | ClickUp team/workspace ID | - |
| `CLICKUP_FOLDER_ID` | ⚠️ | Sprint folder ID for current sprint lists | - |
| `OPENAI_API_KEY` | ⚠️ | OpenAI API key for AI features | - |

## Docker Configuration Details 🐳

### Dockerfile Features
- **Base**: Python 3.11 slim image
- **Security**: Runs as non-root user
- **Health Checks**: Built-in Discord API connectivity checks
- **Optimization**: Multi-stage builds and layer caching

### Docker Compose Features
- **Auto-restart**: Container restarts unless manually stopped
- **Resource limits**: Memory and CPU constraints
- **Log rotation**: Automatic log file management
- **Health monitoring**: Health check integration
- **Volume mounting**: Persistent logs directory

### Production Deployment
```bash
# For production, you might want to:

# 1. Build and tag for your registry
docker build -t your-registry/discord-clickup-bot:v1.0 .
docker push your-registry/discord-clickup-bot:v1.0

# 2. Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# 3. Set up monitoring with Watchtower (auto-updates)
# Uncomment watchtower service in docker-compose.yml
```

## How It Works 🔍

### Task Creation Process
1. **Mention Detection**: Bot detects when it's mentioned in a message
2. **Command Analysis**: AI determines if mention is a command vs. task description
3. **Context Extraction**: For commands, analyzes recent conversation for task content
4. **Content Processing**: Extracts or generates task description based on type
5. **Context Analysis**: AI analyzes recent channel messages for relevance
6. **List Routing**: Determines target list based on "backlog" keyword
7. **Title Generation**: AI creates actionable task title using context
8. **Task Creation**: Creates task in ClickUp with rich description

### Smart Command Detection
1. **AI Intent Analysis**: Uses OpenAI to understand user intent from natural language
2. **Context Analysis**: When command detected, analyzes recent channel messages
3. **Task Extraction**: AI determines what task should be created from conversation
4. **Intelligent Processing**: No predefined phrases needed - understands various expressions
5. **Fallback System**: Simple heuristics when OpenAI is unavailable

### Task Update Process
1. **Command Parsing**: Extracts task description and desired status
2. **Task Retrieval**: Gets all tasks from newest sprint list
3. **Semantic Matching**: AI finds most similar task based on meaning
4. **Status Update**: Updates the matched task's status in ClickUp
5. **Confirmation**: Shows what was changed with visual feedback

### AI Context Filtering
1. **Message Collection**: Gathers recent channel messages (up to 20)
2. **Relevance Analysis**: AI evaluates which messages relate to the task
3. **Context Selection**: Only relevant messages are used for title generation
4. **Quality Enhancement**: Results in more accurate and contextual task titles

## API Setup Instructions 📝

### ClickUp Setup

#### Get API Token
1. Go to ClickUp Settings → Apps
2. Generate a new API token
3. Copy the token to your `.env` file

#### Get List and Folder IDs
1. **Backlog List ID**: Right-click your backlog list → Copy link → Extract ID from URL
2. **Folder ID**: Right-click your sprint folder → Copy link → Extract ID from URL
3. **Team ID**: Go to team settings → Copy team ID

### Discord Bot Setup
1. Create a new application at https://discord.com/developers/applications
2. Create a bot user and copy the token
3. Invite bot with necessary permissions:
   - Send Messages
   - Read Message History
   - Use Slash Commands
   - Embed Links
   - Add Reactions

## Troubleshooting 🔧

### Docker Issues

#### Container won't start
```bash
# Check logs
./docker-run.sh logs

# Check environment variables
docker-compose config

# Rebuild image
./docker-run.sh clean
./docker-run.sh build
./docker-run.sh run
```

#### Health check fails
```bash
# Check Discord API connectivity
docker exec discord-clickup-bot python -c "import requests; print(requests.get('https://discord.com/api/v10/gateway').status_code)"

# Check bot logs for connection issues
./docker-run.sh logs
```

### Common Issues

#### Bot doesn't respond to mentions
- Check Discord permissions (Read Messages, Send Messages)
- Verify bot token is correct
- Ensure `message_content` intent is enabled

#### ClickUp connection fails
```bash
# Test connection (if running locally)
python src/test_clickup.py

# In Docker
docker exec discord-clickup-bot python src/test_clickup.py
```
- Verify API token has proper permissions
- Check list and folder IDs are correct
- Ensure team ID matches your workspace

#### AI features not working
- Verify OpenAI API key is valid and has credits
- Check API key permissions for GPT-4o model
- Bot will fallback to basic features without OpenAI

### Debug Commands
```bash
# Bot commands
!status                   # Check all connections and configuration
!health                   # Simple ping test
!lists                    # Show available sprint lists
!tasks                    # Show tasks in current sprint

# Docker commands
./docker-run.sh status    # Container status and health
./docker-run.sh logs      # Real-time logs
docker stats              # Resource usage
```

## Monitoring and Maintenance 📊

### Log Management
```bash
# View live logs
./docker-run.sh logs

# Log files are stored in ./logs/ directory
ls -la logs/

# Logs are automatically rotated (max 10MB, 3 files)
```

### Health Monitoring
```bash
# Check health status
./docker-run.sh status

# Manual health check
docker exec discord-clickup-bot python -c "import requests; requests.get('https://discord.com/api/v10/gateway', timeout=5)"
```

### Updates and Maintenance
```bash
# Update bot code and restart
./docker-run.sh update

# Clean up old Docker resources
./docker-run.sh clean

# Full rebuild
docker system prune -a
./docker-run.sh build
./docker-run.sh run
```

## Advanced Configuration ⚙️

### Custom Docker Settings

Edit `docker-compose.yml` for custom configuration:

```yaml
# Resource limits
deploy:
  resources:
    limits:
      memory: 1G      # Increase for heavy usage
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'

# Environment overrides
environment:
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=DEBUG
```

### Scaling and Load Balancing
```bash
# Run multiple instances
docker-compose up --scale discord-bot=3

# Or use Docker Swarm for production
docker swarm init
docker stack deploy -c docker-compose.yml discord-bot-stack
```

## Security Best Practices 🔒

1. **Environment Variables**: Never commit `.env` to version control
2. **Token Rotation**: Regularly rotate API tokens
3. **Container Security**: Bot runs as non-root user
4. **Network Isolation**: Use Docker networks for service isolation
5. **Resource Limits**: Set memory and CPU limits
6. **Log Security**: Ensure logs don't contain sensitive information

## Contributing 🤝

Feel free to submit issues, feature requests, or pull requests to improve the bot's functionality.

## License 📄

This project is MIT-licensed.
