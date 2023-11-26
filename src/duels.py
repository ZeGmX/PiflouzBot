from random import choice

from my_database import db
import utils
from wordle import Wordle


def generate_duel(id_challenger, id_challenged, amount, duel_type):
    """
    Generates a new duel
    --
    input:
        id_challenged: int
        id_challenged: int
        amount: int
        duel_type: str
    -- 
        output:
        duel: Duel
    """
    match = {"Shifumi": Shifumi_duel, "Wordle": Wordle_duel}
    return match[duel_type].new(id_challenger, id_challenged, amount)


def recover_duel(duel_dict):
    """
    Returns the duel object corresponding to the given dict
    --
    input:
        duel_dict: dict
    --
    output:
        duel: Duel
    """
    match = {"Shifumi": Shifumi_duel, "Wordle": Wordle_duel}
    return match[duel_dict["duel_type"]](duel_dict)


def create_duel_dict(id_challenger, id_challenged, amount, duel_type):
    """
    Generates a new duel
    --
    input:
        id_challenged: int
        id_challenged: int
        amount: int
        duel_type: str
    --
    output:
        duel: dict
    """
    duel = {
        "user_id1": id_challenger, # Challenger
        "user_id2": id_challenged, # Challenged
        "duel_id": get_new_duel_id(),
        "duel_type": duel_type,
        "amount": amount,
        "result1": None, # Not played yet
        "result2": None, # Not played yet
        "accepted": False, # Not accepted yet
        "message_id": None, # Not announced yet
        "thread_id": None
    }
    return duel


def get_new_duel_id():
    """
    Creates a new unique id to represent a duel
    --
    output:
        res: int
    """
    if "last_duel_id" not in db.keys():
        db["last_duel_id"] = -1
  
    db["last_duel_id"] += 1
    return db["last_duel_id"]


class Duel:
    """
    TODO
    """

    @staticmethod
    def new(id_challenger, id_challenged, amount):
        """
        Creates a new duel
        --
        input:
          id_challenger: int
          id_challenged: int
          amount: int
        --
        output:
          res: Duel
        """
        return None


    def get_dict(self):
        """
        Returns a dict representation of the duel, to be stored in the database
        --
        output:
          res: dict
        """
        return self.dict


    def edit(self, key, val):
        """
        Modifies the dict of the duel
        --
        input:
            key: str
            value: any
        """
        self.dict[key] = val
    

    async def on_accept(self, thread):
        """
        Called when the duel is accepted -> sends the message in the thread
        --
        input:
            thread: interactions.ThreadChannel
        """
        pass
    

    def status(self):
        """
        Returns the status of the duel
        --
        output:
            res: str
        """
        mention = "anyone" if self.dict["user_id2"] == -1 else f"<@{self.dict['user_id2']}>"

        if not self.dict["accepted"]:
            return f"Waiting on {mention} to accept\n"
        else:
            res = ""
            if self.dict["result1"] is None:
                res += f"Waiting on <@{self.dict['user_id1']}> to finish playing\n"
            if self.dict["result2"] is None:
                res += f"Waiting on <@{self.dict['user_id2']}> to finish playing\n"
            return res


    def play(self, user_id, action):
        """
        Edits the dict in response to a user playing
        --
        input:
            user_id: int
            action: any
        """
        pass
    

    def is_over(self):
        """
        Returns True if the duel is over
        --
        output:
            res: bool
        """
        return self.dict["result1"] is not None and self.dict["result2"] is not None


    def get_winner_loser(self):
        """
        Returns the id of the winner and the loser of the duel
        Assumes the duel is over
        Returns None if the duel is a tie
        --
        output:
            winner: int
            loser: int
        """
        return -1, -1
    

    def tie_str(self):
        """
        Returns the string to send when the duel is a tie
        --
        output:
            res: str
        """
        return ""
    

    def win_str(self, winner_id, loser_id):
        """
        Returns the string to send when the duel is won
        --
        input:
            winner_id: int
            loser_id: int
        --
        output:
            res: str
        """
        return ""


class Shifumi_duel(Duel):
    """
    TODO
    """

    def __init__(self, dict):
        self.dict = dict

    
    @staticmethod
    def new(id_challenger, id_challenged, amount):
        return Shifumi_duel(create_duel_dict(id_challenger, id_challenged, amount, "Shifumi"))


    async def on_accept(self, thread):
        await thread.send(f"<@{self.dict['user_id2']}> accepted <@{self.dict['user_id1']}>'s challenge! Use `/duel play shifumi [your move]`")
    

    def play(self, user_id, action):
        user = 1 if user_id == self.dict["user_id1"] else 2
        self.dict[f"result{user}"] = action
    

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
        return f"They both played {self.dict['result1']}!"
        

    def win_str(self, winner_id, loser_id):
        if winner_id == self.dict["user_id1"]:
            return f"They played {self.dict['result1']} vs {self.dict['result2']}!"
        else:
            return f"They played {self.dict['result2']} vs {self.dict['result1']}!"
        