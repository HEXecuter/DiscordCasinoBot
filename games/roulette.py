from decimal import Decimal
from random import choice
from os import path
from PIL import Image, ImageFont, ImageDraw
import json
from utils.helpers import format_money


class Roulette:
    TABLE_NUMBERS = (
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
        '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36')

    OUTSIDE_BETS = ('even', 'odd', 'first dozen', 'second dozen', 'third dozen', 'low', 'high')

    GAME_TYPE = 'roulette'

    _OUTSIDE_IMAGE_POSITIONS = {
        'even': (336, 410),
        'odd': (820, 410),
        'first dozen': (257, 321),
        'second dozen': (578, 321),
        'third dozen': (900, 321),
        'low': (176, 410),
        'high': (980, 410),
    }

    _INSIDE_IMAGE_POSITIONS = {
        '0': (48, 140),
        '1': (135, 232),
        'x_distance': 80,
        'y_distance': 92
    }

    _CHIP_PATH = path.join('images', 'chip.png')
    _TABLE_PATH = path.join('images', 'roulette_table.png')
    _FONT_TTF_PATH = path.join('fonts', 'Smokum-Regular.ttf')

    def __init__(self):
        self.outside_mappings = {
            'even': self.is_even,
            'odd': self.is_odd,
            'first dozen': self.is_first_dozen,
            'second dozen': self.is_second_dozen,
            'third dozen': self.is_third_dozen,
            'low': self.is_low,
            'high': self.is_high,
        }

        self.outside_bets = {
            'even':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')},
            'odd':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')},
            'first dozen':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('2.00')},
            'second dozen':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('2.00')},
            'third dozen':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('2.00')},
            'low':
                {'amount': Decimal('0.00'),
                 'payout': Decimal('1.00')},
            'high':
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

        self.tile_picked = ''
        self.bet_hits = []

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
        self.bet_total = Decimal(state['bet_total'])
        self.payout = Decimal(state['payout'])
        return self

    @classmethod
    def from_json(cls, state: str):
        return Roulette().deserialize_from_json(state)

    def play(self):
        if not self.bet_placed:
            raise RuntimeError('No bets have been placed')

        self.tile_picked = choice(Roulette.TABLE_NUMBERS)
        for outer_group in self.outside_bets:
            if self.outside_mappings[outer_group](self.tile_picked) and \
                    self.outside_bets[outer_group]['amount'] > Decimal('0.00'):
                bet_payout = self.outside_bets[outer_group]['amount'] * \
                             (Decimal('1.00') + self.outside_bets[outer_group]['payout'])
                self.payout += bet_payout
                self.bet_hits.append([outer_group, bet_payout])

        if self.tile_picked in self.inside_bets['straight up']['picks']:
            bet_payout = self.inside_bets['straight up']['picks'][self.tile_picked]['amount'] * \
                         (Decimal('1.00') + self.inside_bets['straight up']['payout'])
            self.payout += bet_payout
            self.bet_hits.append([self.tile_picked, bet_payout])

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
    def is_low(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 1 <= num <= 18:
            return True
        return False

    @staticmethod
    def is_high(tile: str) -> bool:
        if tile == '0':
            return False
        num = int(tile)
        if 19 <= num <= 36:
            return True
        return False

    @staticmethod
    def create_chip(value: Decimal) -> Image:
        chip_image: Image = Image.open(Roulette._CHIP_PATH)
        chip_width = chip_image.width
        chip_height = chip_image.height

        drawable_chip: ImageDraw = ImageDraw.Draw(chip_image)
        font = ImageFont.truetype(Roulette._FONT_TTF_PATH, 20)
        text = format_money(value)[0:-3]
        _, _, w, h = drawable_chip.textbbox((0, 0), text, font=font)

        centered_x_axis = (chip_width - w) / 2
        centered_y_axis = (chip_height - h) / 2
        drawable_chip.text((centered_x_axis, centered_y_axis), text, font=font, fill='black')
        return chip_image
