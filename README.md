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

## Valid Task Statuses 📊

The bot accepts various status formats and automatically normalizes them:

| Input Formats | Normalized Status |
|---------------|------------------|
| `to do`, `todo`, `backlog` | `to do` |
| `in progress`, `progress`, `working`, `started` | `in progress` |
| `in review`, `review`, `reviewing` | `in review` |
| `done`, `complete`, `completed`, `finished` | `complete` |
| `closed`, `close`, `resolved`, `fixed` | `closed` |

#### Update Tasks
Use semantic matching to find and update existing tasks:
