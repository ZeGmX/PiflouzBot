import os
import random

# import utils
from constant import Constants
from database.my_database import ElementDict
from user_profile import get_profile


def get_all_cards():
    """
    Returns all the cards in the TCG

    Returns
    -------
        list[Card]: All the cards in the TCG
    """
    return {family: [Card(family=family, id=id) for id in CardFamily(family).get_ids()] for family in Constants.TCG_FAMILIES}


class CardFamily:
    """
    Represents a family of cards in the TCG
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def pretty_str(self):
        return self.name.capitalize()

    def get_ids(self, small = True):
        """
        Returns the IDs of the card for this family (= name of the files in the folder)

        Returns
        -------
            list[str]: The IDs of the card for this family
        """
        folder = "small_cards" if small else "big_cards"
        files = os.listdir(os.path.join(Constants.TCG_BASE_PATH, folder, self.name))
        return list(map(lambda x: x.split(".")[0], files))


class CardID:
    """
    Represents the ID of a card in the TCG (regardless of family)
    """

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return self.id

    def pretty_str(self):
        return self.id.capitalize()


class Card:
    """
    Represents a card in the TCG
    """

    def __init__(self, family: str, id: str):
        self.family = CardFamily(family)
        self.id = CardID(id)

    def __str__(self):
        return self.family.pretty_str() + " - " + self.id.pretty_str()

    def family_name(self):
        """
        Returns the name of the card's family as a string

        Returns
        -------
        str
        """
        return str(self.family)

    def id_name(self):
        """
        Returns the name of the card's ID as a string

        Returns
        -------
        str
        """
        return str(self.id)

    def get_image_path(self, small: bool = True):
        """
        Returns the path to the image of the card

        Args:
            small (bool, optional): Whether to return the path to the small image or the large image. Defaults to True

        Returns
        -------
            str: The path to the image of the card
        """
        folder = "small_cards" if small else "big_cards"
        return os.path.join(Constants.TCG_BASE_PATH, folder, self.family_name(), self.id_name() + ".png")


class CardCollection:
    def __init__(self, counts: dict[str, int] | ElementDict | None = None):
        if counts is None:
            counts = self.create_empty_collection()
        self.cards_counts: dict[str, int] | ElementDict = counts

    @staticmethod
    def create_empty_collection():
        """
        Creates a deserialized empty collection for the user, in the format stored in the db.
        TODO: Docstring
        """
        return {family: {card_id: 0 for card_id in CardFamily(family).get_ids()} for family in Constants.TCG_FAMILIES}

    def get_card_count(self, family, id) -> int:
        """
        Returns the number of copies of a card in the user's collection

        Parameters
        ----------
        family (str): The family of the card
        id (str): The ID of the card

        Returns
        -------
            int: The number of copies of the card in the user's collection
        """
        return self.cards_counts[family][id]

    def add_card(self, family, id):
        """
        Adds a copy of a card to the user's collection

        Parameters
        ----------
        family (str): The family of the card
        id (str): The ID of the card

        Returns
        -------
            int: The updated number of copies of the card in the user's collection
        """
        self.cards_counts[family][id] += 1
        return self.get_card_count(family, id)

    def add_cards(self, cards: list[Card]):
        """
        Adds multiple cards to the user's collection

        Parameters
        ----------
        cards (list[Card]): The list of cards to add

        Returns
        -------
            dict[str, int]: The updated card counts in the user's collection
        """
        for card in cards:
            self.add_card(card.family.name, card.id.id)
        return self.cards_counts

    def deserialize(self):
        return self.cards_counts

    def __str__(self):
        filtered_families = [family for family in self.cards_counts.keys() if any(count > 0 for count in self.cards_counts[family].values())]  # Filter families with at least one card
        filtered_collection = {family: {card_id: count for card_id, count in self.cards_counts[family].items() if count > 0} for family in filtered_families}
        return str(filtered_collection)


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

    Returns
    -------
        Card: The generated card
    """
    if randomizer is None:
        randomizer = random.Random()

    family = randomizer.choice(Constants.TCG_FAMILIES)
    id = randomizer.choice(CardFamily(family).get_ids())  # TODO: add rarity

    return Card(family, id)


def generate_random_pack(randomizer: random.Random | None = None, pack_size: int = 5):
    """
    Generates a random pack of cards

    Args:
        randomizer (random.Random, optional): The random number generator
        pack_size (int, optional): The size of the pack

    Returns
    -------
        list[Card]: The generated pack of cards
    """
    if randomizer is None:
        randomizer = random.Random()

    return [generate_random_card(randomizer) for _ in range(pack_size)]


def get_user_collection(user_id):
    """
    Returns the user's collection of cards
    Also creates an empty collection if the user doesn't have one yet.

    Parameters
    ----------
        user_id (int/str): The ID of the user

    Returns
    -------
        CardCollection: The user's collection of cards
    """
    profile = get_profile(user_id)

    if "card_collection" not in profile:
        profile["card_collection"] = CardCollection.create_empty_collection()

    fetched_result = profile["card_collection"]

    assert isinstance(fetched_result, ElementDict), "Profile is not an ElementDict"
    return CardCollection(fetched_result)


if __name__ == "__main__":
    pass

    # # Test the Card class
    # card = Card("H", "A")
    # print(card.name)  # Output: AH

    # # Test the Collection class
    # collection = Collection()
    # print(collection.cards_counts)

    # collection.add_card("H", "A")
    # print(collection.cards_counts)

    # collection.add_card("D", "A")
    # print(collection.cards_counts)

    # collection.add_card("H", "K")
    # print(collection.cards_counts)
    # collection.add_card("H", "K")
    # print(collection.cards_counts)

    # print(collection.get_card("H", "A"))
    # print(collection.get_card("H", "K"))
