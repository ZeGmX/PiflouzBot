from discord.ext import tasks
from random import randrange
from random import random
from replit import db
import asyncio
import datetime
import time

from constant import Constants
import embed_messages
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
  if check_cooldown:
    qty = utils.update_with_powerup(qty, user,"multiplier")
  if (cooldown == 0 or not check_cooldown) and balance + qty >= 0:
    db["piflouz_bank"][user_id] = balance + qty
    if check_cooldown:
      db["timers_react"][user_id] = new_time
    return True

  return False


async def spawn_pibox(bot, piflouz_quantity, custom_message=None):
  """
  Generates a pibox of the amount passed in argument.
  --
  input:
    bot: discord.ext.commands.Bot
    amount: int, positive
    custom_message: either None, or a custom message to add at the end.
  """
  out_channel = bot.get_channel(db["out_channel"])

  index = randrange(len(Constants.EMOJI_IDS_FOR_PIBOX))
  emoji_id = Constants.EMOJI_IDS_FOR_PIBOX[index]
  emoji_name = Constants.EMOJI_NAMES_FOR_PIBOX[index]
  emoji = f"<:{emoji_name}:{emoji_id}>"

  text_output = f"Be Fast ! First to react with {emoji} will get {piflouz_quantity} {Constants.PIFLOUZ_EMOJI} !" 
  if custom_message is not None:
    text_output += " " + custom_message
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
  if random() < Constants.RANDOM_DROP_RATE:
    piflouz_quantity = int(Constants.RANDOM_DROP_AVERAGE * random())
    await spawn_pibox(bot,piflouz_quantity)


@tasks.loop(hours=1)
async def miners_action(bot):
  """
  Generate the action of miners, adding the amount to the users balance
  --
  input:
    bot: discord.ext.commands.Bot
  """
  now = datetime.datetime.now()
  then = now + datetime.timedelta(hours=1)
  then = datetime.datetime(then.year, then.month, then.day, then.hour, then.minute, then.second)
  dt = then - now
  await asyncio.sleep(dt.total_seconds() % 3600)
  
  print("Updating miners") #TODO remove once checked in more detail on live server
  if "powerups" in db.keys():
    for user_id,powerups in db["powerups"].items():
      nb_miners = powerups["miners"]
      user = await bot.guilds[0].fetch_member(user_id)
      qty = nb_miners * Constants.POWERUP_MINER_PIFLOUZ
      update_piflouz(user, qty, check_cooldown=False)
  await utils.update_piflouz_message(bot)


async def daily_raffle(bot):
  """
  Generates a new raffle and ends the previous one
  --
  input:
    bot: discord.ext.commands.Bot
  """
  if "out_channel" not in db.keys():
    return
  
  message_exists = False
  out_channel = bot.get_channel(db["out_channel"])
  if "last_raffle_message" in db.keys():
    message_exists = True
    message = await out_channel.fetch_message(db["last_raffle_message"])
    del db["last_raffle_message"]
    await message.unpin()
  
  # Computing the winner for the last raffle
  if message_exists and len(db["raffle_participation"]) > 0:
    
    total_tickets = sum(db["raffle_participation"].values())
    winning_index = randrange(0, total_tickets)
    
    partial_sum = 0
    for id, value in db["raffle_participation"].items():
      if partial_sum <= winning_index < partial_sum + value:
        break
      partial_sum += value
    
    prize = utils.get_raffle_total_prize()
    db["raffle_participation"] = dict()

    member = await bot.guilds[0].fetch_member(id)
    message = f"Congratulations to <@{member.id}> for winning the raffle, earning {prize} {Constants.PIFLOUZ_EMOJI}!"

    update_piflouz(member, prize, check_cooldown=False)
    await out_channel.send(message)
    
    await utils.update_piflouz_message(bot)
  
  # Starting new raffle
  embed = await embed_messages.get_embed_raffle(bot)
  message = await out_channel.send(embed=embed)
  db["last_raffle_message"] = message.id
  await message.pin()


@tasks.loop(hours=24)
async def check_daily_raffle(bot):
  """
  Checks the raffle once a day
  --
  input:
    bot: discord.ext.commands.Bot
  """
  now = datetime.datetime.now()
  then = Constants.RAFFLE_TIME
  then = datetime.datetime(now.year, now.month, now.day, then.hour, then.minute, then.second)

  dt = then - now

  print("time remaining: ", dt.total_seconds() % (24 * 3600))
  await asyncio.sleep(dt.total_seconds() % (24 * 3600))
  await daily_raffle(bot)
