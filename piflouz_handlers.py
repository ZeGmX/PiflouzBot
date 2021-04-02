from discord.ext import tasks
from random import randrange
from random import random
from replit import db
import time

from constant import Constants
import utils


@tasks.loop(seconds=3)
async def random_gift(client):
  """
  Generates piflouz gifts randomly
  --
  input:
    client: discord.Client
  """
  if random() < Constants.RANDOM_DROP_RATE:
    piflouz_quantity = int(Constants.RANDOM_DROP_AVERAGE*random())

    out_channel = client.get_channel(db["out_channel"])

    emoji_id, emoji = Constants.EMOJI_DATABASE[randrange(len(Constants.EMOJI_DATABASE))]  

    message = await out_channel.send(f"Be Fast ! First to react with {emoji} will get {piflouz_quantity} {Constants.PIFLOUZ_EMOJI} !")
    
    db["random_gifts"][str(message.id)] = [emoji, piflouz_quantity]
    

def update_piflouz(user, qty=Constants.NB_PIFLOUZ_PER_REACT, check_cooldown=True):
  """
  This function does the generic piflouz mining, and returns wether it suceeded or not
  --
  input:
    user: discord.User -> the person who reacted
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
    db["timers_react"][user_id] = int(time.time())
    return True

  # User already registered
  balance = db["piflouz_bank"][user_id]
  new_time = int(time.time())
  cooldown = utils.get_timer(user)
  if cooldown == 0 or not check_cooldown:
    db["piflouz_bank"][user_id] = balance + qty
    if check_cooldown:
      db["timers_react"][user_id] = new_time
    return True

  return False
    