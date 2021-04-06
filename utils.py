import requests
import time
import os
from replit import db

from constant import Constants

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
  """
  user_id = str(user.id)
  if "timers_react" not in db.keys():
      db["timers_react"] = dict()
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0
  old_time = db["timers_react"][user_id]
  current_time = int(time.time())
  differential = current_time - old_time
  time_needed = max(0, Constants.REACT_TIME_INTERVAL - differential)
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