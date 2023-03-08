from typing import List
from sqlalchemy import BigInteger
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import DECIMAL
from sqlalchemy import DATE
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    money: Mapped[DECIMAL] = mapped_column(DECIMAL(precision=2), nullable=False, server_default='1000')
    job: Mapped['Job'] = relationship(back_populates='user')
    multipliers: Mapped[List['Multipliers']] = relationship(back_populates='user')


class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='job')
    title: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)
    company: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)
    # Default is an arbitrary date in the past so the user can immediately redeem paycheck
    paycheck_redeemed: Mapped[DateTime] = mapped_column(DATE, nullable=False, server_default='2020-01-01')


class Multipliers(Base):
    __tablename__ = 'multipliers'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='multipliers')
    stat_multiplier: Mapped[DECIMAL] = mapped_column(DECIMAL(2), nullable=False)
    amount_owned: Mapped[int] = mapped_column(BigInteger, nullable=False)
    degree_type_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    industry_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
