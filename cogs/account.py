from typing import Union
from datetime import datetime
import nextcord
from nextcord.ext import commands
from models.model import engine
from models.model import User
from models.model import Pet
from models.model import MONEY_DEFAULT
from models.model import PET_PRICE_DEFAULT
from sqlalchemy.orm import Session
from utils.helpers import get_user
from utils.helpers import format_money
from utils.helpers import get_multipliers
from utils.helpers import send_response
from utils.helpers import send_error_message
from decimal import Decimal
from random import randint


class AccountManagement(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command()
    async def create_account(
            self, interaction: nextcord.Interaction,
            pet_name: str = nextcord.SlashOption(min_length=2, max_length=32)):
        """Use this command to get started, include your pet's name to stay ✨motivated✨ 🙈 😉

        Parameters
        _____________
        pet_name: str
            The name of your ✨adorable✨ pet 😉
        """
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)
            user_not_exist: bool = user is None
            if user_not_exist:
                self.create_user(session, interaction.user.id, interaction.guild.id, pet_name)
                await self.send_welcome_message(interaction, pet_name)
                session.commit()
                return
            else:
                await send_error_message(interaction, 'Error Creating Account', 'Your account already exists')
                return

    @staticmethod
    def create_user(session: Session, discord_id: int, guild_id: int, pet_name):
        new_user: User = User(discord_id=discord_id, guild_id=guild_id)
        new_user.pet = Pet(current_owner_id=None, name=pet_name)
        session.add(new_user)

    @staticmethod
    async def send_welcome_message(interaction: nextcord.Interaction, pet_name: str):
        response = nextcord.Embed(title="Welcome to CasinoBot!", color=0x00e1ff)
        response.add_field(name="Date you joined Discord",
                           value=f"```\n{interaction.user.created_at.strftime('%m/%d/%Y')}\n```", inline=True)
        response.add_field(name="Date you joined CasinoBot",
                           value=f"```\n{datetime.now().strftime('%m/%d/%Y')}\n```", inline=True)
        response.add_field(name="Date _̷̱̃_̷̲̆  ̸̱̔_̴͇̉ ̴̭͠_̶_̦̎ _̵͔̿_̶̪́ ̴̵̳͌͝?̟",
                           value=f"```\n{randint(1, 12):02}/{randint(1, 28):02}/2̶̺̘̈͊0̷̢̎̀?̷̘̅?̸̢͓͘\n```", inline=True)
        # response.set_thumbnail(bot.user.avatar.url)
        response.description = \
            f"```Hello {interaction.user.display_name},\n" \
            f"Since you do not have any money, I have deposited {format_money(Decimal(MONEY_DEFAULT))} into " \
            f"your account. My generosity is not free, so I have also kidnapped your pet, {pet_name}. I do " \
            f"charge interest, so you will have to pay me back {format_money(Decimal(PET_PRICE_DEFAULT))}. " \
            f"Hurry before someone else buys {pet_name} from me!\n```"
        await send_response(interaction, embed=response)

    @nextcord.slash_command()
    async def view_account(self, interaction: nextcord.Interaction, member: nextcord.Member):
        """Use this command to get information on someone's account

        Parameters
        _____________
        user:
            User's account you want to see
        """
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, member.id, member.guild.id)
            user_exists = user is not None
            if user_exists:
                await self.send_account_info(interaction, user, member.display_name)
            else:
                await send_error_message(interaction, 'Error Querying Account',
                                         f'{member.display_name} has not created an account yet.')

    @staticmethod
    async def send_account_info(interaction: nextcord.Interaction, user: User, display_name: str):
        has_job: bool = user.job is not None

        response = nextcord.Embed(title=f"{display_name} Account Info", color=0x00e1ff)

        response.add_field(name=f"Pet Name", value=f"```\n{user.pet.name}\n```", inline=True)
        if user.pet.current_owner is None:
            pet_status = '```\nKidnapped by Bot\n```'
        elif user.pet.current_owner is user:
            pet_status = '```\nSafe\n```'
        else:
            pet_status = f'Kidnapped by @<{user.pet.current_owner.discord_id}>'
        response.add_field(name=f"Pet Status", value=pet_status, inline=True)

        if has_job:
            response.add_field(name=f"Job Title", value=f"```\n{user.job.title}\n```", inline=False)
            response.add_field(name=f"Company Name", value=f"```\n{user.job.company}\n```", inline=False)
        else:
            response.add_field(name=f"Job Title", value=f"```\nUnemployed\n```", inline=False)
            response.add_field(name=f"Company Name", value=f"```\nUnemployed\n```", inline=False)
        response.add_field(name=f"Account Balance", value=f"```\n{format_money(user.money)}\n```", inline=True)

        total_multipliers: Decimal = get_multipliers(user)
        response.add_field(name=f"Paycheck Multiplier", value=f"```\n{total_multipliers:.0%}\n```", inline=True)

        await send_response(interaction, embed=response)
