import nextcord
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Union
from models.model import User
from models.model import Multipliers
from decimal import Decimal
from locale import currency


def get_user(session: Session, discord_id: int, guild_id: int) -> Union[None | User]:
    return session.execute(select(User).filter_by(discord_id=discord_id, guild_id=guild_id)).scalar()


def get_multipliers(session: Session, user_id: int) -> Union[Decimal | None]:
    return session.execute(select(func.sum(Multipliers.stat_multiplier))
                           .where(Multipliers.user_id == user_id)
                           .group_by('user_id')).scalar() + Decimal('1.0')


def format_money(amount: Union[Decimal | int | float]) -> str:
    return currency(amount, grouping=True)


async def send_response(interaction: nextcord.Interaction, **kwargs):
    if interaction.response.is_done():
        await interaction.followup.send(**kwargs)
    else:
        await interaction.response.send_message(**kwargs)


async def send_error_message(interaction: nextcord.Interaction, error_title: str, error_message: str):
    response = nextcord.Embed(title=error_title, color=0xf50202)
    response.description = f'```{error_message}\n```'
    await send_response(interaction, embed=response)
