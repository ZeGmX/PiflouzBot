import time

from constant import Constants
from custom_task_triggers import TaskCustom as Task
from my_database import db
from piflouz_generated import Piflouz_source, add_to_stat
import piflouz_handlers
import user_profile
import utils


@Task.create(Constants.EVERY_HOUR_TRIGGER)
async def handle_actions_every_hour(bot):
    """
    Callback for handling powerups that have an action every hour (such as miners)
    --
    input:
        bot: interactions.Client
    """
    print("handling hourly powerups")

    for user_id, profile in user_profile.get_active_profiles().items():
        powerups = profile["powerups"]
        for powerup_str in powerups:
            # Removing the '__name__.' at the beginning
            powerup = eval(powerup_str[len(__name__) + 1:])
            if powerup.has_action_every_hour:
                powerup.actions_every_hour(user_id)
    await utils.update_piflouz_message(bot)


class Powerups:
    """
    Base class for the powerups, inherited by every powerup class
    """
    has_action_every_hour = False

    def get_cooldown_multiplier_value(self):
        """
        Returns the piflouz multiplier value of the powerup
        --
        output:
            res: float
        """
        return 1
    
    
    def get_piflouz_multiplier_value(self):
        """
        Returns the cooldown reduction value of the powerup
        --
        output:
            res: float
        """
        return 1
    
    
    def get_pibox_rate_multiplier_value(self):
        """
        Returns the pibox rate multiplier of the powerup
        --
        output:
            res: float
        """
        return 1


    def get_pibox_reward_multiplier_value(self):
        """
        Returns the pibox size multiplier of the powerup
        --
        output:
            res: float
        """
        return 1


    def get_max_combo_increase(self):
        """
        Returns the max combo increase of the powerup
        --
        output:
            res: int
        """
        return 0


    def get_combo_reward_multiplier(self):
        """
        Returns the combo reward multiplier of the powerup
        --
        output:
            res: int
        """
        return 1

    
    def get_store_price_multiplier(self):
        """
        Returns the store price multiplier of the powerup
        --
        output:
            res: int
        """
        return 1
    

    def get_info_str(self):
        """
        Returns the string to be shown in /powerups when the powerup is active
        --
        output:
            res: str
        """
        return ""
    
    
    def get_store_str(self):
        """
        Returns the string to be shown in /store embed if the powerup is in the store
        --
        output:
            res: str
        """
        return ""


    def get_event_str(self):
        """
        Returns the string to be shown when the powerup is part of an event
        --
        output:
            res: str
        """
        return self.get_info_str()


    def to_str(self):
        """
        Returns the string used for recreating the object with eval()
        --
        output:
            res: str
        """
        return ""


    def on_buy(self, user_id, current_time):
        """
        Actions to be done when buying the powerup
        --
        input:
            user_id: int/str -> id of the user who bought the powerup
            current_time: int -> when the interaction was created
        --
        output:
            res: bool -> wether it succeded or not
        """
        return False
    

    def actions_every_hour(self, user_id):
        """
        Callback if a powerup has an effect every hour
        --
        input:
            user_id: int/str
        """
        pass


class Powerups_non_permanent(Powerups):
    """
    Non permanent powerups
    """
    def __init__(self, price, value, duration, buy_date=0):
        self.price = price
        self.value = value
        self.duration = duration
        self.buy_date = buy_date
    
    
    def on_buy(self, user_id, current_time):
        user_id = str(user_id)
        profile = user_profile.get_profile(user_id)
                    
        i = None
        for current, powerup_str in enumerate(profile["powerups"]):
            if powerup_str.startswith(f"{__name__}.{type(self).__name__}"):
                i = current
                break

        # Remove the '__name__.' at the begining
        if i is not None and eval(profile["powerups"][i][len(__name__) + 1:]).is_active():
            return False  # User already has an active power of the same type
        
        self.buy_date = current_time
        powerup_str = self.to_str()

        if not piflouz_handlers.update_piflouz(user_id, qty=-self.price, check_cooldown=False):
            return False

        if i is not None:
            del profile["powerups"][i]
        profile["powerups"].append(powerup_str)

        return True


    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.price}, {self.value}, {self.duration}, {self.buy_date})"


    def is_active(self):
        return self.duration is None or time.time() - self.buy_date <= self.duration


class Cooldown_reduction(Powerups_non_permanent):
    """
    Cooldown reduction powerup
    The powerup is multiplicative
    """
    def get_cooldown_multiplier_value(self):
        return 1 - self.value / 100 if self.is_active() else 1
    

    def get_info_str(self):
        dt = self.duration - int(time.time()) + self.buy_date
        if dt >= 0:
            sign = "+" if self.value < 0 else ""
            return f"Cooldown • {sign}{-self.value}%\nTime left: {utils.seconds_to_formatted_string(dt)}"
        return ""


    def get_event_str(self):
        sign = "+" if self.value < 0 else ""
        return f"Cooldown • {sign}{-self.value}%"
    

    def get_store_str(self):
        return f"{self.value}% cooldown reduction for the piflouz mining!\nCosts {self.price} {Constants.PIFLOUZ_EMOJI}"


class Piflouz_multiplier(Powerups_non_permanent):
    """
    Piflouz multiplier for /get powerup
    The powerup is multiplicative
    """
    def get_piflouz_multiplier_value(self):
        return 1 + self.value / 100 if self.is_active() else 1
    

    def get_info_str(self):
        dt = self.duration - int(time.time()) + self.buy_date
        if dt >= 0:
            sign = "+" if self.value > 0 else ""
            return f"Piflouz multiplier • {sign}{self.value}%\nTime left: {utils.seconds_to_formatted_string(dt)}"
        return ""


    def get_event_str(self):
        sign = "+" if self.value > 0 else ""
        return f"Piflouz multiplier • {sign}{self.value}%"
    

    def get_store_str(self):
        return f"{self.value}% multiplier for the piflouz mining!\nCosts {self.price} {Constants.PIFLOUZ_EMOJI}"

class Birthday_Multiplier(Piflouz_multiplier):
    """
    Birthday piflouz multiplier.
    Should only be called in very specific conditions.
    """
    def get_info_str(self):
        dt = self.duration - int(time.time()) + self.buy_date
        if dt >= 0:
            sign = "+" if self.value > 0 else ""
            return f"Birthday multiplier • {sign}{self.value}%\nTime left: {utils.seconds_to_formatted_string(dt)}"
        return ""


    def get_event_str(self):
        return "This is a bug :eyes:. This should not be used in a event. If you see this message, please signal it."


    def get_store_str(self):
        return "This is a bug :eyes:. This powerup shouldn't be in the store. Please signal this if you see it."

class Powerups_permanent(Powerups):
    """
    Permanent powerups
    """
    def __init__(self, price, value, max_qty, qty=0):
        self.price = price
        self.value = value
        self.qty = qty  # How many of this powerup does the user have
        self.max_qty = max_qty  # How many of this powerup can the user get
    

    def on_buy(self, user_id, current_time):
        user_id = str(user_id)
        profile = user_profile.get_profile(user_id)
                    
        i = None
        for current, powerup_str in enumerate(profile["powerups"]):
            if powerup_str.startswith(f"{__name__}.{type(self).__name__}"):
                i = current
                self.qty = eval(profile["powerups"][i][len(__name__) + 1:]).qty
                break

        # Remove the '__name__.' at the begining
        if i is not None and eval(profile["powerups"][i][len(__name__) + 1:]).qty == self.max_qty:
            return False  # User already has the maximum number of this powerup
        
        self.qty += 1
        powerup_str = self.to_str()

        if not piflouz_handlers.update_piflouz(user_id, qty=-self.price, check_cooldown=False):
            return False

        if i is not None:
            del profile["powerups"][i]
        profile["powerups"].append(powerup_str)

        return True

    
    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.price}, {self.value}, {self.max_qty}, {self.qty})"


    def is_active(self):
        return True
    

class Miner_powerup(Powerups_permanent):
    """
    Piflouz auto-miner powerup
    Piflouz are earned every hour
    """

    has_action_every_hour = True

    def get_info_str(self):
        if self.qty == 0:
            return ""
        return f"Miners • {self.qty}\nExpires at the end of the season"


    def get_store_str(self):
        return f"Piflouz auto-miner! Earn {self.value} {Constants.PIFLOUZ_EMOJI} every hour\nYou can only have {self.max_qty} auto-miners\nCosts {self.price} {Constants.PIFLOUZ_EMOJI}"
    

    def actions_every_hour(self, user_id):
        user_id = str(user_id)
        piflouz_earned = self.value * self.qty
        piflouz_handlers.update_piflouz(user_id, qty=piflouz_earned, check_cooldown=False)
        add_to_stat(piflouz_earned, Piflouz_source.MINER)


class Pibox_drop_rate_multiplier(Powerups_permanent):
    """
    Powerup that changes the drop rate of piboxes
    Should only be used in events
    The powerup is multiplicative
    """
    def __init__(self, value):
        self.value = value
    

    def get_pibox_rate_multiplier_value(self):
        return 1 + self.value / 100
    

    def get_info_str(self):
        sign = "+" if self.value > 0 else ""
        return f"Pibox drop rate • {sign}{self.value}%"
    

    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.value})"


class Combo_max_increase(Powerups_permanent):
    """
    Powerup that changes the maximum rewardable combo
    Should only be used in events
    The powerup is additive
    """
    def __init__(self, value):
        self.value = value
    

    def get_max_combo_increase(self):
        return self.value
    

    def get_info_str(self):
        sign = "+" if self.value > 0 else ""
        return f"Maximum rewardable combo • {sign}{self.value}"
    

    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.value})"


class Combo_reward_multiplier(Powerups_permanent):
    """
    Powerup that changes the reward for each combo
    Should only be used in events
    The powerup is multiplicative
    """
    def __init__(self, value):
        self.value = value
    
    
    def get_combo_reward_multiplier(self):
        return 1 + self.value / 100
    
    
    def get_info_str(self):
        sign = "+" if self.value > 0 else ""
        return f"Combo reward multiplier • {sign}{self.value}%"
    
    
    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.value})"


class Pibox_size_multiplier(Powerups_permanent):
    """
    Powerup that changes the max pibox reward 
    Should only be used in events
    The powerup is multiplicative
    """
    def __init__(self, value):
        self.value = value
    

    def get_pibox_reward_multiplier_value(self):
        return 1 + self.value / 100


    def get_info_str(self):
        sign = "+" if self.value > 0 else ""
        return f"Pibox reward • {sign}{self.value}%"


    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.value})"


class Store_price_multiplier(Powerups_permanent):
    """
    Powerup that changes the price of items in the store
    Should only be used in events
    The powerup is multiplicative
    """
    def __init__(self, value):
        self.value = value
    

    def get_store_price_multiplier(self):
        return 1 - self.value / 100
    

    def get_info_str(self):
        sign = "+" if self.value < 0 else ""
        return f"Store price • {sign}{-self.value}%"
    

    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.value})"