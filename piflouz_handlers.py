from discord.ext import tasks
from random import random, randrange
from replit import db
import functools
import time

from constant import Constants
import events  # Used in eval()
import powerups  # Used in eval()
import utils

 
def update_piflouz(user_id, qty=None, check_cooldown=True):
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
    qty: int -> the amount actually sent/received (only returned if check_cooldown = Try(corresponding to a /get))
  """
  if "piflouz_bank" not in db.keys():
      db["piflouz_bank"] = dict()
    
  user_id = str(user_id)

  # New user
  if user_id not in db["piflouz_bank"].keys():
    db["piflouz_bank"][user_id] = 0
    db["timers_react"][user_id] = 0

  # User already registered
  balance = db["piflouz_bank"][user_id]
  new_time = int(time.time())
  cooldown = utils.get_timer(user_id)

  if check_cooldown:  # corresponding to a /get
    if user_id not in db["powerups"].keys():
      db["powerups"][user_id] = []

    qty = utils.get_total_piflouz_multiplier(user_id)
  else:
    assert qty is not None, "Got qty = None"
  
  if (cooldown == 0 or not check_cooldown) and balance + qty >= 0:
    db["piflouz_bank"][user_id] = balance + qty
    if check_cooldown:
      """
      if user_id not in db["stats"].keys():
        db["stats"][user_id] = {"nb": 0, "times": []}
        
      cooldown = utils.update_with_powerup(Constants.REACT_TIME_INTERVAL, user, "cooldown_reduction")
      differential = abs(db["timers_react"][user_id] + cooldown - new_time)
      
      db["stats"][user_id]["nb"] += 1
      db["stats"][user_id]["times"].append(differential)

      print(db["stats"])
      """
    
      db["timers_react"][user_id] = new_time
      return True, qty
    return True

  if check_cooldown:
    return False, qty
  return False


async def spawn_pibox(bot, piflouz_quantity, custom_message=None, ctx=None):
  """
  Generates a pibox of the amount passed in argument.
  --
  input:
    bot: discord.ext.commands.Bot
    amount: int, positive
    custom_message: either None, or a custom message to add at the end.
    ctx: discord_slash.context.SlashContext -> None if not a giveway
  """
  out_channel = bot.get_channel(db["out_channel"])

  index = randrange(len(Constants.EMOJI_IDS_FOR_PIBOX))
  emoji_id = Constants.EMOJI_IDS_FOR_PIBOX[index]
  emoji_name = Constants.EMOJI_NAMES_FOR_PIBOX[index]
  emoji = f"<:{emoji_name}:{emoji_id}>"

  role = bot.guilds[0].get_role(Constants.PIBOX_NOTIF_ROLE_ID)

  text_output = f"{role.mention} Be Fast ! First to react with {emoji} will get {piflouz_quantity} {Constants.PIFLOUZ_EMOJI} !" 
  if custom_message is not None:
    text_output += " " + custom_message
  if ctx is not None:
    out_channel = ctx.channel # To reply to the sender of a giveaway
  message = await out_channel.send(text_output)
  
  db["random_gifts"][str(message.id)] = [emoji, piflouz_quantity, custom_message]


@tasks.loop(seconds=30)
async def random_gift(bot):
  """
  Generates piflouz gifts randomly
  --
  input:
    bot: discord.ext.commands.Bot
  """
  drop_rate = Constants.PIBOX_DROP_RATE

  # Computing the drop rate based on the current event's powerups
  if "current_event" in db.keys():
    event = eval(db["current_event"])
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


def update_combo(user_id):
  """
  Updates the current combo of the user
  --
  input:
    user_id: int/str
  """
  if str(user_id) not in db["mining_combo"].keys():
    db["mining_combo"][str(user_id)] = 0

  cooldown = utils.get_total_cooldown(user_id)
  old_time = db["timers_react"][str(user_id)]
  current_time = int(time.time())

  if old_time + cooldown <= current_time < old_time + 2 * cooldown:
    db["mining_combo"][str(user_id)] += 1
  
  elif current_time >= old_time + 2 * cooldown:
    db["mining_combo"][str(user_id)] = 0


def get_mining_accuracy_bonus(user_id):
  """
  Returns the piflouz bonus earned from a /get depending on the user accuracy
  --
  input:
    user_id: str/int
  --
  output:
    res: int
  """
  user_id = str(user_id)
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0

  old_time = db["timers_react"][user_id]
  current_time = int(time.time())
  diff = current_time - old_time

  cooldown = utils.get_total_cooldown(user_id)

  if diff < cooldown or diff > 2 * cooldown:
    return 0
  
  t = 1 - (diff - cooldown) / cooldown
  return round(t * Constants.MAX_MINING_ACCURACY_BONUS)

