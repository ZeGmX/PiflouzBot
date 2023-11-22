import requests
import datetime
import asyncio
import pickle
from functools import wraps
from pyimgur import Imgur
from interactions import Button, ButtonStyle, TimeTrigger

from constant import Constants
from custom_task_triggers import TaskCustom as Task
import embed_messages
from my_database import db
import powerups  # Used in eval()
import events.events  # Used in eval()

def get_new_joke():
  """
  Checks a joke API to format a new random joke
  --
  output:
    joke: str -> the formatted joke
  """
  r = requests.get("https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,racist,sexist").json()  
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
    db["powerups"][str(user_id)] = []

  current_event = eval(db["current_event_passive"])
  powerups_user = [eval(p) for p in db["powerups"][str(user_id)]]
  powerups_event = current_event.get_powerups()

  cooldown = Constants.REACT_TIME_INTERVAL * (1 + sum(p.get_cooldown_multiplier_value() - 1 for p in powerups_user + powerups_event))
  return cooldown


async def update_piflouz_message(bot):
  """
  Updates the piflouz message with the rankings
  --
  input:
    bot: interactions.Client
  """
  from cogs.cog_piflouz_mining import Cog_piflouz_mining
  
  channel = await bot.fetch_channel(db["out_channel"])
  embed = embed_messages.get_embed_piflouz()
  piflouz_message = await channel.fetch_message(db["piflouz_message_id"])
  piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id="piflouz_mining_button", emoji=Constants.PIFLOUZ_EMOJI)
  piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id=Cog_piflouz_mining.BUTTON_NAME, emoji=Constants.PIFLOUZ_EMOJI)
  await piflouz_message.edit(embeds=embed, components=piflouz_button)


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
    "accepted": False, # Not accepted yet
    "message_id": None, # Not announced yet
    "thread_id": None
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


def check_message_to_be_processed(fun):
  """
  Check if the bot should treat the command as a real one (sent by a user, in the setuped channel)
  --
  input:
    fun: async function for a function defined in an extension, taking a context as first argument
  --
  output:
    wrapper: async function
  """
  @wraps(fun)
  async def wrapper(self, ctx, *args, **kwargs): # the other parameters will be added later

    await custom_assert("out_channel" in db.keys() and db["out_channel"] == int(ctx.channel_id), "Command attempt in the wrong channel", ctx)
    return await fun(self, ctx, *args, **kwargs)
  
  return wrapper


@Task.create(TimeTrigger(hour=23))
async def backup_db(folder=None):
  """
  Creates a daily backup of the database
  --
  input:
    filename: str -> the path to the file where the database will be saved. If None, the name is based on the date
  """
  parent_folder ="backups_db"
  if folder is None:
    now = datetime.datetime.now()
    folder = now.strftime("%Y_%m_%d_%H:%M:%S")
  db.make_backup(parent_folder, folder)

  print("Made a backup of the database in file: ", folder)


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
    if min > 0:
        if seconds > 0: return f"{hours}h {min}min {seconds}s"
        return f"{hours}h {min}min"
    elif seconds > 0: return f"{hours}h {seconds}s"
    return f"{hours}h"
  elif min > 0:
    if seconds > 0: return f"{min}min {seconds}s"
    return f"{min}min"
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


async def custom_assert(condition, msg, ctx):
  """
  Respond to an interaction with an error message if the condition is not met
  This also raises an exception to stop the coroutine handling the interaction
  --
  input:
    cont: bool
    msg: str
    ctx: interactions.CommandContext
  """
  if not condition:
    await ctx.send(msg, ephemeral=True)
    raise Exception(msg)


def upload_image_to_imgur(path):
  """
  Uploads an image file to imgur and returns the link
  --
  input:
    path: str
  --
  output:
    res: str
  """
  imgur = Imgur(Constants.IMGUR_CLIENT_ID)
  img = imgur.upload_image(path)
  return img.link
