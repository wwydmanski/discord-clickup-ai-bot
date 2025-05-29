# Discord ClickUp Bot

A Discord bot that automatically creates ClickUp tasks when mentioned in Discord messages. Perfect for turning Discord conversations into actionable tasks in your project management workflow.

## Features

- 🤖 **Automatic Task Creation**: Mention the bot with a message to create a ClickUp task
- 📋 **Rich Task Details**: Tasks include message content, author info, channel, timestamp, and link back to Discord
- 🎨 **Beautiful Embeds**: Clean Discord embeds for feedback and status
- ⚡ **Real-time Response**: Instant feedback when tasks are created
- 🔧 **Easy Configuration**: Simple environment variable setup
- 📝 **Logging**: Comprehensive logging for debugging and monitoring

## Prerequisites

1. **Discord Bot**: Create a Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. **ClickUp API**: Get your ClickUp API token from [ClickUp Settings](https://app.clickup.com/settings/apps)
3. **Python 3.8+**: Make sure you have Python 3.8 or higher installed

## Setup Instructions

### 1. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Copy the bot token (you'll need this for the `.env` file)
6. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional)

### 2. Discord Bot Permissions

When inviting the bot to your server, make sure it has these permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Read Message History
- Add Reactions (optional)

Invite URL template:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=412384&scope=bot
```

### 3. ClickUp Setup

1. Go to [ClickUp Settings > Apps](https://app.clickup.com/settings/apps)
2. Generate a new API token
3. Copy the token (you'll need this for the `.env` file)
4. Find your List ID:
   - Go to the ClickUp list where you want tasks created
   - Copy the list ID from the URL: `https://app.clickup.com/.../list/LIST_ID`

### 4. Installation

1. Clone or navigate to the bot directory:
   ```bash
   cd misc/discord-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create environment file:
   ```bash
   cp env.example .env
   ```

4. Edit `.env` file with your credentials:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   CLICKUP_API_TOKEN=your_clickup_api_token_here
   CLICKUP_LIST_ID=your_clickup_list_id_here
   CLICKUP_TEAM_ID=your_clickup_team_id_here  # Optional
   ```

### 5. Running the Bot

```bash
python bot.py
```

The bot will start and show a "connected to Discord" message when ready.

## Usage

### Creating Tasks

Simply mention the bot in any Discord message with your task description:

```
@YourBot Please review the new authentication system
```

```
@YourBot Bug: Users can't log in with special characters in password
```

```
@YourBot Create documentation for the new API endpoints
```

### Commands

- `!help` - Show help information
- `!status` - Check bot status and ping

### Task Details

Each created ClickUp task will include:
- **Task Name**: "Discord Task: [first 50 characters of message]"
- **Description**: Full message content plus metadata
- **Author**: Discord username and display name
- **Channel**: Where the message was sent
- **Server**: Which Discord server
- **Timestamp**: When the message was sent
- **Link**: Direct link back to the Discord message

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Your Discord bot token |
| `CLICKUP_API_TOKEN` | Yes | Your ClickUp API token |
| `CLICKUP_LIST_ID` | Yes | ClickUp list ID where tasks will be created |
| `CLICKUP_TEAM_ID` | No | ClickUp team ID (for team member features) |

### Customization

You can customize the bot behavior by modifying `bot.py`:

- **Task Priority**: Change the `priority` value in the `create_task` method (1=Urgent, 2=High, 3=Normal, 4=Low)
- **Task Status**: Modify the `status` field to set a different default status
- **Bot Prefix**: Change the `command_prefix` in the bot initialization
- **Response Messages**: Customize the embed messages and responses

## Troubleshooting

### Common Issues

1. **Bot doesn't respond to mentions**:
   - Check that Message Content Intent is enabled in Discord Developer Portal
   - Verify the bot has permission to read messages in the channel

2. **ClickUp API errors**:
   - Verify your API token is correct
   - Check that the List ID exists and you have access to it
   - Ensure your ClickUp plan supports API access

3. **Bot goes offline**:
   - Check the console for error messages
   - Verify your Discord token is still valid
   - Check your internet connection

### Debug Mode

To enable more detailed logging, modify the logging level in `bot.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Testing the Setup

1. Test ClickUp connection:
   ```python
   # Add this to test your ClickUp setup
   from bot import ClickUpClient
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   client = ClickUpClient(
       api_token=os.getenv('CLICKUP_API_TOKEN'),
       list_id=os.getenv('CLICKUP_LIST_ID')
   )
   
   # This should create a test task
   response = client.create_task("Test Task", "This is a test task from the bot setup")
   print(response)
   ```

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Regularly rotate your API tokens
- Use environment variables in production deployments
- Consider using Discord slash commands for additional security

## Production Deployment

For production deployment, consider:

1. **Process Management**: Use PM2, systemd, or Docker
2. **Monitoring**: Set up logging and health checks
3. **Error Handling**: Implement proper error recovery
4. **Rate Limiting**: Be aware of Discord and ClickUp API rate limits
5. **Backup**: Keep backups of your configuration

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License. 