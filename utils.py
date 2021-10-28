import requests
import datetime
import asyncio
import pickle
from replit import db
from replit.database.database import ObservedList, ObservedDict, Database
from discord.ext import commands, tasks

from constant import Constants
import embed_messages
import piflouz_handlers
import powerups  # Used in eval()
import events  # Used in eval()


def get_new_joke():
  """
  Checks a joke API to format a new random joke
  --
  output:
    joke: str -> the formatted joke
  """
  #r = requests.get("https://official-joke-api.appspot.com/random_joke").json()
  r = requests.get("https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist,sexist").json()  
  if r["type"] == "twopart":
    joke = r["setup"] + "\n||**" + r["delivery"] + "**||"
  else:
    joke = r["joke"]
  return joke


def get_timer(user_id, current_time):
  """
  This function returns the amount of time needed before being able to earn more piflouz
  --
  input:
    user_id: int/str
  --
  output:
    time_needed: int -> time remaining before the end of cooldown
    current_time: int -> the time at which the interaction was created
  """
  user_id = str(user_id)
  if user_id not in db["timers_react"].keys():
    db["timers_react"][user_id] = 0

  old_time = db["timers_react"][user_id]
  differential = current_time - old_time

  cooldown = get_total_cooldown(user_id)

  time_needed = max(0, cooldown - differential)
  
  return int(time_needed)


def get_total_cooldown(user_id):
  """
  Returns the time to wait between two /get, taking into account the user powerups and the current event
  --
  input:
    user_id: int/str - the id of the user having the powerups
  --
  output:
    cooldown: the time in seconds
  """
  if str(user_id) not in db["powerups"].keys():
    db["powerups"][user_id] = []

  current_event = eval(db["current_event"])
  powerups_user = [eval(p) for p in db["powerups"][str(user_id)]]
  powerups_event = current_event.get_powerups()

  cooldown = Constants.REACT_TIME_INTERVAL * (1 + sum(p.get_cooldown_multiplier_value() - 1 for p in powerups_user + powerups_event))
  return cooldown


async def update_piflouz_message(bot):
  """
  Updates the piflouz message with the rankings
  --
  input:
    bot: discord.ext.commands.Bot
  """
  channel = bot.get_channel(db["out_channel"])
  embed = embed_messages.get_embed_piflouz(bot)
  piflouz_message = await channel.fetch_message(db["piflouz_message_id"])
  await piflouz_message.edit(embed=embed)


def create_duel(id_challenger, id_challenged, amount, duel_type):
  """
  Generates a new duel
  --
  input:
    id_challenged: int
    id_challenged: int
    amount: int
    duel_type: str
  --
  output:
    duel: dict
  """
  duel = {
    "user_id1": id_challenger, # Challenger
    "user_id2": id_challenged, # Challenged
    "duel_id": get_new_duel_id(),
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


@commands.check
def check_message_to_be_processed(ctx):
    """
    Check if the bot should treat the command as a real one (sent by a user, in the setuped channel)
    --
    input:
      ctx: discord.ext.commands.Context
    """
    assert not (ctx.author == ctx.bot.user or "out_channel" not in db.keys() or ctx.bot.get_channel(db["out_channel"]) != ctx.channel), "Command attempt in the wrong channel"
    return True


def get_total_piflouz_multiplier(user_id, current_time):
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

  current_event = eval(db["current_event"])
  powerups_user = [eval(p) for p in db["powerups"][str(user_id)]]
  powerups_event = current_event.get_powerups()

  qty = Constants.BASE_MINING_AMOUNT * (1 + sum(p.get_piflouz_multiplier_value() - 1 for p in powerups_user + powerups_event))
  qty = round(qty)

  combo_bonus = min(db["mining_combo"][str(user_id)], Constants.MAX_MINING_COMBO) * Constants.PIFLOUZ_PER_MINING_COMBO

  return qty + combo_bonus + piflouz_handlers.get_mining_accuracy_bonus(user_id, current_time)


def observed_to_py(obj):
  """
  Turns an "Observed" object (from the database) into a classic Python object
  --
  input:
    obj: int/str/bool/None/ObservedDict/ObservedList/Database
  output:
    res: int/str/bool/None/dict/list
  """
  t = type(obj)
  if t == int or t == str or t == bool or obj is None:
    return obj

  elif t == ObservedList:
    return [observed_to_py(sub_obj) for sub_obj in obj]
  
  elif t == ObservedDict or t == Database:
    return {key: observed_to_py(val) for key, val in obj.items()}
  
  else:
    print("Cannot convert from type: ", t)


@tasks.loop(hours=24)
async def backup_db(filename=None):
  """
  Creates a daily backup of the database
  --
  input:
    filename: str -> the path to the file where the database will be saved. If None, the name is based on the date
  """
  then = datetime.time(22, 0, 0)
  await wait_until(then)

  if filename is None:
    now = datetime.datetime.now()
    filename = now.strftime("backups_db/%Y_%m_%d_%H:%M:%S.dump")

  content = observed_to_py(db)

  pickle.dump(content, open(filename, "wb"))
  print("Made a backup of the database in file: ", filename)


async def recover_db(filename):
  """
  Overrides the current database with one from a backed up file
  --
  input:
    filename: str -> the path to the file
  """
  new_db = pickle.load(open(filename, "rb"))
  print("loaded the database from file: ", filename)

  # Backing up the current database just in case
  now = datetime.datetime.now()
  tmp_filename = now.strftime("backups_db/tmp_%Y_%m_%d_%H:%M:%S.dump")
  await backup_db(tmp_filename)

  print("Overriding the current database")
  for key in db.keys():
    del db[key]
  
  for key in new_db.keys():
    db[key] = new_db[key]


def seconds_to_formatted_string(s):
  """
  Returns a formated string 'Xh Ymin Zs' corresponding to a certain amount of seconds
  --
  input:
    s: int -> the number of seconds
  """
  seconds = s % 60
  min = (s // 60) % 60
  hours = s // (60 * 60)
  if hours > 0:
    return f"{hours}h {min}min {seconds}s"
  elif min > 0:
    return f"{min}min {seconds}s"
  else:
    return f"{seconds}s"


def get_new_duel_id():
    """
    Creates a new unique id to represent a duel
    --
    output:
      res: int
    """
    if "last_duel_id" not in db.keys():
      db["last_duel_id"] = -1
    
    db["last_duel_id"] += 1
    return db["last_duel_id"]