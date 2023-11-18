from random import random, randrange
import functools
from interactions import IntervalTrigger

from constant import Constants
from custom_task_triggers import TaskCustom as Task
import events.events  # Used in eval()
from my_database import db
import powerups  # Used in eval()
import utils

 
def update_piflouz(user_id, qty=None, check_cooldown=True, current_time=None):
  """
  This function does the generic piflouz mining, and returns wether it suceeded or not
  --
  input:
    user_id: int/str -> id of the person who reacted
    qty: int -> number of piflouz (not necesseraly positive)
    check_cooldown: boolean -> if we need to check the cooldown (for the piflouz mining)
  --
  output:
    res: boolean -> if the update succeded
    qty: int -> the amount actually sent/received (only returned if check_cooldown = True (corresponding to a /get))
    current_time: int -> the time at which the interaction was created
  """
  if "piflouz_bank" not in db.keys():
      db["piflouz_bank"] = dict()
    
  user_id = str(user_id)

  # New user
  if user_id not in db["piflouz_bank"].keys():
    db["piflouz_bank"][user_id] = 0
    db["timers_react"][user_id] = 0

  balance = db["piflouz_bank"][user_id]

  if check_cooldown:  # corresponding to a /get
    assert current_time is not None, "Got current_time = None"

    cooldown = utils.get_timer(user_id, current_time)
    qty = get_total_piflouz_earned(user_id, current_time)
  else:
    assert qty is not None, "Got qty = None"
  
  if (not check_cooldown or cooldown == 0) and balance + qty >= 0:
    db["piflouz_bank"][user_id] = balance + qty
    if check_cooldown:
      db["timers_react"][user_id] = current_time
      return True, qty
    return True

  if check_cooldown:
    return False, qty
  return False


async def spawn_pibox(bot, piflouz_quantity, custom_message=None):
  """
  Generates a pibox of the amount passed in argument.
  --
  input:
    bot: interactions.Client
    amount: int, positive
    custom_message: either None, or a custom message (str) to add at the end.
  """
  out_channel = await bot.fetch_channel(db["out_channel"])

  index = randrange(len(Constants.EMOJI_IDS_FOR_PIBOX))
  emoji_id = Constants.EMOJI_IDS_FOR_PIBOX[index]
  emoji_name = Constants.EMOJI_NAMES_FOR_PIBOX[index]
  emoji = f"<:{emoji_name}:{emoji_id}>"

  role = await bot.guilds[0].fetch_role(Constants.PIBOX_NOTIF_ROLE_ID)

  text_output = f"{role.mention} Be Fast ! First to react with {emoji} will get {piflouz_quantity} {Constants.PIFLOUZ_EMOJI} !" 
  if custom_message is not None:
    text_output += " " + custom_message
  message = await out_channel.send(text_output)
  
  db["random_gifts"][str(message.id)] = [emoji_id, piflouz_quantity, custom_message]


@Task.create(IntervalTrigger(seconds=30))
async def random_gift(bot):
  """
  Generates piflouz gifts randomly
  --
  input:
    bot: discord.ext.commands.Bot
  """
  drop_rate = Constants.PIBOX_DROP_RATE

  # Computing the drop rate based on the current event's powerups
  if "current_event_passive" in db.keys():
    event = eval(db["current_event_passive"])
    powerups_list = event.get_powerups()
    drop_rate = functools.reduce(lambda accu, powerup: accu * powerup.get_pibox_rate_multiplier_value(), powerups_list, drop_rate)
  
  if random() < drop_rate:
    # Main piflouz
    piflouz_quantity = randrange(Constants.MAX_PIBOX_AMOUNT)
    await spawn_pibox(bot, piflouz_quantity)

  if random() < drop_rate:
    # Piflouz with the bot's money
    piflouz_quantity = randrange(Constants.MAX_PIBOX_AMOUNT)
    if update_piflouz(bot.user.id, qty=-piflouz_quantity, check_cooldown=False):
      await spawn_pibox(bot, piflouz_quantity, custom_message=f"{bot.user.mention} spawned it with its own {Constants.PIFLOUZ_EMOJI}!")


def update_combo(user_id, current_time):
  """
  Updates the current combo of the user
  --
  input:
    user_id: int/str
    current_time: int
  """
  if str(user_id) not in db["mining_combo"].keys():
    db["mining_combo"][str(user_id)] = 0

  cooldown = utils.get_total_cooldown(user_id)
  old_time = db["timers_react"][str(user_id)]

  if old_time + cooldown <= current_time < old_time + 2 * cooldown:
    db["mining_combo"][str(user_id)] += 1
  
  elif current_time >= old_time + 2 * cooldown:
    db["mining_combo"][str(user_id)] = 0


def get_mining_accuracy_bonus(user_id, current_time):
  """
  Returns the piflouz bonus earned from a /get depending on the user accuracy
  --
  input:
    user_id: str/int
    current_time: int -> the time at which the interaction was created
  --
  output:
    res: int
  """
  user_id = str(user_id)
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0

  old_time = db["timers_react"][user_id]
  diff = current_time - old_time

  cooldown = utils.get_total_cooldown(user_id)

  if diff < cooldown or diff > 2 * cooldown:
    return 0
  
  t = 1 - (diff - cooldown) / cooldown
  return round(t * Constants.MAX_MINING_ACCURACY_BONUS)


def get_max_rewardable_combo(user_id):
  """
  Returns the maximum rewardable combo for a given user
  --
  input:
    user_id: int/str
  --
  output:
    res: int
  """
  current_event = eval(db["current_event_passive"])
  powerups_user = [eval(p) for p in db["powerups"][str(user_id)]]
  powerups_event = current_event.get_powerups()
  all_powerups = powerups_user + powerups_event
  return round(Constants.MAX_MINING_COMBO + sum(p.get_max_combo_increase() for p in all_powerups))


def get_total_piflouz_earned(user_id, current_time):
  """
  Returns the amount earned with a /get, taking into account the user powerups, the current event, the user combo and the accuracy
  --
  input:
    user_id: int/str - the id of the user having the powerups
    current_time: int -> the time at which the interaction was created
  --
  output:
    qty: the pilouz amount
  """
  if str(user_id) not in db["mining_combo"].keys():
    db["mining_combo"][str(user_id)] = 0

  current_event = eval(db["current_event_passive"])
  powerups_user = [eval(p) for p in db["powerups"][str(user_id)]]
  powerups_event = current_event.get_powerups()
  all_powerups = powerups_user + powerups_event

  qty = Constants.BASE_MINING_AMOUNT * (1 + sum(p.get_piflouz_multiplier_value() - 1 for p in all_powerups))
  qty = round(qty)

  max_combo = get_max_rewardable_combo(user_id)

  combo_bonus = min(db["mining_combo"][str(user_id)], max_combo) * Constants.BASE_PIFLOUZ_PER_MINING_COMBO * (1 + sum(p.get_combo_reward_multiplier() - 1 for p in all_powerups))
  combo_bonus = round(combo_bonus)

  return qty + combo_bonus + get_mining_accuracy_bonus(user_id, current_time)
