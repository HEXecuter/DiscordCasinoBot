import nextcord
from nextcord.ext import commands
from games.blackjack import BlackJack
from models.model import engine
from models.model import User
from models.model import Games
from utils.helpers import get_user
from utils.helpers import send_error_message
from utils.helpers import send_response
from utils.helpers import get_active_game
from utils.helpers import register_new_game
from utils.helpers import format_money
from utils.helpers import charge_user
from utils.helpers import pay_user
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Union


class BlackjackCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command()
    async def blackjack(self, interaction: nextcord.Interaction):
        """
        Main command for blackjack related subcommands
        """
        pass

    @blackjack.subcommand()
    async def start(self, interaction: nextcord.Interaction, bet_amount: int = nextcord.SlashOption(min_value=1)):
        bet_amount = Decimal(bet_amount)
        await self.play_game(interaction, 'start', bet_amount)

    @blackjack.subcommand()
    async def double_down(self, interaction: nextcord.Interaction):
        await self.play_game(interaction, 'double down')

    @blackjack.subcommand()
    async def stand(self, interaction: nextcord.Interaction):
        await self.play_game(interaction, 'stand')

    @blackjack.subcommand()
    async def hit(self, interaction: nextcord.Interaction):
        await self.play_game(interaction, 'hit')

    async def play_game(self, interaction, action: str, bet_amount: Decimal = Decimal(0)):
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)
            user_not_exist: bool = user is None

            if user_not_exist:
                await send_error_message(interaction, 'Error Playing Blackjack Game',
                                         'You can not play any casino games before creating an account')
                return

            insufficient_funds = user.money < bet_amount
            if insufficient_funds:
                await send_error_message(interaction, 'Error Playing Blackjack Game',
                                         f'You are too broke to make this bet. '
                                         f'Come back when you have {format_money(bet_amount)}.')
                return

            game: Union[Games | None] = get_active_game(user, BlackJack.GAME_TYPE)
            if game is None and action != 'start':
                await send_error_message(interaction, 'Error Playing Blackjack Game',
                                         f'You do not have an active Blackjack game. '
                                         f'Start a Blackjack game before using this action.')
                return

            if action == 'start':
                if game is None:
                    await self.start_blackjack_game(interaction, user, bet_amount)
                    session.commit()
                    return
                else:
                    await self.send_game_state(interaction, BlackJack.from_json(game.game_state), user)
                    return

            blackjack_game = BlackJack.from_json(game.game_state)
            if action == 'double down':
                insufficient_funds = user.money < blackjack_game.state['bet_amount']
                if insufficient_funds:
                    await send_error_message(interaction, 'Error Doubling Down',
                                             f"You do not have enough money to double down. "
                                             f"Come back when you have {blackjack_game.state['bet_amount']}.")
                    return
                charge_user(user, blackjack_game.state['bet_amount'])
                blackjack_game.double_down()

            if action == 'hit':
                blackjack_game.hit_player()

            if action == 'stand':
                blackjack_game.stand()

            if blackjack_game.state['game_ended']:
                if blackjack_game.state['payout'] > Decimal(0.00):
                    pay_user(user, blackjack_game.state['payout'])
                session.delete(game)
            else:
                game.game_state = blackjack_game.serialize_to_json()
            await self.send_game_state(interaction, blackjack_game, user)
            session.commit()

    @staticmethod
    async def start_blackjack_game(interaction: nextcord.Interaction, user: User, bet_amount: Decimal):
        blackjack_game = BlackJack()
        charge_user(user, bet_amount)
        blackjack_game.start_game(bet_amount)
        register_new_game(user, BlackJack.GAME_TYPE, blackjack_game.serialize_to_json())
        await BlackjackCommands.send_game_state(interaction, blackjack_game, user)

    @staticmethod
    async def send_game_state(interaction: nextcord.Interaction, black_jack_game: BlackJack, user: User):
        if black_jack_game.state['game_ended']:
            response = nextcord.Embed(title=f"Bet Placed!", color=0x00e1ff)
            response.add_field(name=f"Bet Placed",
                               value=f"```\n{format_money(black_jack_game.state['bet_amount'])}\n```",
                               inline=True)
            response.add_field(name=f"Total Winnings",
                               value=f"```\n{format_money(black_jack_game.state['payout'])}\n```",
                               inline=True)
            response.add_field(name="Account Balance", value=f"```\n{format_money(user.money)}\n```", inline=False)

            await send_response(interaction, embed=response, file=nextcord.File(fp=black_jack_game.create_table_image(),
                                                                                filename='blackjack.png'))
        else:
            await send_response(interaction, file=nextcord.File(fp=black_jack_game.create_table_image(),
                                                                filename='blackjack.png'))
