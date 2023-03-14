from decimal import Decimal
import json


class Roulette:
    TABLE_NUMBERS = (
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
        '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36')

    def __init__(self):
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

    def add_outside_bet(self, bet_type: str, amount: Decimal):
        if bet_type not in self.outside_bets:
            raise ValueError(f'Value supplied for bet_type is not valid: {bet_type=}')
        self.outside_bets[bet_type]['amount'] += amount

    def add_inside_bet(self, table_tile: str, amount: Decimal):
        if table_tile not in Roulette.TABLE_NUMBERS:
            raise ValueError(f'Value supplied for table_tile is not valid: {table_tile=}')
        if table_tile not in self.inside_bets['straight up']['picks']:
            self.inside_bets['straight up']['picks'][table_tile] = {'amount': Decimal('0.00')}
        self.inside_bets['straight up']['picks'][table_tile]['amount'] += amount

    def serialize_to_json(self):
        state: dict = dict()
        state['inside_bets'] = self.inside_bets
        state['outside_bets'] = self.outside_bets
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

        return self

    @classmethod
    def from_json(cls, state: str):
        return Roulette().deserialize_from_json(state)
