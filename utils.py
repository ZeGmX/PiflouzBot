import requests
import time
import os
import asyncio
from replit import db

from constant import Constants
import embed_messages

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

def update_with_powerup(base_value,user,powerup_type):
  """
  This function returns the modificator for a user, according to the powerup_type asked
  --
  input:
    base_value: int, the amount of piflouz/time needed according to the powerup type
    user: discord.Member/User
    powerup_type: string
  """
  user_id = str(user.id)  
  if user_id not in db["powerups"]:
    db["powerups"][user_id] ={
        "multiplier": [0, 0], # Effect, limit time
        "cooldown_reduction" : [0, 0], # Effect, limit time
        "miners": 0 
      }
  current_time = int(time.time())

  if powerup_type == "multiplier" :
    if db["powerups"][user_id][powerup_type][1] >= current_time:
      new_value = (base_value * (1 +  db["powerups"][user_id][powerup_type][0]/100))
      return int(new_value)
    else:
      return int(base_value)

  elif powerup_type == "cooldown_reduction":
    if db["powerups"][user_id][powerup_type][1] >= current_time:
      new_value = (base_value * (1 - db["powerups"][user_id][powerup_type][0]/100 ))
      return int(new_value)
    else:
      return int(base_value)


def get_timer(user):
  """
  This function returns the amount of time needed before being able to earn more piflouz
  --
  input:
    user: discord.Member/User
  """
  user_id = str(user.id)
  if "timers_react" not in db.keys():
      db["timers_react"] = dict()
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0


  old_time = db["timers_react"][user_id]
  current_time = int(time.time())
  differential = current_time - old_time
  cooldown = update_with_powerup( Constants.REACT_TIME_INTERVAL, user, "cooldown_reduction")
  time_needed = max(0, cooldown - differential)
  
  return time_needed


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


async def update_raffle_message(bot):
  """
  Updates the piflouz message with the rankings
  --
  input:
    bot: discord.ext.commands.Bot
  """
  if "last_raffle_message" not in db.keys():
    return

  channel = bot.get_channel(db["out_channel"])
  embed = await embed_messages.get_embed_raffle(bot)
  raffle_message = await channel.fetch_message(db["last_raffle_message"])
  await raffle_message.edit(embed=embed)


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


def get_raffle_total_prize():
  """
  Returns the total prize in the current raffle
  Returns 0 if there is no current raffle
  --
  output:
    prize: int
  """
  nb_tickets = sum(db["raffle_participation"].values())
  prize = int(nb_tickets * Constants.RAFFLE_TICKET_PRICE * (100 - Constants.RAFFLE_TAX_RATIO) / 100)
  return prize