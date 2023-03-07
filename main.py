from dotenv import load_dotenv
from os import getenv
import nextcord
from nextcord.ext import commands


load_dotenv()
TOKEN: str = getenv("DISCORD_TOKEN")
DEBUG_ENABLED: bool = getenv("CASINO_DEBUG") == "TRUE"
INTENTS: nextcord.Intents = nextcord.Intents.default()

bot = commands.Bot()

bot.run(TOKEN)
