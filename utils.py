import requests
import time
import datetime
import os
import asyncio
from replit import db
import functools

from constant import Constants
import embed_messages
import powerups  # Used in eval()


def get_new_joke():
  """
  Checks a joke API to format a new random joke
  --
  output:
    joke: str -> the formatted joke
  """
  r = requests.get("https://official-joke-api.appspot.com/random_joke").json()
  joke = r["setup"] + "\n||**" + r["punchline"] + "**||"
  return joke


def get_timer(user_id):
  """
  This function returns the amount of time needed before being able to earn more piflouz
  --
  input:
    user_id: int/str
  --
  output:
    time_needed: int -> time remaining before the end of cooldown
  """
  user_id = str(user_id)
  if "timers_react" not in db.keys():
    db["timers_react"] = dict()
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0

  if user_id not in db["powerups"].keys():
    db["powerups"][user_id] = []

  old_time = db["timers_react"][user_id]
  current_time = int(time.time())
  differential = current_time - old_time
  cooldown = functools.reduce(lambda cumul, powerup_str: cumul * eval(powerup_str).get_cooldown_multiplier_value(), db["powerups"][user_id], Constants.REACT_TIME_INTERVAL)

  time_needed = max(0, cooldown - differential)
  
  return int(time_needed)


async def update_piflouz_message(bot):
  """
  Updates the piflouz message with the rankings
  --
  input:
    bot: discord.ext.commands.Bot
  """
  channel = bot.get_channel(db["out_channel"])
  embed = await embed_messages.get_embed_piflouz(bot)
  piflouz_message = await channel.fetch_message(db["piflouz_message_id"])
  await piflouz_message.edit(embed=embed)


def create_duel(ctx, user, amount, duel_type):
  """
  Generates a new duel
  --
  input:
    ctx: discord.ext.commands.Context
    user: discord.User/Member
    amount: int
    duel_type: str
  --
  output:
    duel: dict
  """
  duel = {
    "user_id1": ctx.author_id, # Challenger
    "user_id2": user.id, # Challenged
    "duel_type": duel_type,
    "amount": amount,
    "move1": None, # Not played yet
    "move2": None, # Not played yet
    "accepted": False # Not accepted yet
  }
  return duel


async def wait_until(then):
  """
  Waits until a certain time of the day (or the next day)
  --
  input:
    then: datetime.datetime
  """
  now = datetime.datetime.now()
  then = datetime.datetime(now.year, now.month, now.day, then.hour, then.minute, then.second)

  dt = then - now

  print("Waiting for:", dt.total_seconds() % (24 * 3600))
  await asyncio.sleep(dt.total_seconds() % (24 * 3600))