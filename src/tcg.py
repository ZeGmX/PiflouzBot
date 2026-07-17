import random

# import utils

# from constant import Constants
# from interactions import OptionType, auto_defer, slash_command, slash_option
# from user_profile import get_profile
from database.my_database import Element, ElementList

SUITS = ["H", "D", "C", "S"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.name = f"{rank}{suit}"
    
    def __str__(self):
        return self.name

ALL_CARDS = [Card(suit=suit, rank=rank) for rank in RANKS for suit in SUITS]

class Collection:
    def __init__(self, count_list: list[int] | ElementList | None = None):
        if count_list is None:
            count_list = self.create_empty_collection()
        self.cards_counts: list[int] | ElementList = count_list

    @staticmethod
    def create_empty_collection():
        """
        Creates a deserialized empty collection for the user, in the format stored in the db.
        TODO: Docstring
        """
        return [0 for _ in range (len(ALL_CARDS))]

    @staticmethod
    def convert_tuple_to_index( suit, rank) -> int:
        """
        Converts a card tuple to an index in the collection

        Args:
            card_tuple (tuple[str, str]): The card tuple to convert

        Returns:
            int: The index of the card in the collection
        """
        suit_index = SUITS.index(suit)
        rank_index = RANKS.index(rank)
        return (suit_index * len(RANKS) + rank_index)


    def get_card(self,suit, rank) -> int:
        return self.cards_counts[self.convert_tuple_to_index(suit, rank)]


    def add_card(self, suit, rank):
        self.cards_counts[self.convert_tuple_to_index(suit, rank)] += 1
        return self.cards_counts[self.convert_tuple_to_index(suit, rank)]
    
    def add_cards(self, cards: list[Card]):
        for card in cards:
            self.add_card(card.suit, card.rank)
        return self.cards_counts
    
    def deserialize(self):
        return self.cards_counts
    
    def __str__(self):
        return str([f'{card}:{self.cards_counts[self.convert_tuple_to_index(card.suit, card.rank)]}' for card in ALL_CARDS if self.cards_counts[self.convert_tuple_to_index(card.suit, card.rank)] > 0])



def add_card_to_collection(user_id, card):
    """
    Adds a card to the user's collection

    Args:
        user_id (int/str): The ID of the user
        card (Card): The card to add
    """
    current_collection = get_user_collection(user_id)
    
    current_collection["card_name"] = card.name
    
    
    raise NotImplementedError("This function is not implemented yet")


def generate_random_card(randomizer: random.Random | None = None):
    """
    Generates a random card

    Args:
        randomizer (random.Random, optional): The random number generator

    Returns:
        Card: The generated card
    """
    if randomizer is None:
        randomizer = random.Random()
    
    suit = randomizer.choice(SUITS)
    rank = randomizer.choice(RANKS) #TODO: add rarity

    return Card(suit, rank)

def generate_random_pack(randomizer: random.Random | None = None, pack_size: int = 5):
    """
    Generates a random pack of cards

    Args:
        randomizer (random.Random, optional): The random number generator
        pack_size (int, optional): The size of the pack

    Returns:
        list[Card]: The generated pack of cards
    """
    if randomizer is None:
        randomizer = random.Random()
    
    return [generate_random_card(randomizer) for _ in range(pack_size)]

if __name__ == "__main__":
    # Test the Card class
    card = Card("H", "A")
    print(card.name)  # Output: AH

    # Test the Collection class
    collection = Collection()
    print(collection.cards_counts)
    
    collection.add_card("H", "A")
    print(collection.cards_counts)
    
    collection.add_card("D", "A")
    print(collection.cards_counts)
    
    collection.add_card("H", "K")
    print(collection.cards_counts)
    collection.add_card("H", "K")
    print(collection.cards_counts)
    
    print(collection.get_card("H", "A"))
    print(collection.get_card("H", "K"))