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


def get_live_status(user_name):
  """
  Sends a request to the twich API about a streamer
  --
  input:
    user_name: string -> name of the streamer
  --
  output:
    r: dict -> request
  """
  API_ENDPOINT = f"https://api.twitch.tv/helix/streams?user_login={user_name}"
  head = {
    'client-id': os.getenv("TWITCHID"),
    'authorization': 'Bearer ' + os.getenv("TWITCHTOKEN")
  }
  return requests.get(url=API_ENDPOINT, headers=head).json()


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


def get_timer(user):
  """
  This function returns the amount of time needed before being able to earn more piflouz
  --
  input:
    user: discord.Member/User
  --
  output:
    time_needed: int -> time remaining before the end of cooldown
  """
  user_id = str(user.id)
  if "timers_react" not in db.keys():
    db["timers_react"] = dict()
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0

  if str(user.id) not in db["powerups"].keys():
    db["powerups"][str(user.id)] = []

  old_time = db["timers_react"][user_id]
  current_time = int(time.time())
  differential = current_time - old_time
  cooldown = functools.reduce(lambda cumul, powerup_str: cumul * eval(powerup_str).get_cooldown_multiplier_value(), db["powerups"][str(user.id)], Constants.REACT_TIME_INTERVAL)

  time_needed = max(0, cooldown - differential)
  
  return time_needed

# TODO: deprecated?
def check_tag(tag):
  """
  Checks if a tag corresponds to a user mention
  --
  input:
    tag: str -> the string version of the tag
  """
  # Desktop version
  if tag.startswith("<@!") and tag.endswith(">") and is_digit(tag[3:-1]):
    return int(tag[3:-1])
  # Phone version
  elif tag.startswith("<@") and tag.endswith(">") and is_digit(tag[2:-1]):
    return int(tag[2:-1])
  return None


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


# TODO: deprecated?
def is_digit(var):
  """
  Checks if a string only contains numbers
  --
  input:
    var: str
  --
  output:
    res: bool
  """
  return all(char in "0123456789" for char in var)

# TODO: deprecated?    
async def react_and_delete(message, reaction="❌", t=Constants.TIME_BEFORE_DELETION):
  """
  Eventually reacts to a message and deletes it a few seconds later
  --
  input:
    message: discord.Message -> message to be deleted
    reaction: string/discord.emoji -> reaction to add
    t: int -> number of seconds to wait before deletion
  """
  if reaction is not None:
    await message.add_reaction(reaction)
  await asyncio.sleep(t)
  await message.delete()


def create_duel(ctx, user, amount, duel_type):
  """
  TODO
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