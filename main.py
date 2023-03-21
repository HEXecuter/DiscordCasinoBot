from locale import setlocale
from locale import LC_ALL
from dotenv import load_dotenv
from os import getenv
import nextcord
from nextcord.ext import commands
from cogs.account import AccountManagement
from cogs.employment import Employment
from cogs.roulette_commands import RouletteCommands
from cogs.blackjack_commands import BlackjackCommands


load_dotenv()
TOKEN: str = getenv("CASINO_TOKEN")
DEBUG_ENABLED: bool = getenv("CASINO_DEBUG") == "TRUE"
LOCALE: str = getenv("CASINO_LOCALE")
INTENTS: nextcord.Intents = nextcord.Intents.default()

setlocale(LC_ALL, LOCALE)

bot: nextcord.ext.commands.bot.Bot = commands.Bot()
bot.add_cog(AccountManagement(bot))
bot.add_cog(Employment(bot))
bot.add_cog(RouletteCommands(bot))
bot.add_cog(BlackjackCommands(bot))
bot.run(TOKEN)
