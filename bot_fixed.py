import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClickUpClient:
    """Client for interacting with ClickUp API"""
    
    def __init__(self, api_token: str, list_id: str, team_id: Optional[str] = None):
        self.api_token = api_token
        self.list_id = list_id
        self.team_id = team_id
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    def create_task(self, name: str, description: str, assignees: Optional[list] = None) -> dict:
        """Create a new task in ClickUp"""
        url = f"{self.base_url}/list/{self.list_id}/task"
        
        task_data = {
            "name": name,
            "description": description,
            "status": "To do",
            "priority": 3,  # Normal priority
            "due_date": None,
            "due_date_time": False,
            "time_estimate": None,
            "start_date": None,
            "start_date_time": False,
            "notify_all": True,
            "parent": None,
            "links_to": None,
            "check_required_custom_fields": True,
            "custom_fields": []
        }
        
        if assignees:
            task_data["assignees"] = assignees
        
        try:
            response = requests.post(url, json=task_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create ClickUp task: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Initialize ClickUp client
clickup_client = ClickUpClient(
    api_token=os.getenv('CLICKUP_API_TOKEN'),
    list_id=os.getenv('CLICKUP_LIST_ID'),
    team_id=os.getenv('CLICKUP_TEAM_ID')
)

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info(f"Registered commands: {[cmd.name for cmd in bot.commands]}")
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="for mentions to create ClickUp tasks"
        )
    )

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    logger.info(f"Received message: {message.content}")
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    logger.info(f"user.id: {bot.user.id}")
    logger.info(f"Message starts with prefix: {message.content.startswith(bot.command_prefix)}")
    logger.info(f"Bot mentioned: {bot.user in message.mentions}")
    
    # Process commands first (this handles !help, !status, !health)
    await bot.process_commands(message)
    
    # Only check for task creation if message doesn't start with command prefix
    # and the bot is mentioned
    if not message.content.startswith(bot.command_prefix) and bot.user in message.mentions:
        await handle_task_creation(message)

async def handle_task_creation(message):
    """Handle creating a ClickUp task from a Discord message"""
    try:
        # Send typing indicator
        async with message.channel.typing():
            # Extract task information from the message
            content = message.content
            
            # Remove bot mention from content
            clean_content = content.replace(f'<@{bot.user.id}>', '').strip()
            clean_content = clean_content.replace(f'<@!{bot.user.id}>', '').strip()
            
            if not clean_content:
                await message.reply("❌ Please provide a task description when mentioning me!")
                return
            
            # Create task name and description
            task_name = f"Discord Task: {clean_content[:50]}{'...' if len(clean_content) > 50 else ''}"
            
            task_description = f"""
**Task created from Discord**

**Message:** {clean_content}

**Author:** {message.author.display_name} ({message.author.name}#{message.author.discriminator})
**Channel:** #{message.channel.name}
**Guild:** {message.guild.name if message.guild else 'DM'}
**Timestamp:** {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Message Link:** {message.jump_url}
            """.strip()
            
            # Create the task in ClickUp
            task_response = clickup_client.create_task(
                name=task_name,
                description=task_description
            )
            
            # Create embed for the response
            embed = discord.Embed(
                title="✅ Task Created Successfully!",
                description="I've created a new task in ClickUp based on your message.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Task Name",
                value=task_name,
                inline=False
            )
            
            embed.add_field(
                name="ClickUp Task ID",
                value=task_response.get('id', 'Unknown'),
                inline=True
            )
            
            if 'url' in task_response:
                embed.add_field(
                    name="Task URL",
                    value=f"[View in ClickUp]({task_response['url']})",
                    inline=True
                )
            
            embed.set_footer(text="ClickUp Discord Bot")
            
            await message.reply(embed=embed)
            
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        
        error_embed = discord.Embed(
            title="❌ Error Creating Task",
            description=f"Sorry, I encountered an error while creating the task: {str(e)}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        await message.reply(embed=error_embed)

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="ClickUp Discord Bot Help",
        description="I help you create ClickUp tasks directly from Discord!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="How to use",
        value="Simply mention me (@bot) in any message with your task description, and I'll create a ClickUp task for you!",
        inline=False
    )
    
    embed.add_field(
        name="Example",
        value=f"@{bot.user.display_name if bot.user else 'bot'} Review the new feature documentation",
        inline=False
    )
    
    embed.add_field(
        name="Commands",
        value="`!help` - Show this help message\n`!status` - Check bot status\n`!health` - Simple health check",
        inline=False
    )
    
    embed.set_footer(text="ClickUp Discord Bot")
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status_command(ctx):
    """Check bot status"""
    embed = discord.Embed(
        title="Bot Status",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="Status",
        value="🟢 Online and ready!",
        inline=True
    )
    
    embed.add_field(
        name="Guilds",
        value=str(len(bot.guilds)),
        inline=True
    )
    
    embed.add_field(
        name="Ping",
        value=f"{round(bot.latency * 1000)}ms",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='health')
async def health_command(ctx):
    """Simple health check command"""
    await ctx.send('ping')

def main():
    """Main function to run the bot"""
    # Check required environment variables
    required_vars = ['DISCORD_BOT_TOKEN', 'CLICKUP_API_TOKEN', 'CLICKUP_LIST_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file based on env.example")
        return
    
    try:
        bot.run(os.getenv('DISCORD_BOT_TOKEN'))
    except discord.LoginFailure:
        logger.error("Failed to login. Please check your Discord bot token.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 