import asyncio
import logging
import os
from datetime import datetime
from typing import List, Optional

import discord
import openai
import requests
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class ClickUpClient:
    """Client for interacting with ClickUp API"""
    
    def __init__(self, api_token: str, list_id: str, team_id: Optional[str] = None, folder_id: Optional[str] = None):
        self.api_token = api_token
        self.list_id = list_id  # Backlog list ID
        self.team_id = team_id
        self.folder_id = folder_id  # Folder ID for current sprint lists
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    def get_folder_lists(self) -> List[dict]:
        """Get all lists from the specified folder"""
        if not self.folder_id:
            return []
        
        url = f"{self.base_url}/folder/{self.folder_id}/list"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("lists", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get folder lists: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return []
    
    def get_newest_list_from_folder(self) -> Optional[dict]:
        """Get the newest list from the folder (current sprint)"""
        lists = self.get_folder_lists()
        
        if not lists:
            logger.warning("No lists found in folder")
            return None
        
        # Since ClickUp returns lists in order and dates aren't available,
        # take the LAST list in the array (newest sprint)
        newest_list = lists[-1]  # Last item = newest
        
        logger.info(f"Available lists in order:")
        for i, lst in enumerate(lists):
            marker = " <- SELECTED (NEWEST)" if lst == newest_list else ""
            logger.info(f"  {i+1}. {lst.get('name')}{marker}")
        
        logger.info(f"Selected newest list: {newest_list.get('name')} (ID: {newest_list.get('id')})")
        return newest_list
    
    def create_task(self, name: str, description: str, list_id: Optional[str] = None, assignees: Optional[list] = None) -> dict:
        """Create a new task in ClickUp"""
        # Use provided list_id or default to backlog
        target_list_id = list_id or self.list_id
        url = f"{self.base_url}/list/{target_list_id}/task"
        
        task_data = {
            "name": name,
            "description": description,
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
    list_id=os.getenv('CLICKUP_LIST_ID'),  # Backlog list
    team_id=os.getenv('CLICKUP_TEAM_ID'),
    folder_id=os.getenv('CLICKUP_FOLDER_ID', '90155097400')  # Sprint folder
)

async def get_channel_context(channel, limit: int = 20) -> List[str]:
    """Get recent messages from channel for context"""
    try:
        messages = []
        async for message in channel.history(limit=limit):
            if not message.author.bot:  # Skip bot messages
                # Format: "Author: message content"
                msg_text = f"{message.author.display_name}: {message.content}"
                messages.append(msg_text)
        
        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))
    except Exception as e:
        logger.error(f"Error getting channel context: {e}")
        return []

async def filter_relevant_context(task_content: str, all_messages: List[str]) -> List[str]:
    """Use AI to filter only relevant messages from channel context"""
    if not all_messages or not openai.api_key:
        return all_messages[:5]  # Fallback to recent messages
    
    try:
        messages_text = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(all_messages)])
        
        system_prompt = """You are a context analyzer. Given a task request and recent channel messages, identify which messages are relevant to understanding the task context.

Rules:
- Only select messages that provide useful context for the task
- Ignore casual chat, off-topic discussions, or unrelated conversations
- Look for messages about the same topic, feature, bug, or project area
- Consider technical discussions, bug reports, feature requests related to the task
- Return only the numbers of relevant messages (e.g., "1,3,5")
- If no messages are relevant, return "none"
- Maximum 5 relevant messages"""

        user_prompt = f"""Task request: "{task_content}"

Recent channel messages:
{messages_text}

Which message numbers are relevant to this task? Return only numbers separated by commas (e.g., "1,3,5") or "none":"""

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        if result == "none":
            logger.info("AI determined no messages are relevant to task context")
            return []
        
        # Parse the response to get message numbers
        try:
            relevant_indices = [int(x.strip()) - 1 for x in result.split(',') if x.strip().isdigit()]
            relevant_messages = [all_messages[i] for i in relevant_indices if 0 <= i < len(all_messages)]
            
            logger.info(f"AI selected {len(relevant_messages)} relevant messages from {len(all_messages)} total")
            return relevant_messages[:5]  # Limit to 5 messages
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse AI response for context filtering: {e}")
            return all_messages[:3]  # Fallback
        
    except Exception as e:
        logger.error(f"Error filtering relevant context: {e}")
        return all_messages[:3]  # Fallback to recent messages

async def generate_smart_title(task_content: str, relevant_context: List[str]) -> str:
    """Generate intelligent task title using OpenAI with filtered context"""
    try:
        # Prepare context
        context_text = "\n".join(relevant_context) if relevant_context else ""
        
        system_prompt = """You are a helpful assistant that creates concise, actionable task titles for project management.
        
        Rules:
        - Keep titles under 60 characters
        - Make them actionable (start with verbs when possible)
        - Be specific and clear
        - Focus on the main action or deliverable
        - Don't include "Discord Task:" prefix
        - Use the relevant context to make the title more specific and accurate
        
        Examples:
        - Review authentication system implementation
        - Fix login bug with special characters
        - Create API documentation for endpoints
        - Update user interface design
        """
        
        context_section = f"\n\nRelevant context from recent discussion:\n{context_text}" if context_text else ""
        
        user_prompt = f"""Based on this task request: "{task_content}"{context_section}
        
        Generate a concise, actionable task title:"""
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        generated_title = response.choices[0].message.content.strip()
        
        # Fallback if OpenAI response is empty or too long
        if not generated_title or len(generated_title) > 80:
            return f"{task_content[:50]}{'...' if len(task_content) > 50 else ''}"
        
        return generated_title
        
    except Exception as e:
        logger.error(f"Error generating smart title: {e}")
        # Fallback to simple title
        return f"{task_content[:50]}{'...' if len(task_content) > 50 else ''}"

def determine_target_list(message_content: str) -> tuple[Optional[str], str]:
    """Determine which list to add the task to based on message content
    
    Returns:
        tuple: (list_id, list_description)
    """
    # Check if "backlog" appears in the message (case-insensitive)
    if "backlog" in message_content.lower():
        logger.info("Message contains 'backlog' - routing to backlog list")
        return None, "📋 Backlog"  # None means use default backlog list
    else:
        logger.info("Message doesn't contain 'backlog' - looking for newest sprint list")
        # Get newest list from sprint folder
        newest_list = clickup_client.get_newest_list_from_folder()
        if newest_list:
            list_name = newest_list.get('name', 'Current Sprint')
            list_id = newest_list.get('id')
            logger.info(f"Found newest sprint list: {list_name} (ID: {list_id})")
            return list_id, f"🚀 {list_name}"
        else:
            logger.warning("No lists found in folder, falling back to backlog")
            return None, "📋 Backlog (fallback)"

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info(f"Registered commands: {[cmd.name for cmd in bot.commands]}")
    
    # Test folder connection
    lists = clickup_client.get_folder_lists()
    logger.info(f"Found {len(lists)} lists in sprint folder")
    
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
            
            # Determine target list based on message content
            target_list_id, list_description = determine_target_list(clean_content)
            logger.info(f"Target list: {list_description} (ID: {target_list_id})")
            
            # Get channel context for smarter title generation
            logger.info("Getting channel context...")
            all_channel_messages = await get_channel_context(message.channel, limit=20)
            
            # Filter for relevant context using AI
            logger.info("Filtering relevant context with AI...")
            relevant_context = await filter_relevant_context(clean_content, all_channel_messages)
            
            # Generate smart title using OpenAI with filtered context
            logger.info("Generating smart title with relevant context...")
            task_name = await generate_smart_title(clean_content, relevant_context)
            
            # Prepare context summary for task description
            context_summary = ""
            if relevant_context:
                context_summary = f"\n\n**Relevant Context from Channel:**\n"
                context_summary += "\n".join([f"• {msg}" for msg in relevant_context])
            elif all_channel_messages:
                context_summary = f"\n\n**Note:** AI found no relevant context in recent {len(all_channel_messages)} messages"
            
            task_description = f"""
**Task created from Discord**

**Original Message:** {clean_content}

**Target List:** {list_description}
**Author:** {message.author.display_name} ({message.author.name}#{message.author.discriminator})
**Channel:** #{message.channel.name}
**Guild:** {message.guild.name if message.guild else 'DM'}
**Timestamp:** {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Message Link:** {message.jump_url}{context_summary}
            """.strip()
            
            # Create the task in ClickUp
            logger.info(f"Creating task with title: {task_name}")
            task_response = clickup_client.create_task(
                name=task_name,
                description=task_description,
                list_id=target_list_id  # Will use backlog if None
            )
            
            # Create embed for the response
            embed = discord.Embed(
                title="✅ Task Created Successfully!",
                description=f"I've created a new task in ClickUp with AI-generated title and smart context analysis.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🤖 AI-Generated Title",
                value=task_name,
                inline=False
            )
            
            embed.add_field(
                name="📝 Original Message",
                value=clean_content[:100] + ("..." if len(clean_content) > 100 else ""),
                inline=False
            )
            
            # Add context analysis info
            if relevant_context:
                context_info = f"Found {len(relevant_context)} relevant messages from {len(all_channel_messages)} analyzed"
            else:
                context_info = f"No relevant context found in {len(all_channel_messages)} recent messages"
            
            embed.add_field(
                name="🧠 Context Analysis",
                value=context_info,
                inline=False
            )
            
            embed.add_field(
                name="📍 Added to",
                value=list_description,
                inline=True
            )
            
            embed.add_field(
                name="🆔 Task ID",
                value=task_response.get('id', 'Unknown'),
                inline=True
            )
            
            if 'url' in task_response:
                embed.add_field(
                    name="🔗 Task URL",
                    value=f"[View in ClickUp]({task_response['url']})",
                    inline=True
                )
            
            # Add routing info in footer
            routing_info = "📋 Backlog" if "backlog" in clean_content.lower() else "🚀 Current Sprint"
            embed.set_footer(text=f"ClickUp Discord Bot • AI Context Analysis • Routed to: {routing_info}")
            
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
        title="🤖 ClickUp Discord Bot Help",
        description="I help you create ClickUp tasks directly from Discord using AI!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎯 How to use",
        value="Simply mention me (@bot) in any message with your task description, and I'll create a ClickUp task with an AI-generated title based on channel context!",
        inline=False
    )
    
    embed.add_field(
        name="💡 Example",
        value=f"@{bot.user.display_name if bot.user else 'bot'} Review the new authentication system",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Smart List Routing",
        value="• Include **'backlog'** in your message → Goes to Backlog list\n• No 'backlog' → Goes to newest Sprint list\n• Example: `@bot backlog Review docs` vs `@bot Fix login bug`",
        inline=False
    )
    
    embed.add_field(
        name="⚡ Commands",
        value="`!help` - Show this help message\n`!status` - Check bot status\n`!health` - Simple health check\n`!lists` - Show available lists",
        inline=False
    )
    
    embed.add_field(
        name="🧠 AI Features",
        value="• Smart title generation using OpenAI\n• Channel context analysis\n• Actionable task titles\n• Intelligent list routing",
        inline=False
    )
    
    embed.set_footer(text="ClickUp Discord Bot • Powered by OpenAI")
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status_command(ctx):
    """Check bot status"""
    embed = discord.Embed(
        title="📊 Bot Status",
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
    
    # Check OpenAI availability
    openai_status = "🟢 Connected" if os.getenv('OPENAI_API_KEY') else "🔴 Not configured"
    embed.add_field(
        name="OpenAI",
        value=openai_status,
        inline=True
    )
    
    # Check ClickUp availability
    clickup_status = "🟢 Connected" if os.getenv('CLICKUP_API_TOKEN') else "🔴 Not configured"
    embed.add_field(
        name="ClickUp",
        value=clickup_status,
        inline=True
    )
    
    # Check Sprint folder
    lists = clickup_client.get_folder_lists()
    folder_status = f"🟢 {len(lists)} lists" if lists else "🔴 No access"
    embed.add_field(
        name="Sprint Folder",
        value=folder_status,
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='lists')
async def lists_command(ctx):
    """Show available lists in sprint folder"""
    try:
        lists = clickup_client.get_folder_lists()
        
        if not lists:
            await ctx.send("❌ No lists found in sprint folder")
            return
        
        embed = discord.Embed(
            title="📋 Available Sprint Lists",
            description="Lists in the sprint folder (in ClickUp order):",
            color=discord.Color.blue()
        )
        
        # Limit to 10 lists for display, but remember which is the newest
        display_lists = lists[:10]
        newest_list_id = lists[-1].get('id') if lists else None  # ID of the actual newest list
        
        for i, list_item in enumerate(display_lists):
            list_name = list_item.get('name', 'Unknown')
            list_id = list_item.get('id', 'Unknown')
            
            # Mark the list that matches the newest list ID
            if list_id == newest_list_id:
                status_emoji = "🚀"
                status_text = " (NEWEST - TARGET)"
            else:
                status_emoji = "📝"
                status_text = ""
            
            embed.add_field(
                name=f"{status_emoji} {list_name}{status_text}",
                value=f"ID: `{list_id}`\nPosition: {i+1}/{len(lists)}",
                inline=True
            )
        
        # If we have more than 10 lists and the newest isn't shown
        if len(lists) > 10 and newest_list_id not in [lst.get('id') for lst in display_lists]:
            embed.add_field(
                name="⚠️ Note",
                value=f"Showing first 10 of {len(lists)} lists. Newest list ({lists[-1].get('name')}) is not shown but will be used for new tasks.",
                inline=False
            )
        
        embed.set_footer(text="🚀 = Current target for new tasks (last list in order)")
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error getting lists: {e}")
        await ctx.send(f"❌ Error getting lists: {e}")

@bot.command(name='health')
async def health_command(ctx):
    """Simple health check command"""
    await ctx.send('🏓 ping')

def main():
    """Main function to run the bot"""
    # Check required environment variables
    required_vars = ['DISCORD_BOT_TOKEN', 'CLICKUP_API_TOKEN', 'CLICKUP_LIST_ID']
    recommended_vars = ['OPENAI_API_KEY', 'CLICKUP_FOLDER_ID']
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    missing_recommended = [var for var in recommended_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file based on env.example")
        return
    
    if missing_recommended:
        logger.warning(f"Missing recommended environment variables: {', '.join(missing_recommended)}")
        logger.warning("Bot will work with limited features")
    
    try:
        bot.run(os.getenv('DISCORD_BOT_TOKEN'))
    except discord.LoginFailure:
        logger.error("Failed to login. Please check your Discord bot token.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 