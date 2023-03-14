from decimal import Decimal
from random import choice
import json


class Roulette:
    TABLE_NUMBERS = (
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
        '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36')

    def __init__(self):
        self.outside_mappings = {
            'even': self.is_even,
            'odd': self.is_odd,
            'first twelve': self.is_first_dozen,
            'second twelve': self.is_second_dozen,
            'third twelve': self.is_third_dozen,
            'first 18': self.is_first_eighteen,
            'second 18': self.is_second_eighteen,
        }

        self.outside_bets = {
            'even':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')},
            'odd':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')},
            'first twelve':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('2.00')},
            'second twelve':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('2.00')},
            'third twelve':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('2.00')},
            'first 18':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')},
            'second 18':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')}
        }

        self.inside_bets = {
            'straight up':
                {'picks': dict(),
                 'payout': Decimal('35.00')}
        }

        self.bet_placed = False
        self.bet_total = Decimal('0.00')
        self.payout = Decimal('0.00')

    def add_outside_bet(self, bet_type: str, amount: Decimal):
        if bet_type not in self.outside_bets:
            raise ValueError(f'Value supplied for bet_type is not valid: {bet_type=}')
        self.outside_bets[bet_type]['amount'] += amount
        self.bet_placed = True
        self.bet_total += amount

    def add_inside_bet(self, table_tile: str, amount: Decimal):
        if table_tile not in Roulette.TABLE_NUMBERS:
            raise ValueError(f'Value supplied for table_tile is not valid: {table_tile=}')
        if table_tile not in self.inside_bets['straight up']['picks']:
            self.inside_bets['straight up']['picks'][table_tile] = {'amount': Decimal('0.00')}
        self.inside_bets['straight up']['picks'][table_tile]['amount'] += amount
        self.bet_placed = True
        self.bet_total += amount

    def serialize_to_json(self):
        state: dict = dict()
        state['inside_bets'] = self.inside_bets
        state['outside_bets'] = self.outside_bets
        state['bet_placed'] = self.bet_placed
        state['bet_total'] = self.bet_total
        state['payout'] = self.payout
        return json.dumps(state, default=str)

    def deserialize_from_json(self, state: str):
        state: dict = json.loads(state)

        for outside_bet in state['outside_bets']:
            state['outside_bets'][outside_bet]['payout'] = Decimal(state['outside_bets'][outside_bet]['payout'])
            state['outside_bets'][outside_bet]['amount'] = Decimal(state['outside_bets'][outside_bet]['amount'])

        state['inside_bets']['straight up']['payout'] = Decimal(state['inside_bets']['straight up']['payout'])
        for tile in state['inside_bets']['straight up']['picks']:
            state['inside_bets']['straight up']['picks'][tile]['amount'] = Decimal(
                state['inside_bets']['straight up']['picks'][tile]['amount'])

        self.outside_bets = state['outside_bets']
        self.inside_bets = state['inside_bets']
        self.bet_placed = state['bet_placed']
        self.bet_total = state['bet_total']
        self.payout = state['payout']
        return self

    @classmethod
    def from_json(cls, state: str):
        return Roulette().deserialize_from_json(state)

    def play(self):
        if not self.bet_placed:
            raise RuntimeError('No bets have been placed')

        tile_picked = choice(Roulette.TABLE_NUMBERS)
        print(f'{tile_picked=}')
        for outer_group in self.outside_bets:
            if self.outside_mappings[outer_group](tile_picked) and self.outside_bets[outer_group]['amount'] > Decimal(
                    '0.00'):
                self.payout += self.outside_bets[outer_group]['amount'] * (
                            Decimal('1.00') + self.outside_bets[outer_group]['payout'])
                print(f'hit on {outer_group=} for {tile_picked}')
                print(self.payout)

        if tile_picked in self.inside_bets['straight up']['picks']:
            self.payout += self.inside_bets['straight up']['picks'][tile_picked]['amount'] * (
                    Decimal('1.00') + self.inside_bets['straight up']['payout'])
            print(f'hit on {tile_picked=}')
            print(self.payout)

    @staticmethod
    def is_even(tile: str) -> bool:
        if tile == '0':
            return False
        if int(tile) % 2 == 0:
            return True
        return False

    @staticmethod
    def is_odd(tile: str) -> bool:
        if tile == '0':
            return False
        if int(tile) % 2 == 1:
            return True
        return False

    @staticmethod
    def is_first_dozen(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 1 <= num <= 12:
            return True
        return False

    @staticmethod
    def is_second_dozen(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 13 <= num <= 24:
            return True
        return False

    @staticmethod
    def is_third_dozen(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 25 <= num <= 36:
            return True
        return False

    @staticmethod
    def is_first_eighteen(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 1 <= num <= 18:
            return True
        return False

    @staticmethod
    def is_second_eighteen(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 19 <= num <= 36:
            return True
        return False
