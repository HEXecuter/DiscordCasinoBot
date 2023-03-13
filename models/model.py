from locale import setlocale
from locale import currency
from locale import LC_ALL
from typing import List
from sqlalchemy import BigInteger
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import DECIMAL
from sqlalchemy import DATE
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
import os

MONEY_DEFAULT: str = '1000'
PET_PRICE_DEFAULT: str = '100000'


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    money: Mapped[DECIMAL] = mapped_column(DECIMAL(precision=2), nullable=False, server_default=MONEY_DEFAULT)
    job: Mapped['Job'] = relationship(back_populates='user')
    pet: Mapped['Pet'] = relationship(back_populates='user', foreign_keys='Pet.user_id')
    multipliers: Mapped[List['Multipliers']] = relationship(back_populates='user')

    def __str__(self):
        return_string = f'User Object:\n' \
                        f'\tid: {self.id}\n' \
                        f'\tdiscord_id: {self.discord_id}\n' \
                        f'\tguild_id: {self.guild_id}\n'
        # self.money can be None on the User object before it is committed to the DB
        if self.money is not None:
            return_string += f'\tmoney: {currency(self.money, grouping=True)}\n'
        else:
            return_string += f'\tmoney: None\n'
        return return_string


class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='job')
    title: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)
    company: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)
    # Default is an arbitrary date in the past so the user can immediately redeem paycheck
    paycheck_redeemed: Mapped[DATE] = mapped_column(DATE, nullable=False, server_default='2020-01-01')

    def __str__(self):
        return f'Job Object:\n' \
               f'\tid: {self.id}\n' \
               f'\tuser_id: {self.user_id}\n' \
               f'\ttitle: {self.title}\n' \
               f'\tcompany: {self.company}\n' \
               f'\tpaycheck_redeemed: {self.paycheck_redeemed}\n'


class Multipliers(Base):
    __tablename__ = 'multipliers'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='multipliers')
    stat_multiplier: Mapped[DECIMAL] = mapped_column(DECIMAL(2), nullable=False)
    amount_owned: Mapped[int] = mapped_column(BigInteger, nullable=False)
    degree_type: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)
    field: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)

    def __str__(self):
        return f'Multiplier:\n' \
               f'\tuser_id: {self.user_id}\n' \
               f'\tstat_multiplier: {self.stat_multiplier:.0%}\n' \
               f'\tamount_owned: {self.amount_owned}\n' \
               f'\tdegree_type_index: {self.degree_type}\n' \
               f'\tindustry_index: {self.field}\n'


class Pet(Base):
    __tablename__ = 'pets'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='pet', foreign_keys=user_id)
    # Null current_owner means the pet is owned by the discord bot and not another user
    current_owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    current_owner: Mapped['User'] = relationship(back_populates='pet', foreign_keys=current_owner_id)
    name: Mapped[str] = mapped_column(String(32, collation='NOCASE'), nullable=False)
    purchase_price: Mapped[DECIMAL] = mapped_column(DECIMAL(precision=2), nullable=False,
                                                    server_default=PET_PRICE_DEFAULT)

    def __str__(self):
        return f'Pet:\n' \
               f'\tid: {self.id}\n' \
               f'\tuser_id: {self.user_id}\n' \
               f'\tcurrent_owner_id: {self.current_owner_id}\n' \
               f'\tname: {self.name}\n' \
               f'\tpurchase_price: {self.purchase_price}\n'


engine = create_engine('sqlite:///' + os.path.abspath(os.path.join(os.getcwd(), 'casino.sqlite3')))
Base.metadata.create_all(engine)

if __name__ == '__main__':
    setlocale(LC_ALL, 'en_US')
