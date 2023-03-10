from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Union
from models.model import User
from decimal import Decimal
from locale import currency

def get_user(session: Session, discord_id: int, guild_id: int) -> Union[None | User]:
    return session.execute(select(User).filter_by(discord_id=discord_id, guild_id=guild_id)).first()


def format_money(amount: Union[Decimal | int | float]) -> str:
    return currency(amount, grouping=True)