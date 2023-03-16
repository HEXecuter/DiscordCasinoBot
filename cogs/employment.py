import nextcord
from typing import Union
from nextcord.ext import commands
from models.model import User
from models.model import Job
from models.model import Multipliers
from models.model import engine
from sqlalchemy.orm import Session
from utils.helpers import get_user
from utils.helpers import pay_user
from utils.helpers import charge_user
from utils.helpers import send_error_message
from utils.helpers import send_response
from utils.helpers import format_money
from utils.helpers import format_timedelta
from utils.helpers import get_multipliers
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

PAYCHECK_INTERVAL: timedelta = timedelta(hours=1)
BASE_PAY: Decimal = Decimal('100')


class Employment(commands.Cog):
    degrees = {
        'bachelors': {
            'price': Decimal("1000"),
            'stat': Decimal("1.25"),
            'friendly_name': 'Bachelors Degree'
        },
        'phd': {
            'price': Decimal("2000"),
            'stat': Decimal("3"),
            'friendly_name': 'PhD'
        },
        'bootcamp': {
            'price': Decimal("750"),
            'stat': 0.75,
            'friendly_name': 'Bootcamp Certification of Completion'
        }
    }

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command()
    async def job(self, interaction: nextcord.Interaction):
        """Main command for job related subcommands"""
        pass

    @job.subcommand()
    async def apply(self, interaction: nextcord.Interaction,
                    job_title: str = nextcord.SlashOption(min_length=5, max_length=32),
                    company_name: str = nextcord.SlashOption(min_length=5, max_length=32)):
        """use this command to apply for your ✨first and only job✨

        Parameters
        _____________
        job_title: str
            Your desired job title Ex: Professional Pizza Maker
        company_name: str
            The name of the company you want to apply to
        """
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)
            user_not_exist: bool = user is None

            if user_not_exist:
                await send_error_message(interaction, 'Error Applying for Job',
                                         'You can not apply for a job before creating an account')
                return

            self.create_job(user, job_title, company_name)
            await self.send_job_response(interaction, user)
            session.commit()

    @staticmethod
    def create_job(user: User, job_title: str, company_name: str):
        # If a user already has a job, keep the same paycheck date, so they do not reset paycheck cooldown
        if user.job:
            user.job.title = job_title
            user.job.company = company_name
        else:
            user.job = Job(title=job_title, company=company_name)

    @staticmethod
    async def send_job_response(interaction: nextcord.Interaction, user: User):
        response = nextcord.Embed(title="Congratulations on the New Job!", color=0x00e1ff)
        response.description = f"```\nCongratulations {interaction.user.display_name},\n" \
                               f"The hiring manager got confused and hired the wrong person! " \
                               f"Thanks to their mistake, you are now the {user.job.title} at {user.job.company}. " \
                               f"Don't forget to get your paycheck! You can also \"study hard\" and pay " \
                               f"for certifications and degrees that increase your salary.\n```"
        response.add_field(name=f"Job Title", value=f"```\n{user.job.title}\n```", inline=False)
        response.add_field(name=f"Company Name", value=f"```\n{user.job.company}\n```", inline=False)
        await send_response(interaction, embed=response)

    @job.subcommand()
    async def paycheck(self, interaction: nextcord.Interaction):
        """Use this command to ✨get paid✨ daily"""
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)

            user_not_exist: bool = user is None
            if user_not_exist:
                await send_error_message(interaction, 'Error Receiving Paycheck',
                                         'You can not receive a paycheck if you do not have an account')
                return

            user_is_unemployed = user.job is None
            if user_is_unemployed:
                await send_error_message(interaction, 'Error Receiving Paycheck',
                                         'You can not receive a paycheck if you do not have a job')
                return

            next_paycheck: datetime = user.job.paycheck_redeemed + PAYCHECK_INTERVAL
            utc_time_now: datetime = datetime.utcnow()
            time_difference: timedelta = next_paycheck - utc_time_now
            paycheck_not_available = utc_time_now < next_paycheck
            if paycheck_not_available:
                await send_error_message(interaction, 'Error Receiving Paycheck',
                                         f'You must wait {format_timedelta(time_difference)} '
                                         f'for your next paycheck.')
                return

            multipliers: Decimal = get_multipliers(user)
            paycheck_amount: Decimal = multipliers * BASE_PAY
            pay_user(user, paycheck_amount)
            user.job.paycheck_redeemed = utc_time_now
            await self.send_paycheck_response(interaction, user, paycheck_amount, multipliers)
            session.commit()

    @staticmethod
    async def send_paycheck_response(interaction: nextcord.Interaction, user: User, amount: Decimal,
                                     multipliers: Decimal):
        response = nextcord.Embed(title="You Have Received Your Paycheck!")
        response.add_field(name=f"Total Comp", value=f"```\n{format_money(amount)}\n```", inline=True)
        response.add_field(name=f"Degree Modifiers", value=f"```\n{multipliers:.0%}\n```",
                           inline=True)
        response.add_field(name="Account Balance", value=f"```\n{format_money(user.money)}\n```", inline=False)
        response.add_field(name=f"Job Title", value=f"```\n{user.job.title}\n```", inline=False)
        response.add_field(name=f"Company Name", value=f"```\n{user.job.company}\n```", inline=False)
        await send_response(interaction, embed=response)

    @nextcord.slash_command()
    async def purchase_degree(self, interaction: nextcord.Interaction,
                              degree_type: str = nextcord.SlashOption(choices=degrees.keys()),
                              field: str = nextcord.SlashOption(min_length=5, max_length=32),
                              amount: int = nextcord.SlashOption(min_value=1, max_value=100)):
        """Use this command to ✨bribe✨ a school official into giving you a degree

        Parameters
        _____________
        degree_type:
            Choose from the list of options, more expensive degrees provide better returns
        field:
            The field you want to major in Ex: Twitter Argument De-escalation
        amount:
            The amount of degrees you want to purchase
        """
        with Session(engine) as session:
            user: Union[User | None] = get_user(session, interaction.user.id, interaction.guild.id)
            total_cost: Decimal = Employment.degrees[degree_type]['price'] * amount
            total_multiplier: Decimal = Employment.degrees[degree_type]['stat'] * amount
            degree_name: str = Employment.degrees[degree_type]['friendly_name'] + ("s" if amount == 1 else '')

            user_not_exist: bool = user is None
            if user_not_exist:
                await send_error_message(interaction, 'Error Purchasing Degree',
                                         'You can not purchase a degree before creating an account')
                return

            insufficient_funds: bool = user.money < total_cost
            if insufficient_funds:
                await send_error_message(interaction, 'Error Purchasing Degree',
                                         f'You are too broke to buy {amount} {degree_name} in {field}. '
                                         f'Come back when you have {format_money(total_cost)}.')
                return

            charge_user(user, total_cost)
            self.create_multiplier(user, total_multiplier, amount, degree_type, field)
            await self.send_degree_purchase_response(interaction, user, amount, total_cost, degree_name, field)
            session.commit()

    @staticmethod
    def create_multiplier(user: User, multiplier: Decimal, amount: int, degree_type: str, field: str):
        user.multipliers.append(
            Multipliers(stat_multiplier=multiplier, amount_owned=amount, degree_type=degree_type, field=field))

    @staticmethod
    async def send_degree_purchase_response(interaction: nextcord.Interaction,
                                            user: User,
                                            amount: int,
                                            cost: Decimal,
                                            degree_type: str,
                                            field: str):
        response = nextcord.Embed(title="New Degree Purchased!", color=0x00e1ff)
        response.description = f"Congratulations on all the hard work it took to get " \
                               f"{amount} {degree_type} in {field}! Your paycheck has now gone up!"
        response.add_field(name=f"Total Cost", value=f"```\n{format_money(cost)}\n```", inline=True)
        response.add_field(name=f"Total Paycheck Multiplier", value=f"```\n{get_multipliers(user):.0%}\n```",
                           inline=True)
        response.add_field(name=f"Account Balance", value=f"```\n{format_money(user.money)}\n```", inline=False)
        await send_response(interaction, embed=response)
