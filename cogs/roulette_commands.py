import nextcord
from typing import Union
from nextcord.ext import commands
from games.roulette import Roulette
from models.model import User
from models.model import Games
from models.model import engine
from utils.helpers import get_user
from utils.helpers import charge_user
from utils.helpers import pay_user
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

    @nextcord.slash_command()
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
        await self.place_bet(interaction, bet_type, Decimal(bet_amount))

    async def place_bet(self, interaction: nextcord.Interaction, bet_type: str, bet_amount: Decimal):
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)
            user_not_exist: bool = user is None

            if user_not_exist:
                await send_error_message(interaction, 'Error Making Roulette Bet',
                                         'You can not play any casino games before creating an account')
                return

            insufficient_funds = user.money < bet_amount
            if insufficient_funds:
                await send_error_message(interaction, 'Error Making Roulette Bet',
                                         f'You are too broke to make this bet. '
                                         f'Come back when you have {format_money(bet_amount)}.')
                return

            game: Union[Games | None] = get_active_game(user, Roulette.GAME_TYPE)
            if game is None:
                roulette_game = Roulette()
                game = register_new_game(user, Roulette.GAME_TYPE, roulette_game.serialize_to_json())
            else:
                roulette_game = Roulette.from_json(game.game_state)

            if bet_type in Roulette.TABLE_NUMBERS:
                roulette_game.add_inside_bet(bet_type, bet_amount)
            elif bet_type in Roulette.OUTSIDE_BETS:
                roulette_game.add_outside_bet(bet_type, bet_amount)

            charge_user(user, bet_amount)
            game.game_state = roulette_game.serialize_to_json()
            await self.send_bet_placed_response(interaction, roulette_game)
            session.commit()

    @staticmethod
    async def send_bet_placed_response(interaction: nextcord.Interaction, roulette_game: Roulette):
        # TODO: Change response to image with chips once functionality is added
        await send_response(interaction, file=nextcord.File(fp=roulette_game.create_table_image(),
                                                            filename='roulette bets.png'))

    @roulette.subcommand()
    async def inside_bet(self,
                         interaction: nextcord.Interaction,
                         roulette_number: int = nextcord.SlashOption(min_value=0, max_value=36),
                         bet_amount: int = nextcord.SlashOption(min_value=1)):
        """Use this command to place an ✨inside bet✨ on the roulette table

            Parameters
            _____________
            roulette_number: str
                The roulette number for this bet Ex: 1
            bet_amount: str
                The amount of money you want to place for this bet
        """
        await self.place_bet(interaction, str(roulette_number), Decimal(bet_amount))

    @roulette.subcommand()
    async def spin(self, interaction: nextcord.Interaction):
        """Use this command to spin the roulette and win some money!"""
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)

            user_not_exist: bool = user is None
            if user_not_exist:
                await send_error_message(interaction, 'Error Spinning Roulette',
                                         'You can not play any casino games before creating an account')
                return

            game: Union[Games | None] = get_active_game(user, Roulette.GAME_TYPE)
            if game is None:
                await send_error_message(interaction, 'Error Spinning Roulette',
                                         'You can not spin the roulette until you have placed a bet.')
                return

            roulette_game = Roulette.from_json(game.game_state)
            roulette_game.play()

            if roulette_game.payout > Decimal(0.00):
                pay_user(user, roulette_game.payout)
            session.delete(game)
            session.commit()
            await self.send_roulette_spin_response(interaction, user, roulette_game)

    @staticmethod
    async def send_roulette_spin_response(interaction: nextcord.Interaction, user: User, roulette: Roulette):
        response = nextcord.Embed(title="You have spun the roulette!")
        response.add_field(name=f"Number Rolled", value=f"```{roulette.tile_picked}\n```", inline=True)
        response.add_field(name=f"Total Bets Placed", value=f"```\n{format_money(roulette.bet_total)}\n```",
                           inline=True)
        response.add_field(name=f"Total Winnings", value=f"```\n{format_money(roulette.payout)}\n```",
                           inline=True)
        response.add_field(name="Account Balance", value=f"```\n{format_money(user.money)}\n```", inline=False)
        if len(roulette.bet_hits) > 0:
            description = '```'
            for bet_type, payout in roulette.bet_hits:
                description += f"Your bet on {bet_type} won you {format_money(payout)}.\n"
            description += '```'
        else:
            description = "```You didn't win anything this time.\n" \
                          "I'm sure you will win big time, if you bet this month's mortgage!\n```"
        response.description = description
        await send_response(interaction, embed=response)
