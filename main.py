from locale import setlocale
from locale import currency
from locale import LC_ALL
from dotenv import load_dotenv
from os import getenv
import nextcord
from nextcord.ext import commands
from cogs.account import AccountManagement


load_dotenv()
TOKEN: str = getenv("CASINO_TOKEN")
DEBUG_ENABLED: bool = getenv("CASINO_DEBUG") == "TRUE"
LOCALE: str = getenv("CASINO_LOCALE")
INTENTS: nextcord.Intents = nextcord.Intents.default()

setlocale(LC_ALL, LOCALE)

bot: nextcord.ext.commands.bot.Bot = commands.Bot()
bot.add_cog(AccountManagement(bot))
bot.run(TOKEN)
