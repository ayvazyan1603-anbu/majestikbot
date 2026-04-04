import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.welcome",
    "cogs.logs",
    "cogs.moderation",
    "cogs.music",
    "cogs.family",
]

@bot.event
async def on_ready():
    print(f"{bot.user} запущен")

@bot.event
async def on_command(ctx):
    print(f"[CMD] {ctx.author} → {ctx.message.content}")

@bot.event  
async def on_command_error(ctx, error):
    print(f"[ERR] {error}")
    
for cog in COGS:
    bot.load_extension(cog)

bot.run(os.getenv("TOKEN"))