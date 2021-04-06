from discord.ext import tasks
from random import randrange
from random import random
from replit import db
import time

from constant import Constants
import utils


@tasks.loop(seconds=30)
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


@tasks.loop(seconds=30)
async def update_rank_pilord(client):
  """
  Changes the rank of the players with the most piflouz
  --
  input:
    client: discord.client
  """
  if "piflouz_bank" not in db.keys():
    return
  
  guild = client.guilds[0]
  role = guild.get_role(Constants.PILORD_ROLE_ID)

  L = sorted(list(db["piflouz_bank"].items()), key=lambda key_val: -int(key_val[1]))
  # in case of ties
  L = list(filter(lambda key_val: key_val[1] == L[0][1], L))
  user_ids = [key_val[0] for key_val in L]

  if "current_pilords" in db.keys():
    # Remove old pilords
    for user_id in db["current_pilords"]:
      if user_id not in user_ids:
        member = await guild.fetch_member(user_id)
        await member.remove_roles(role)

    # Setup new pilords
    for user_id, amount in L:
      if user_id not in db["current_pilords"]:
        user = await guild.fetch_member(user_id)
        await user.add_roles(role)
    
    db["current_pilords"] = user_ids

