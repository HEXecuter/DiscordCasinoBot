import nextcord
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Union
from models.model import User
from models.model import Multipliers
from decimal import Decimal
from locale import currency
from datetime import timedelta


def get_user(session: Session, discord_id: int, guild_id: int) -> Union[None | User]:
    return session.execute(select(User).filter_by(discord_id=discord_id, guild_id=guild_id)).scalar()


def get_multipliers(user: User) -> Union[Decimal]:
    multipliers_sum: Union[Decimal | None] = Session.object_session(user).execute(
        select(func.sum(Multipliers.stat_multiplier))
        .where(Multipliers.user_id == user.id)
        .group_by('user_id')).scalar()
    if multipliers_sum is None:
        return Decimal('1.0')
    else:
        return multipliers_sum + Decimal('1.0')


def format_money(amount: Union[Decimal | int | float]) -> str:
    return currency(amount, grouping=True)


def format_timedelta(time: timedelta) -> str:
    seconds_in_hour: int = 3600
    seconds_in_minute: int = 60

    time_list = []
    remaining_seconds: int = int(time.total_seconds())
    if remaining_seconds >= seconds_in_hour:
        remaining_hours = remaining_seconds // seconds_in_hour
        time_list.append(f'{remaining_hours} hour' + ('s' if remaining_hours == 1 else ''))
        remaining_seconds %= seconds_in_hour

    if remaining_seconds >= seconds_in_minute:
        remaining_minutes = remaining_seconds // seconds_in_minute
        time_list.append(f'{remaining_minutes} minute' + ('s' if remaining_minutes == 1 else ''))
        remaining_seconds %= seconds_in_minute

    if remaining_seconds:
        time_list.append(f'{remaining_seconds} second' + ('s' if remaining_seconds == 1 else ''))

    if len(time_list) > 1:
        time_string: str = ', '.join(time_list[0:-1])
        time_string += ', and ' + time_list[-1]
    elif len(time_list) == 0:
        time_string = '0 seconds'
    else:
        time_string = time_list[0]

    return time_string


async def send_response(interaction: nextcord.Interaction, **kwargs):
    if interaction.response.is_done():
        await interaction.followup.send(**kwargs)
    else:
        await interaction.response.send_message(**kwargs)


async def send_error_message(interaction: nextcord.Interaction, error_title: str, error_message: str):
    response = nextcord.Embed(title=error_title, color=0xf50202)
    response.description = f'```{error_message}\n```'
    await send_response(interaction, embed=response)
