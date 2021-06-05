from discord.ext import tasks
from random import randrange
from random import random
from replit import db
import functools
import time

from constant import Constants
import events  # Used in eval()
import powerups  # Used in eval()
import utils

 
def update_piflouz(user, qty=Constants.NB_PIFLOUZ_PER_REACT, check_cooldown=True):
  """
  This function does the generic piflouz mining, and returns wether it suceeded or not
  --
  input:
    user: discord.User -> the person who reacted
    qty: int -> number of piflouz (not necesseraly positive)
    check_cooldown: boolean -> if we need to check the cooldown (for the piflouz mining)
  --
  output:
    res: boolean -> if the update succeded
  """
  if "piflouz_bank" not in db.keys():
      db["piflouz_bank"] = dict()
    
  user_id = str(user.id)

  # New user
  if user_id not in db["piflouz_bank"].keys():
    db["piflouz_bank"][user_id] = qty
    db["timers_react"][user_id] = 0
    return True

  # User already registered
  balance = db["piflouz_bank"][user_id]
  new_time = int(time.time())
  cooldown = utils.get_timer(user)

  if check_cooldown:  # corresponding to a /get
    if str(user.id) not in db["powerups"].keys():
      db["powerups"][str(user.id)] = []

    qty = functools.reduce(lambda accu, powerup_str: accu * eval(powerup_str).get_piflouz_multiplier_value(), db["powerups"][str(user.id)], qty)
    qty = int(qty)
  
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
    return True

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
  drop_rate = Constants.RANDOM_DROP_RATE

  # Computing the drop rate based on the current event's powerups
  if "current_event" in db.keys():
    event = eval(db["current_event"])
    powerups_list = event.get_powerups()
    drop_rate = functools.reduce(lambda accu, powerup: accu * powerup.get_pibox_rate_multiplier_value(), powerups_list, drop_rate)
  
  if random() < drop_rate:
    # Main piflouz
    piflouz_quantity = int(Constants.RANDOM_DROP_AVERAGE * random())
    await spawn_pibox(bot, piflouz_quantity)

  if random() < drop_rate:
    # Piflouz with the bot's money
    piflouz_quantity = int(Constants.RANDOM_DROP_AVERAGE * random())
    if update_piflouz(bot.user, qty=-piflouz_quantity, check_cooldown=False):
      await spawn_pibox(bot, piflouz_quantity, custom_message=f"{bot.user.mention} spawned it with its own {Constants.PIFLOUZ_EMOJI}!")

