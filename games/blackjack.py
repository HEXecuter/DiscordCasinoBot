import os
from random import shuffle
from decimal import Decimal
import json


class BlackJack:
    GAME_TYPE = 'blackjack'
    _CARDS_BASE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'images', 'cards')

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
        self._load_playing_cards()
        self._shuffle_cards()

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
        print(winner)
        print(self._calculate_hand_value(self.state['player_hand']))
        print(self._calculate_hand_value(self.state['house_hand']))
        if winner == 'player':
            if self._calculate_hand_value(self.state['player_hand']) == 21 and len(self.state['player_hand']) == 2:
                print('natural')
                self.state['payout'] = self.state['bet_amount'] * 3
            else:
                self.state['payout'] = self.state['bet_amount'] * 2
        if winner == 'push':
            self.state['payout'] = self.state['bet_amount']

    def serialize_to_json(self):
        return json.dumps(self.state, default=str)

    def deserialize_from_json(self, state: str):
        self.state = json.loads(state)
        self.state['payout'] = Decimal(self.state['payout'])
        self.state['bet_amount'] = Decimal(self.state['bet_amount'])
        return self

    @classmethod
    def from_json(cls, state: str):
        return BlackJack().deserialize_from_json(state)
