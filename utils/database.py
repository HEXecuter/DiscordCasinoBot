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
    return session.execute(select(func.sum(Multipliers.stat_multiplier)).where(Multipliers.user_id == user_id).group_by(
        'user_id')).scalar() + Decimal('1.0')


def format_money(amount: Union[Decimal | int | float]) -> str:
    return currency(amount, grouping=True)
