import os
from random import shuffle
from decimal import Decimal
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from io import BytesIO
from utils.helpers import format_money
import json


class BlackJack:
    GAME_TYPE = 'blackjack'
    _CARDS_BASE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'images', 'cards')
    _FONT_TTF_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'Smokum-Regular.ttf')

    def __init__(self):
        self.state = {
            'remaining_cards': [],
            'house_hand': [],
            'player_hand': [],
            'bet_amount': Decimal('0.00'),
            'payout': Decimal('0.00'),
            'game_ended': False,
            'can_double_down': True
        }

    def _load_playing_cards(self):
        self.state['remaining_cards'] = os.listdir(BlackJack._CARDS_BASE_DIRECTORY)
        self.state['remaining_cards'].remove('back.png')

    @staticmethod
    def _get_card_value(card_name: str) -> int:
        rank, _ = card_name.split('_')
        if rank.isdigit():
            return int(rank)
        return 10

    def _shuffle_cards(self):
        shuffle(self.state['remaining_cards'])

    def _deal_card(self) -> str:
        return self.state['remaining_cards'].pop()

    def _add_to_bet(self, bet_amount: Decimal):
        self.state['bet_amount'] += bet_amount

    def start_game(self, bet_amount: Decimal):
        self._load_playing_cards()
        self._shuffle_cards()
        self._add_to_bet(bet_amount)
        self.state['house_hand'].append(self._deal_card())
        self.state['house_hand'].append(self._deal_card())
        self.state['player_hand'].append(self._deal_card())
        self.state['player_hand'].append(self._deal_card())

    def hit_player(self):
        if self.state['game_ended']:
            raise RuntimeError('Game has already ended')

        self.state['player_hand'].append(self._deal_card())
        if self._calculate_hand_value(self.state['player_hand']) >= 21 or not self.state['can_double_down']:
            self.state['game_ended'] = True
            self._close_game()

    def _hit_house(self):
        self.state['house_hand'].append(self._deal_card())

    def double_down(self):
        if self.state['can_double_down']:
            self.state['can_double_down'] = False
            self._add_to_bet(self.state['bet_amount'])
            self.hit_player()
        else:
            raise RuntimeError('Player can not double down twice')

    def _calculate_hand_value(self, hand: list[str]):
        possible_values = [0]
        ace_used = False

        for card in hand:
            value = self._get_card_value(card)
            if value == 1 and not ace_used:
                possible_values.append(possible_values[0] + 10)
            for index in range(len(possible_values)):
                possible_values[index] += value
        return self._get_best_value(possible_values)

    @staticmethod
    def _get_best_value(values: list[int]) -> int:
        if len(values) == 1:
            return values[0]
        if values[0] == 21 or values[1] == 21:
            return 21
        if values[0] > 21 or values[1] > 21:
            return min(values)
        if values[0] <= 21 and values[1] <= 21:
            return max(values)
        print(-1, values)
        return -1

    def stand(self):
        self.state['game_ended'] = True
        self._close_game()

    def _get_winner(self):
        player_value = self._calculate_hand_value(self.state['player_hand'])
        house_value = self._calculate_hand_value(self.state['house_hand'])
        if player_value > 21:
            return 'house'
        if house_value > 21:
            return 'player'
        if player_value == house_value:
            return 'push'
        if player_value > house_value:
            return 'player'
        if house_value > player_value:
            return 'house'

    def _close_game(self):
        while self._calculate_hand_value(self.state['house_hand']) < 17:
            self._hit_house()
        winner = self._get_winner()
        if winner == 'player':
            if self._calculate_hand_value(self.state['player_hand']) == 21 and len(self.state['player_hand']) == 2:
                self.state['payout'] = self.state['bet_amount'] * 3
            else:
                self.state['payout'] = self.state['bet_amount'] * 2
        if winner == 'push':
            self.state['payout'] = self.state['bet_amount']

    def serialize_to_json(self):
        return json.dumps(self.state, default=str)

    def _deserialize_from_json(self, state: str):
        self.state = json.loads(state)
        self.state['payout'] = Decimal(self.state['payout'])
        self.state['bet_amount'] = Decimal(self.state['bet_amount'])
        return self

    @classmethod
    def from_json(cls, state: str):
        return BlackJack()._deserialize_from_json(state)

    def _create_hand_image(self, hand: list[str], hide_second_card: bool = False) -> Image:
        spacing_between_cards = 20
        card_images: list[Image] = []
        for index, card_name in enumerate(hand):
            if index == 1 and hide_second_card and not self.state['game_ended']:
                card_name = 'back.png'
            card_images.append(Image.open(os.path.join(BlackJack._CARDS_BASE_DIRECTORY, card_name)))
        card_width = card_images[0].width
        card_height = card_images[0].height
        canvas = Image.new('RGBA',
                           # Calculate width of blank canvas with 10 px spacing on each edge and between all cards
                           ((card_width * len(card_images)) + (spacing_between_cards * (len(card_images) + 1)),
                            card_height))
        current_x = spacing_between_cards
        for image in card_images:
            canvas.paste(image, (current_x, 0), mask=image.convert('RGBA'))
            current_x += spacing_between_cards + card_width
        return canvas

    def _create_headline_image(self) -> Image:
        spacing = 10
        if self.state['game_ended']:
            winner = self._get_winner()
            if winner != 'push':
                text = f'{winner} WON!'
            else:
                text = winner
            text = text.upper()
        else:
            text = f"AMOUNT BET: {format_money(self.state['bet_amount'])[0:-3]}"

        font = ImageFont.truetype(BlackJack._FONT_TTF_PATH, 200)
        _, _, w, h = font.getbbox(text)
        canvas = Image.new('RGBA',
                           (w + (2 * spacing), h + (2 * spacing)))
        drawable_canvas = ImageDraw.Draw(canvas)
        drawable_canvas.text((spacing, spacing), text, font=font, fill='gold')
        return canvas

    def create_table_image(self) -> BytesIO:
        spacing_between_decks = 100
        width_min = 2500
        headline_image = self._create_headline_image()
        house_deck = self._create_hand_image(self.state['house_hand'], True)
        player_deck = self._create_hand_image(self.state['player_hand'], False)

        max_width = max(width_min, headline_image.width, player_deck.width, house_deck.width)
        max_width += max_width // 2

        canvas = Image.new('RGBA',
                           (max_width,
                            headline_image.height + spacing_between_decks + house_deck.height + spacing_between_decks + player_deck.height + spacing_between_decks),
                           'forestgreen')
        height_position = 0
        for index, image_to_paste in enumerate([headline_image, house_deck, player_deck]):
            centered_x = (max_width - image_to_paste.width) // 2
            canvas.paste(image_to_paste, (centered_x, height_position), mask=image_to_paste)
            height_position += image_to_paste.height + spacing_between_decks

        canvas_bytes = BytesIO()
        canvas.save(canvas_bytes, 'PNG')
        canvas_bytes.seek(0)
        return canvas_bytes
