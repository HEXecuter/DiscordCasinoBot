from typing import Union
from datetime import datetime
import nextcord
from nextcord.ext import commands
from models.model import engine
from models.model import User
from models.model import MONEY_DEFAULT
from sqlalchemy.orm import Session
from utils.database import get_user
from utils.database import format_money
from utils.database import get_multipliers
from decimal import Decimal
from random import randint

PET_PRICE = Decimal('100000')


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
                self.create_user(session, interaction.user.id, interaction.guild.id)
                await self.send_welcome_message(interaction, pet_name)
                session.commit()
                return
            else:
                await self.send_error_message(interaction, 'Error Creating Account', 'Your account already exists')

    @staticmethod
    def create_user(session: Session, discord_id: int, guild_id: int):
        session.add(User(discord_id=discord_id, guild_id=guild_id))

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
            f"charge interest, so you will have to pay me back {format_money(PET_PRICE)}. Hurry before someone " \
            f"else buys {pet_name} from me!\n```"
        if interaction.response.is_done():
            await interaction.followup.send(embed=response)
        else:
            await interaction.response.send_message(embed=response)

    @staticmethod
    async def send_error_message(interaction: nextcord.Interaction, error_title: str, error_message: str):
        response = nextcord.Embed(title=error_title, color=0xf50202)
        response.description = f'```{error_message}\n```'
        if interaction.response.is_done():
            await interaction.followup.send(embed=response)
        else:
            await interaction.response.send_message(embed=response)

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
                await self.send_error_message(interaction, 'Error Querying Account',
                                              f'{member.display_name} has not created an account yet.')

    @staticmethod
    async def send_account_info(interaction: nextcord.Interaction, user: User, display_name: str):
        has_job: bool = user.job is not None
        has_multipliers: bool = len(user.multipliers) > 0

        response = nextcord.Embed(title=f"{display_name} Account Info", color=0x00e1ff)
        # TODO: Add fields for pet info
        # response.add_field(name=f"{target_obj.pet_name} Status", value=f"```\n{target_obj.pet_status}\n```",
        #                    inline=True)
        # response.add_field(name=f"{target_obj.pet_name} Owner", value=f"<@{target_obj.pet_owner}>", inline=True)
        if has_job:
            response.add_field(name=f"Job Title", value=f"```\n{user.job.title}\n```", inline=False)
            response.add_field(name=f"Company Name", value=f"```\n{user.job.company}\n```", inline=False)
        else:
            response.add_field(name=f"Job Title", value=f"```\nUnemployed\n```", inline=False)
            response.add_field(name=f"Company Name", value=f"```\nUnemployed\n```", inline=False)
        response.add_field(name=f"Account Balance", value=f"```\n{format_money(user.money)}\n```", inline=True)
        if has_multipliers:
            total_multipliers: Decimal = get_multipliers(Session.object_session(user), user.id)
            response.add_field(name=f"Paycheck Multiplier", value=f"```\n{total_multipliers:.0%}\n```", inline=True)

        if interaction.response.is_done():
            await interaction.followup.send(embed=response)
        else:
            await interaction.response.send_message(embed=response)
