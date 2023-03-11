import nextcord
from typing import Union
from nextcord.ext import commands
from models.model import User
from models.model import Job
from models.model import engine
from sqlalchemy.orm import Session
from utils.helpers import get_user
from utils.helpers import send_error_message
from utils.helpers import send_response
from datetime import date
from decimal import Decimal


class Employment(commands.Cog):
    degrees = {
        'bachelors': {
            'price': Decimal("1000"),
            'stat': Decimal("1"),
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

    @nextcord.slash_command(guild_ids=[868296265564319774])
    async def apply_for_job(self, interaction: nextcord.Interaction,
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
            else:
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
                               f"Thanks to their mistake, you are now the {user.job.title} at {user.job.company}. Don't " \
                               f"forget to get your paycheck! You can also \"study hard\" and pay " \
                               f"for certifications and degrees that increase your salary.\n```"
        response.add_field(name=f"Job Title", value=f"```\n{user.job.title}\n```", inline=False)
        response.add_field(name=f"Company Name", value=f"```\n{user.job.company}\n```", inline=False)
        await send_response(interaction, embed=response)
