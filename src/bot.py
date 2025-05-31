import asyncio
import logging
import os
from datetime import datetime
from typing import List, Optional

import discord
from discord import app_commands
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

    def get_tasks_from_list(self, list_id: str) -> List[dict]:
        """Get all tasks from a specific list"""
        url = f"{self.base_url}/list/{list_id}/task"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("tasks", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get tasks from list {list_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return []
    
    def get_tasks_from_newest_sprint(self) -> List[dict]:
        """Get all tasks from the newest sprint list"""
        newest_list = self.get_newest_list_from_folder()
        if not newest_list:
            logger.warning("No newest sprint list found")
            return []
        
        list_id = newest_list.get('id')
        logger.info(f"Getting tasks from newest sprint: {newest_list.get('name')} (ID: {list_id})")
        return self.get_tasks_from_list(list_id)
    
    def update_task_status(self, task_id: str, status: str) -> dict:
        """Update task status in ClickUp"""
        url = f"{self.base_url}/task/{task_id}"
        
        task_data = {
            "status": status
        }
        
        try:
            response = requests.put(url, json=task_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update task status: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def assign_task(self, task_id: str, assignee_id: str) -> dict:
        """Assign a user to a ClickUp task"""
        url = f"{self.base_url}/task/{task_id}/assignee/{assignee_id}"

        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to assign task: {e}")
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
    folder_id=os.getenv('CLICKUP_FOLDER_ID')  # Sprint folder
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
        - The name of the task must be generic - if user sends an error message, the title has to be generalized
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
    try:
        await bot.tree.sync()
        logger.info("Slash commands synced")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")
    
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

async def is_task_creation_command(content: str) -> bool:
    """Use AI to determine if the message is a command to create a task rather than a task description"""
    content_cleaned = content.strip()
    
    # Handle empty content
    if not content_cleaned:
        return False
    
    # Quick heuristic for very obvious task descriptions (performance optimization)
    # If message is long and technical, it's likely a task description
    if len(content_cleaned.split()) > 10 and any(word in content_cleaned.lower() for word in ['implement', 'fix', 'create', 'update', 'review', 'add', 'remove', 'delete', 'bug', 'feature', 'system', 'api', 'database', 'interface']):
        return False
    
    # Use AI for intent analysis
    if not openai.api_key:
        logger.warning("OpenAI API key not available, falling back to simple heuristics")
        # Simple fallback: very short messages with task-related words are likely commands
        simple_command_words = ['task', 'taska', 'zadanie', 'backlog']
        return len(content_cleaned.split()) <= 3 and any(word in content_cleaned.lower() for word in simple_command_words)
    
    try:
        system_prompt = """You are an intent classifier for a Discord bot that creates tasks. Your job is to determine whether a user's message is:

1. A COMMAND to create a task (user wants bot to analyze context and create a task)
2. A TASK DESCRIPTION (user directly describes what the task should be about)

COMMAND examples:
- "dodaj taska" (Polish: add a task)
- "create task"
- "task this"
- "wrzuć do backlog" (Polish: put in backlog)
- "zapisz to" (Polish: save this)
- "task z tego" (Polish: task from this)
- "możesz stworzyć task?" (Polish: can you create a task?)
- "task please"
- "backlog this"

TASK DESCRIPTION examples:
- "Fix login bug with special characters"
- "Implement user authentication system"
- "Review the new authentication system"
- "Update API documentation"
- "Create tests for payment module"

Rules:
- If user is asking the bot to create a task without specifying what it should be about = COMMAND
- If user is directly describing what needs to be done = TASK DESCRIPTION
- Commands often contain meta-language about task creation
- Task descriptions contain specific technical details, actions, or deliverables
- Consider both Polish and English expressions
- When in doubt, lean towards TASK DESCRIPTION

Respond with only "COMMAND" or "TASK_DESCRIPTION"."""

        user_prompt = f'Analyze this message: "{content_cleaned}"'

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip().upper()
        
        is_command = result == "COMMAND"
        logger.info(f"AI intent analysis: '{content_cleaned}' -> {result} -> {'COMMAND' if is_command else 'TASK_DESCRIPTION'}")
        
        return is_command
        
    except Exception as e:
        logger.error(f"Error in AI intent analysis: {e}")
        # Fallback to simple heuristics
        simple_command_words = ['task', 'taska', 'zadanie', 'backlog', 'dodaj', 'stwórz', 'create', 'add']
        is_simple_command = len(content_cleaned.split()) <= 5 and any(word in content_cleaned.lower() for word in simple_command_words)
        logger.info(f"Fallback heuristic: '{content_cleaned}' -> {'COMMAND' if is_simple_command else 'TASK_DESCRIPTION'}")
        return is_simple_command

async def extract_task_from_context(message, command_content: str) -> tuple[str, str]:
    """Extract task information from channel context when a command is detected"""
    logger.info(f"Command detected: '{command_content}' - analyzing context for task content")
    
    # Get recent channel messages for context
    all_channel_messages = await get_channel_context(message.channel, limit=15)
    
    # Use AI to determine what task should be created from the context
    if not openai.api_key:
        logger.warning("OpenAI API key not available, using fallback method")
        return "Task from conversation context", "No AI analysis available"
    
    try:
        # Prepare context for AI analysis
        context_text = ""
        if all_channel_messages:
            context_text = "\n".join([
                f"{msg}" for msg in all_channel_messages
            ])
        
        system_prompt = """You are a smart task creation assistant. The user mentioned a bot with a command to create a task, but didn't specify what the task should be about. You need to analyze the recent conversation context to determine what task should be created.

Rules:
1. Look at the recent conversation context to understand what needs to be done
2. Create a clear, actionable task title and description
3. Focus on the most recent discussion topics or issues mentioned
4. If there are multiple possible tasks, pick the most recent or urgent one
5. If the context doesn't provide clear task material, create a task about following up on the discussion

Return your response in this format:
TITLE: [Clear, actionable task title]
DESCRIPTION: [Brief description of what needs to be done based on context]"""

        user_prompt = f"""The user said: "{command_content}"

Recent conversation context:
{context_text}

What task should be created based on this context?"""

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        logger.info(f"AI task analysis: {ai_response}")
        
        # Parse the AI response
        lines = ai_response.split('\n')
        title = "Task from conversation context"
        description = command_content
        
        for line in lines:
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                description = line.replace('DESCRIPTION:', '').strip()
        
        return title, description
        
    except Exception as e:
        logger.error(f"Error analyzing context with AI: {e}")
        # Fallback: use command content
        return "Task from conversation context", command_content

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
            
            # Check if this is a command to create a task vs. a task description
            is_command = await is_task_creation_command(clean_content)
            
            if is_command:
                # Extract task from context using AI
                logger.info("Detected task creation command - analyzing context")
                task_name, task_description_from_context = await extract_task_from_context(message, clean_content)
                
                # For commands, we use the AI-generated title directly and don't need additional title generation
                final_task_name = task_name
                task_input_content = task_description_from_context
            else:
                # This is a regular task description
                task_input_content = clean_content
                final_task_name = None  # Will be generated later
            
            # Determine target list based on message content
            target_list_id, list_description = determine_target_list(clean_content)
            logger.info(f"Target list: {list_description} (ID: {target_list_id})")
            
            # Get channel context for smarter title generation (if needed)
            logger.info("Getting channel context...")
            all_channel_messages = await get_channel_context(message.channel, limit=20)
            
            # Filter for relevant context using AI
            logger.info("Filtering relevant context with AI...")
            relevant_context = await filter_relevant_context(task_input_content, all_channel_messages)
            
            # Generate smart title using OpenAI with filtered context (only if not already generated)
            if final_task_name is None:
                logger.info("Generating smart title with relevant context...")
                final_task_name = await generate_smart_title(task_input_content, relevant_context)
            else:
                logger.info(f"Using AI-generated title from context analysis: {final_task_name}")
            
            # Prepare context summary for task description
            context_summary = ""
            if relevant_context:
                context_summary = f"\n\n**Relevant Context from Channel:**\n"
                context_summary += "\n".join([f"• {msg}" for msg in relevant_context])
            elif all_channel_messages:
                context_summary = f"\n\n**Note:** AI found no relevant context in recent {len(all_channel_messages)} messages"
            
            # Different description format for commands vs direct descriptions
            if is_command:
                original_message_section = f"**Command:** {clean_content}\n**Extracted from context:** {task_description_from_context}"
            else:
                original_message_section = f"**Original Message:** {clean_content}"
            
            task_description = f"""
**Task created from Discord**

{original_message_section}

**Target List:** {list_description}
**Author:** {message.author.display_name} ({message.author.name}#{message.author.discriminator})
**Channel:** #{message.channel.name}
**Guild:** {message.guild.name if message.guild else 'DM'}
**Timestamp:** {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Message Link:** {message.jump_url}{context_summary}
            """.strip()
            
            # Create the task in ClickUp
            logger.info(f"Creating task with title: {final_task_name}")
            task_response = clickup_client.create_task(
                name=final_task_name,
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
                value=final_task_name,
                inline=False
            )
            
            if is_command:
                embed.add_field(
                    name="📝 Command Detected",
                    value=f"Command: `{clean_content}`\nExtracted from context: {task_description_from_context[:100]}{'...' if len(task_description_from_context) > 100 else ''}",
                    inline=False
                )
            else:
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
            creation_method = "🎯 Smart Command" if is_command else "📝 Direct Description"
            embed.set_footer(text=f"ClickUp Discord Bot • {creation_method} • Routed to: {routing_info}")
            
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

def normalize_status(status_input: str) -> Optional[str]:
    """Normalize status input to valid ClickUp status"""
    status_mapping = {
        "todo": "to do",
        "to do": "to do", 
        "backlog": "to do",
        "start": "in progress",
        "started": "in progress",
        "progress": "in progress",
        "in progress": "in progress",
        "working": "in progress",
        "review": "in review",
        "in review": "in review",
        "reviewing": "in review",
        "done": "complete",
        "complete": "complete",
        "completed": "complete",
        "finished": "complete",
        "close": "complete",
        "closed": "complete",
        "resolved": "complete",
        "fixed": "complete"
    }
    
    normalized = status_input.lower().strip()
    return status_mapping.get(normalized)

async def find_similar_task(task_description: str, tasks: List[dict]) -> Optional[dict]:
    """Use AI to find the most similar task based on semantic similarity"""
    if not tasks or not openai.api_key:
        return None
    
    try:
        # Prepare task list for AI analysis
        task_list = []
        for i, task in enumerate(tasks):
            task_name = task.get('name', 'Unnamed Task')
            task_desc = task.get('description', '')
            # Clean description from markdown/formatting
            clean_desc = task_desc.replace('**', '').replace('*', '').replace('\n', ' ')[:200]
            
            task_info = f"{i+1}. {task_name}"
            if clean_desc.strip():
                task_info += f" - {clean_desc}"
            task_list.append(task_info)
        
        tasks_text = "\n".join(task_list)
        
        system_prompt = """You are a task matching assistant. Given a task description and a list of existing tasks, find the most semantically similar task.

Rules:
- Look for semantic similarity, not just exact word matches
- Consider synonyms, related concepts, and context
- Focus on the main purpose/goal of the task
- If no task is reasonably similar, return "none"
- Return only the number of the most similar task (e.g., "3")"""

        user_prompt = f"""Find the most similar task to: "{task_description}"

Available tasks:
{tasks_text}

Which task number is most similar? Return only the number or "none":"""

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=20,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        if result == "none":
            logger.info("AI found no similar tasks")
            return None
        
        try:
            task_index = int(result) - 1
            if 0 <= task_index < len(tasks):
                selected_task = tasks[task_index]
                logger.info(f"AI selected task: {selected_task.get('name')} (confidence: semantic match)")
                return selected_task
            else:
                logger.warning(f"AI returned invalid task index: {result}")
                return None
                
        except ValueError:
            logger.warning(f"Could not parse AI response: {result}")
            return None
        
    except Exception as e:
        logger.error(f"Error finding similar task: {e}")
        return None

async def match_member_by_name(name_query: str, members: List[discord.Member]) -> Optional[discord.Member]:
    """Use AI to match an approximate name to a guild member"""
    if not members:
        return None

    # Fallback to simple substring search when OpenAI is unavailable
    if not openai.api_key:
        for member in members:
            if name_query.lower() in member.display_name.lower() or name_query.lower() in member.name.lower():
                return member
        return None

    try:
        name_list = "\n".join([f"{i+1}. {m.display_name}" for i, m in enumerate(members)])
        system_prompt = (
            "You are a helpful assistant that matches a provided name to the best discord user from a list. "
            "Return only the number of the best match or 'none' if no good match."
        )
        user_prompt = (
            f"Available users:\n{name_list}\n\n"
            f"Find the best match for '{name_query}'. Return the number or 'none'."
        )

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            max_tokens=10,
            temperature=0.1,
        )
        result = response.choices[0].message.content.strip().lower()
        if result == "none":
            return None

        index = int(result) - 1
        if 0 <= index < len(members):
            return members[index]
    except Exception as e:
        logger.error(f"Error matching member name: {e}")

    return None

def parse_update_command(command_text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse !update command to extract task description and status
    
    Examples:
    - "!update integracja bota z clickupem review" -> ("integracja bota z clickupem", "review")
    - "!update fix login bug in progress" -> ("fix login bug", "in progress")
    - "!update dokumentacja closed" -> ("dokumentacja", "closed")
    
    Returns:
        tuple: (task_description, status) or (None, None) if parsing fails
    """
    # Remove the !update prefix
    content = command_text.replace('!update', '').strip()
    
    if not content:
        return None, None
    
    # Valid status keywords (order matters - longer phrases first)
    valid_statuses = ["in progress", "in review", "to do", "todo", "review", "progress", "done", "complete", "closed", "resolved", "fixed"]
    
    # Find status at the end of the command
    found_status = None
    task_description = content
    
    for status in valid_statuses:
        if content.lower().endswith(status.lower()):
            found_status = status.lower()
            # Remove status from task description
            task_description = content[:-len(status)].strip()
            break
    
    if not found_status:
        return None, None
    
    # Normalize the status
    normalized_status = normalize_status(found_status)
    
    return task_description, normalized_status

@bot.tree.command(name="update", description="Update task status using AI semantic matching")
@app_commands.describe(task_description="Task description to match", status="New task status")
async def update_command(interaction: discord.Interaction, task_description: str, status: str):
    """Update task status using AI semantic matching"""
    await interaction.response.defer()

    new_status = normalize_status(status)
    if not new_status:
        embed = discord.Embed(
            title="❌ Invalid Status",
            description="Please provide a valid status.",
            color=discord.Color.red()
        )
        embed.add_field(name="Valid Statuses", value="`to do`, `in progress`, `in review`, `closed`", inline=False)
        await interaction.followup.send(embed=embed)
        return

    if not task_description:
        await interaction.followup.send("❌ Please provide a task description")
        return

    try:
        # Send typing indicator
        async with interaction.channel.typing():
            # Get tasks from newest sprint
            logger.info(f"Looking for tasks similar to: '{task_description}' with status: '{new_status}'")
            tasks = clickup_client.get_tasks_from_newest_sprint()
            
            if not tasks:
                embed = discord.Embed(
                    title="❌ No Tasks Found",
                    description="No tasks found in the newest sprint list.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            logger.info(f"Found {len(tasks)} tasks in newest sprint")
            
            # Find similar task using AI
            similar_task = await find_similar_task(task_description, tasks)
            
            if not similar_task:
                embed = discord.Embed(
                    title="❌ No Similar Task Found",
                    description=f"Could not find a task similar to: '{task_description}'",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Available Tasks",
                    value=f"Found {len(tasks)} tasks in newest sprint.",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Update task status
            task_id = similar_task.get('id')
            task_name = similar_task.get('name')
            current_status = similar_task.get('status', {}).get('status', 'Unknown')
            
            logger.info(f"Updating task '{task_name}' (ID: {task_id}) from '{current_status}' to '{new_status}'")
            
            update_response = clickup_client.update_task_status(task_id, new_status)
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Task Updated Successfully!",
                description=f"Found and updated the most similar task using AI semantic matching.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🔍 Search Query",
                value=task_description,
                inline=False
            )
            
            embed.add_field(
                name="🎯 Matched Task",
                value=task_name,
                inline=False
            )
            
            embed.add_field(
                name="📊 Status Change",
                value=f"`{current_status}` → `{new_status}`",
                inline=True
            )
            
            embed.add_field(
                name="🆔 Task ID",
                value=task_id,
                inline=True
            )
            
            if 'url' in similar_task:
                embed.add_field(
                    name="🔗 Task URL",
                    value=f"[View in ClickUp]({similar_task['url']})",
                    inline=True
                )
            
            embed.set_footer(text="ClickUp Discord Bot • AI Task Matching")
            await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"Error updating task: {e}")

        error_embed = discord.Embed(
            title="❌ Error Updating Task",
            description=f"Sorry, I encountered an error: {str(e)}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        await interaction.followup.send(embed=error_embed)


@bot.tree.command(name="assign", description="Assign a user to a task using AI name matching")
@app_commands.describe(task_description="Description of the task to match", member_name="Approximate member name")
async def assign_command(interaction: discord.Interaction, task_description: str, member_name: str):
    """Assign a Discord member to the most similar ClickUp task"""
    await interaction.response.defer()

    try:
        tasks = clickup_client.get_tasks_from_newest_sprint()
        if not tasks:
            await interaction.followup.send("❌ No tasks found in the newest sprint list")
            return

        similar_task = await find_similar_task(task_description, tasks)
        if not similar_task:
            await interaction.followup.send(f"❌ Could not find a task similar to: '{task_description}'")
            return

        member = await match_member_by_name(member_name, interaction.guild.members)
        if not member:
            await interaction.followup.send(f"❌ Could not find a member matching '{member_name}'")
            return

        clickup_client.assign_task(similar_task['id'], str(member.id))

        embed = discord.Embed(
            title="✅ Task Assigned",
            description=f"Assigned **{member.display_name}** to **{similar_task.get('name')}**",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )
        if 'url' in similar_task:
            embed.add_field(name="🔗 Task URL", value=f"[View in ClickUp]({similar_task['url']})", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"Error assigning task: {e}")
        await interaction.followup.send(f"❌ Error assigning task: {e}")

@bot.tree.command(name="tasks", description="Show all tasks from newest sprint list")
async def tasks_command(interaction: discord.Interaction):
    """Show all tasks from newest sprint list"""
    try:
        await interaction.response.defer()
        tasks = clickup_client.get_tasks_from_newest_sprint()
        
        if not tasks:
            await interaction.followup.send("❌ No tasks found in newest sprint list")
            return
        
        # Get newest list info
        newest_list = clickup_client.get_newest_list_from_folder()
        list_name = newest_list.get('name', 'Unknown') if newest_list else 'Unknown'
        
        embed = discord.Embed(
            title=f"📋 Tasks in {list_name}",
            description=f"Found {len(tasks)} tasks:",
            color=discord.Color.blue()
        )
        
        # Limit to 10 tasks for display
        display_tasks = tasks[:10]
        
        for i, task in enumerate(display_tasks):
            task_name = task.get('name', 'Unnamed Task')
            task_status = task.get('status', {}).get('status', 'No Status')
            task_id = task.get('id', 'Unknown')
            
            embed.add_field(
                name=f"{i+1}. {task_name[:50]}{'...' if len(task_name) > 50 else ''}",
                value=f"Status: `{task_status}`\nID: `{task_id}`",
                inline=True
            )
        
        if len(tasks) > 10:
            embed.add_field(
                name="⚠️ Note",
                value=f"Showing first 10 of {len(tasks)} tasks",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        await interaction.followup.send(f"❌ Error getting tasks: {e}")

@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="🤖 ClickUp Discord Bot Help",
        description="I help you create and manage ClickUp tasks directly from Discord using AI!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎯 Create Tasks",
        value="Simply mention me (@bot) in any message with your task description, and I'll create a ClickUp task with an AI-generated title based on channel context!",
        inline=False
    )
    
    embed.add_field(
        name="💡 Create Example",
        value=f"@{bot.user.display_name if bot.user else 'bot'} Review the new authentication system",
        inline=False
    )
    
    embed.add_field(
        name="🔄 Update Tasks",
        value="Use `/update` with task description and status to update similar tasks using AI semantic matching.",
        inline=False
    )

    embed.add_field(
        name="🔄 Update Examples",
        value="`/update integracja bota review`\n`/update fix login bug in progress`\n`/update dokumentacja api closed`",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Smart List Routing",
        value="• Include **'backlog'** in your message → Goes to Backlog list\n• No 'backlog' → Goes to newest Sprint list\n• Example: `@bot backlog Review docs` vs `@bot Fix login bug`",
        inline=False
    )
    
    embed.add_field(
        name="⚡ Commands",
        value="`/help` - Show this help message\n`/update` - Update task status with AI matching\n`/tasks` - Show tasks in newest sprint\n`/status` - Check bot status\n`/health` - Simple health check\n`/lists` - Show available lists\n`/assign` - Assign user to task",
        inline=False
    )
    
    embed.add_field(
        name="📊 Valid Statuses",
        value="`to do`, `in progress`, `in review`, `closed`",
        inline=False
    )
    
    embed.add_field(
        name="🧠 AI Features",
        value="• Smart title generation using OpenAI\n• Semantic task matching\n• Channel context analysis\n• Intelligent list routing",
        inline=False
    )
    
    embed.set_footer(text="ClickUp Discord Bot • Powered by OpenAI")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Check bot status")
async def status_command(interaction: discord.Interaction):
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
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="lists", description="Show available lists in sprint folder")
async def lists_command(interaction: discord.Interaction):
    """Show available lists in sprint folder"""
    try:
        await interaction.response.defer()
        lists = clickup_client.get_folder_lists()
        
        if not lists:
            await interaction.followup.send("❌ No lists found in sprint folder")
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
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error getting lists: {e}")
        await interaction.followup.send(f"❌ Error getting lists: {e}")

@bot.tree.command(name="health", description="Simple health check")
async def health_command(interaction: discord.Interaction):
    """Simple health check command"""
    await interaction.response.send_message('🏓 ping')

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