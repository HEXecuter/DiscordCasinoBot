import nextcord
from nextcord.ext import commands


class BlackjackCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command()
    async def blackjack(self, interaction: nextcord.Interaction):
        """
        Main command for blackjack related subcommands
        """
        pass
