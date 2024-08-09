from random import choice

from database import db
import embed_messages
from wordle import Wordle


def generate_duel(id_challenger, id_challenged, amount, duel_type):
    """
    Generates a new duel

    Parameters
    ----------
    id_challenged (int)
    id_challenged (int)
    amount (int)
    duel_type (str)

    Returns
    -------
    duel (Duel)
    """
    match = {"Shifumi": ShifumiDuel, "Wordle": WordleDuel}
    return match[duel_type].new(id_challenger, id_challenged, amount)


def recover_duel(duel_dict):
    """
    Returns the duel object corresponding to the given dict

    Parameters
    ----------
    duel_dict (dict)

    Returns
    -------
    duel (Duel)
    """
    match = {"Shifumi": ShifumiDuel, "Wordle": WordleDuel}
    return match[duel_dict["duel_type"]](duel_dict)


def create_duel_dict(id_challenger, id_challenged, amount, duel_type):
    """
    Generates a new duel

    Parameters
    ----------
    id_challenged (int)
    id_challenged (int)
    amount (int)
    duel_type (str)

    Returns
    -------
    duel (dict)
    """
    duel = {
        "user_id1": id_challenger,  # Challenger
        "user_id2": id_challenged,  # Challenged
        "duel_id": get_new_duel_id(),
        "duel_type": duel_type,
        "amount": amount,
        "result1": None,  # Not played yet
        "result2": None,  # Not played yet
        "accepted": False,  # Not accepted yet
        "message_id": None,  # Not announced yet
        "thread_id": None
    }
    return duel


def get_new_duel_id():
    """
    Creates a new unique id to represent a duel

    Returns
    -------
    res (int)
    """
    if "last_duel_id" not in db.keys():
        db["last_duel_id"] = -1

    db["last_duel_id"] += 1
    return db["last_duel_id"]


def get_all_duels():
    """
    Returns the list of all duels

    Returns
    -------
    res (list (Element_list))
    """
    return db["duels"]


class Duel:
    """
    Abstract class representing a duel
    """

    @staticmethod
    def new(id_challenger, id_challenged, amount):
        """
        Creates a new duel

        Parameters
        ----------
        id_challenger (int)
        id_challenged (int)
        amount (int)

        Returns
        -------
        res (Duel)
        """
        return None

    def get_dict(self):
        """
        Returns a dict representation of the duel, to be stored in the database

        Returns
        -------
        res (dict)
        """
        return self.dict

    def edit(self, key, val):
        """
        Modifies the dict of the duel

        Parameters
        ----------
        key (str)
        value (any)
        """
        self.dict[key] = val

    async def on_accept(self, thread):
        """
        Called when the duel is accepted -> sends the message in the thread

        Parameters
        ----------
        thread (interactions.ThreadChannel)
        """
        pass

    def status(self, caller_id):
        """
        Returns the status of the duel

        Parameters
        ----------
        caller_id (int):
            the id of the user who called the command

        Returns
        -------
        res (str)
        """
        mention = "anyone" if self.dict["user_id2"] == -1 else f"<@{self.dict["user_id2"]}>"

        if not self.dict["accepted"]:
            return f"Waiting on {mention} to accept\n"
        else:
            res = ""
            if self.dict["result1"] is None:
                res += f"Waiting on <@{self.dict["user_id1"]}> to finish playing\n"
            if self.dict["result2"] is None:
                res += f"Waiting on <@{self.dict["user_id2"]}> to finish playing\n"
            return res

    async def play(self, user_id, action):
        """
        Edits the dict in response to a user playing

        Parameters
        ----------
        user_id (int)
        action (any)

        Returns
        -------
        res (dict/None):
            used as kwargs for the reply
        """
        return None

    def is_over(self):
        """
        Returns True if the duel is over

        Returns
        -------
        res (bool)
        """
        return self.dict["result1"] is not None and self.dict["result2"] is not None

    def get_winner_loser(self):
        """
        Returns the id of the winner and the loser of the duel
        Assumes the duel is over
        Returns None if the duel is a tie

        Returns
        -------
        winner (int)
        loser (int)
        """
        return -1, -1

    def tie_str(self):
        """
        Returns the string to send when the duel is a tie

        Returns
        -------
        res (str)
        """
        return ""

    def win_str(self, winner_id, loser_id):
        """
        Returns the string to send when the duel is won

        Parameters
        ----------
        winner_id (int)
        loser_id (int)

        Returns
        -------
        res (str)
        """
        return ""

    def check_entry(self, action):
        """
        Verifies that the given action is valid

        Parameters
        ----------
        action (any)

        Returns
        -------
        res (bool)
        """
        return True, ""


class ShifumiDuel(Duel):
    """
    Classic shifumi duel
    """

    def __init__(self, dict):
        self.dict = dict

    @staticmethod
    def new(id_challenger, id_challenged, amount):
        return ShifumiDuel(create_duel_dict(id_challenger, id_challenged, amount, "Shifumi"))

    async def on_accept(self, thread):
        await thread.send(f"<@{self.dict["user_id2"]}> accepted <@{self.dict["user_id1"]}>'s challenge! Use `/duel play shifumi [your move]`")

    async def play(self, user_id, action):
        user = 1 if user_id == self.dict["user_id1"] else 2
        self.dict[f"result{user}"] = action
        return None

    def get_winner_loser(self):
        move1 = self.dict["result1"]
        move2 = self.dict["result2"]

        # Tie
        if move1 == move2:
            return None

        win_shifumi = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
        if win_shifumi[move1] == move2:
            return self.dict["user_id1"], self.dict["user_id2"]
        else:
            return self.dict["user_id2"], self.dict["user_id1"]

    def tie_str(self):
        return f"They both played {self.dict["result1"]}!"

    def win_str(self, winner_id, loser_id):
        if winner_id == self.dict["user_id1"]:
            return f"They played {self.dict["result1"]} vs {self.dict["result2"]}!"
        else:
            return f"They played {self.dict["result2"]} vs {self.dict["result1"]}!"


class WordleDuel(Duel):
    """
    Wordle duel: the player who finds the word in the least number of attempts wins
    """

    def __init__(self, dict):
        self.dict = dict

    @staticmethod
    def new(id_challenger, id_challenged, amount):
        d = create_duel_dict(id_challenger, id_challenged, amount, "Wordle")
        d["attempts1"] = []
        d["attempts2"] = []
        d["last_image_url1"] = None
        d["last_image_url2"] = None
        d["word"] = choice(Wordle.SOLUTIONS)
        d["hard1"] = False
        d["hard2"] = False

        return WordleDuel(d)

    async def on_accept(self, thread):
        await thread.send(f"<@{self.dict["user_id2"]}> accepted <@{self.dict["user_id1"]}>'s challenge! Use `/duel play wordle [your guess]`")

    def status(self, caller_id):
        mention = "anyone" if self.dict["user_id2"] == -1 else f"<@{self.dict["user_id2"]}>"
        user = 1 if caller_id == self.dict["user_id1"] else 2

        if not self.dict["accepted"]:
            return f"Waiting on {mention} to accept\n"
        else:
            res = ""
            if self.dict["result1"] is None:
                res += f"Waiting on <@{self.dict["user_id1"]}> to finish playing\n"
            if self.dict["result2"] is None:
                res += f"Waiting on <@{self.dict["user_id2"]}> to finish playing\n"

            if self.dict[f"result{user}"] is None and self.dict[f"attempts{user}"] != []:
                res += f"Here is your progress: {self.dict[f"last_image_url{user}"]}\n"
            return res

    def check_entry(self, guess):
        wordle = Wordle(self.dict["word"])
        if not wordle.is_valid(guess.lower()): return False, "This is not a valid word!"
        return True, ""

    async def play(self, user_id, guess):
        user = 1 if user_id == self.dict["user_id1"] else 2

        guess = guess.lower()
        guesses = self.dict[f"attempts{user}"]
        guesses.append(guess)
        nb_guesses = len(guesses)

        header_str = f"{nb_guesses} / {Wordle.NB_ATTEMPTS} attempts made"
        if guess == self.dict["word"]:

            wordle = Wordle(self.dict["word"])
            hard_sol = wordle.is_hard_solution(guesses)
            self.dict[f"result{user}"] = nb_guesses
            header_str = f"You found the word after {nb_guesses} attempts!"
            if hard_sol:
                header_str += "\nThis was a hard-mode solution!"
                self.dict[f"hard{user}"] = True
        elif nb_guesses == Wordle.NB_ATTEMPTS:
            self.dict[f"result{user}"] = Wordle.NB_ATTEMPTS + 1
            header_str = "You failed to find the word!"

        embed = await embed_messages.get_embed_wordle(self.dict["word"], guesses, header_str, user_id)
        self.dict[f"last_image_url{user}"] = embed.images[0].url
        return {"embed": embed}

    def get_winner_loser(self):
        n1 = self.dict["result1"]
        n2 = self.dict["result2"]

        hard1 = self.dict["hard1"]
        hard2 = self.dict["hard2"]

        # Tie
        if n1 == n2:
            if hard1 == hard2: return None
            if hard1: return self.dict["user_id1"], self.dict["user_id2"]
            return self.dict["user_id2"], self.dict["user_id1"]
        if n1 < n2: return self.dict["user_id1"], self.dict["user_id2"]
        return self.dict["user_id2"], self.dict["user_id1"]

    def tie_str(self):
        if self.dict["result1"] == Wordle.NB_ATTEMPTS + 1:
            return "They both failed to find the word!"
        s = f"They both found the word in {self.dict["result1"]} attempts"
        if self.dict["hard1"]: s += " (hard-mode)!"
        else: s += " (not hard-mode)!"
        return s

    def win_str(self, winner_id, loser_id):
        n1, n2 = self.dict["result1"], self.dict["result2"]
        if n1 == Wordle.NB_ATTEMPTS + 1:
            return f"<@{winner_id}> found the word in {n2} attempts while <@{loser_id}> failed!"
        if n2 == Wordle.NB_ATTEMPTS + 1:
            return f"<@{winner_id}> found the word in {n1} attempts while <@{loser_id}> failed!"
        if n1 != n2:
            return f"<@{winner_id}> found the word in {min(n1, n2)} attempts while <@{loser_id}> found it in {max(n1, n2)} attempts!"
        return f"<@{winner_id}> and <@{loser_id}> both found the word in {n1} attempts, but <@{winner_id}> did it in hard mode while <@{loser_id}> did not!"
