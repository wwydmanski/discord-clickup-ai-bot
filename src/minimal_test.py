import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

@bot.command()
async def test(ctx):
    await ctx.send('Test działa!')

@bot.command()
async def health(ctx):
    await ctx.send('ping')

@bot.event
async def on_ready():
    print(f'{bot.user} połączony!')
    print(f'Zarejestrowane komendy: {[cmd.name for cmd in bot.commands]}')

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_BOT_TOKEN')) 