import time
import datetime
import asyncio
from discord.ext import tasks
from replit import db

from constant import Constants
import piflouz_handlers
import utils


@tasks.loop(hours=1)
async def handle_actions_every_hour(bot):
  """
  Callback for handling powerups that have an action every hour (such as miners)
  --
  input:
    bot: discord.ext.commands.Bot
  """
  # Waiting for the next hour
  now = datetime.datetime.now()
  then = now + datetime.timedelta(hours=1)
  then = datetime.datetime(then.year, then.month, then.day, then.hour, 0, 0)
  dt = then - now
  await asyncio.sleep(dt.total_seconds() % 3600)

  print("handling hourly powerups")

  for user_id, powerups in db["powerups"].items():
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


  def to_str(self):
    """
    Returns the string used for recreating the object with eval()
    --
    output:
      res: str
    """
    return ""


  def on_buy(self, user_id):
    """
    Actions to be done when buying the powerup
    --
    input:
      user_id: int/str -> id of the user who bought the powerup
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
  
  def on_buy(self, user_id):
    user_id = str(user_id)
    if user_id not in db["powerups"].keys():
        db["powerups"][user_id] = []
          
    i = None
    for current, powerup_str in enumerate(db["powerups"][user_id]):
      if powerup_str.startswith(f"{__name__}.{type(self).__name__}"):
        i = current
        break

    # Remove the '__name__.' at the begining
    if i is not None and eval(db["powerups"][user_id][i][len(__name__) + 1:]).is_active():
      return False  # User already has an active power of the same type
    
    self.buy_date = int(time.time())
    powerup_str = self.to_str()

    if not piflouz_handlers.update_piflouz(user_id, qty=-self.price, check_cooldown=False):
      return False

    if i is not None:
      del db["powerups"][user_id][i]
    db["powerups"][user_id].append(powerup_str)

    return True


  def to_str(self):
    return f"{__name__}.{type(self).__name__}({self.price}, {self.value}, {self.duration}, {self.buy_date})"


  def is_active(self):
    return self.duration is None or time.time() - self.buy_date <= self.duration


class Cooldown_reduction(Powerups_non_permanent):
  """
  Cooldown reduction powerup
  Powerup is multiplicative
  """
  def get_cooldown_multiplier_value(self):
    return 1 - self.value / 100 if self.is_active() else 1
  

  def get_info_str(self):
    if self.duration is None:
      return f"Cooldown reduction - {self.value}%"

    dt = self.duration - int(time.time()) + self.buy_date
    if dt >= 0:
      return f"Cooldown reduction - {self.value}% - Time left: {utils.seconds_to_formatted_string(dt)}"
    return ""
  

  def get_store_str(self):
    return f"{self.value}% cooldown reduction for the piflouz mining!\nCosts {self.price} {Constants.PIFLOUZ_EMOJI}"


class Piflouz_multiplier(Powerups_non_permanent):
  """
  Piflouz multiplier for /get powerup
  Powerup is multiplicative
  """
  def get_piflouz_multiplier_value(self):
    return 1 + self.value / 100 if self.is_active() else 1
  

  def get_info_str(self):
    if self.duration is None:
      return f"Piflouz multiplier - {self.value}%"

    dt = self.duration - int(time.time()) + self.buy_date
    if dt >= 0:
      return f"Piflouz multiplier - {self.value}% - Time left: {utils.seconds_to_formatted_string(dt)}"
    return ""
  

  def get_store_str(self):
    return f"{self.value}% multiplier for the piflouz mining!\nCosts {self.price} {Constants.PIFLOUZ_EMOJI}"


class Powerups_permanent(Powerups):
  """
  Permanent powerups
  """
  def __init__(self, price, value, max_qty, qty=0):
    self.price = price
    self.value = value
    self.qty = qty  # How many of this powerup does the user have
    self.max_qty = max_qty  # How many of this powerup can the user get
  
  def on_buy(self, user_id):
    user_id = str(user_id)
    if user_id not in db["powerups"].keys():
        db["powerups"][user_id] = []
          
    i = None
    for current, powerup_str in enumerate(db["powerups"][user_id]):
      if powerup_str.startswith(f"{__name__}.{type(self).__name__}"):
        i = current
        self.qty = eval(db["powerups"][user_id][i][len(__name__) + 1:]).qty
        break

    # Remove the '__name__.' at the begining
    if i is not None and eval(db["powerups"][user_id][i][len(__name__) + 1:]).qty == self.max_qty:
      return False  # User already has the maximum number of this powerup
    
    powerup_str = self.to_str()

    if not piflouz_handlers.update_piflouz(user_id, qty=-self.price, check_cooldown=False):
      return False

    if i is not None:
      del db["powerups"][user_id][i]
    db["powerups"][user_id].append(powerup_str)

    return True

  
  def to_str(self):
    return f"{__name__}.{type(self).__name__}({self.price}, {self.value}, {self.max_qty}, {self.qty + 1})"


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
    return f"Miners - {self.qty} - Permanent"


  def get_store_str(self):
    return f"Piflouz auto-miner! Earn {self.value} {Constants.PIFLOUZ_EMOJI} every hour\nYou can only have {self.max_qty} auto-miners\nCosts {self.price} {Constants.PIFLOUZ_EMOJI}"
  

  def actions_every_hour(self, user_id):
    user_id = str(user_id)
    piflouz_earned = self.value * self.qty
    piflouz_handlers.update_piflouz(user_id, qty=piflouz_earned, check_cooldown=False)


class Pibox_drop_rate_multiplier(Powerups_permanent):
  """
  Powerup that changes the drop rate of piboxes
  Should only be used in events
  """
  def __init__(self, value):
    self.value = value
  

  def get_pibox_rate_multiplier_value(self):
    return 1 + self.value / 100
  

  def get_info_str(self):
    return f"Increased pibox drop rate - {self.value}%"
  

  def to_str(self):
    return f"{__name__}.{type(self).__name__}({self.value})"