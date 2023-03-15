import nextcord
from typing import Union
from nextcord.ext import commands
from games.roulette import Roulette
from models.model import User
from models.model import Games
from models.model import engine
from utils.helpers import get_user
from utils.helpers import charge_user
from utils.helpers import send_error_message
from utils.helpers import send_response
from utils.helpers import get_active_game
from utils.helpers import format_money
from utils.helpers import register_new_game
from sqlalchemy.orm import Session
from decimal import Decimal


class RouletteCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(guild_ids=[868296265564319774])
    async def roulette(self, interaction: nextcord.Interaction):
        """
        Main command for roulette related subcommands
        """
        pass

    @roulette.subcommand()
    async def outside_bet(self,
                          interaction: nextcord.Interaction,
                          bet_type: str = nextcord.SlashOption(choices=Roulette.OUTSIDE_BETS),
                          bet_amount: int = nextcord.SlashOption(min_value=1)):
        """Use this command to place an ✨outside bet✨ on the roulette table

            Parameters
            _____________
            bet_type: int
                The type of outside bet you want to make Ex: first dozen
            bet_amount: str
                The amount of money you want to place for this bet
        """
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)
            user_not_exist: bool = user is None
            bet_amount = Decimal(bet_amount)

            if user_not_exist:
                await send_error_message(interaction, 'Error Playing Roulette',
                                         'You can not play any casino games before creating an account')
                return

            insufficient_funds = user.money < bet_amount
            if insufficient_funds:
                await send_error_message(interaction, 'Error Purchasing Degree',
                                         f'You are too broke to make this bet. '
                                         f'Come back when you have {format_money(bet_amount)}.')
                return

            game: Union[Games | None] = get_active_game(user, Roulette.GAME_TYPE)
            if game is None:
                roulette_game = Roulette()
                game = register_new_game(user, Roulette.GAME_TYPE, roulette_game.serialize_to_json())
            else:
                roulette_game = Roulette.from_json(game.game_state)

            roulette_game.add_outside_bet(bet_type, bet_amount)
            charge_user(user, bet_amount)
            game.game_state = roulette_game.serialize_to_json()
            await self.send_bet_placed_response(interaction, roulette_game)
            session.commit()

    @staticmethod
    async def send_bet_placed_response(interaction: nextcord.Interaction, game: Games):
        # TODO: Change response to image with chips once functionality is added
        await send_response(interaction, content=str(game))
