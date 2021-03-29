import random
import os
import requests
import time
from discord.ext import tasks
import discord
from replit import db


from keep_alive import keep_alive


@tasks.loop(seconds=30)
async def get_pibou_live_status():
  global is_currently_live

  print("checking live status")

  if out_channel is not None:

    API_ENDPOINT = "https://api.twitch.tv/helix/streams?user_login=aypierre"
    head = {
      'client-id': os.getenv("TWITCHID"),
      'authorization': 'Bearer ' + os.getenv("TWITCHTOKEN")
    }
    
    r = requests.get(url=API_ENDPOINT, headers=head).json()
    if r["data"] != [] and not is_currently_live:
      is_currently_live = True
      await send_new_live_message(r)
    elif r["data"] == [] and is_currently_live:
      is_currently_live = False
      await send_end_live_message(r)


async def send_new_live_message(r):
  title = r["data"][0]["title"]
  await out_channel.send(f"Pibou421 is currently live on \"{title}\", go check him out on http://www.twitch.tv/pibou421 ! :fuego:")


async def send_end_live_message(r):
  await out_channel.send("Pibou421 is no longer live, follow him on http://www.twitch.tv/pibou421 to stay tuned! :fuego:")


def get_live_status(user_name):
  API_ENDPOINT = f"https://api.twitch.tv/helix/streams?user_login={user_name}"
  head = {
    'client-id': os.getenv("TWITCHID"),
    'authorization': 'Bearer ' + os.getenv("TWITCHTOKEN")
  }
  return requests.get(url=API_ENDPOINT, headers=head).json()


def get_new_joke():
  r = requests.get("https://official-joke-api.appspot.com/random_joke").json()
  joke = r["setup"] + "\n||**" + r["punchline"] + "**||"
  return joke



@client.event
async def on_ready():
  print(f"I have logged in as {client.user}")
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Piflouz generator'))
  get_pibou_live_status.start()
  

@client.event
async def on_message(message):
  global is_currently_live, out_channel, piflouz_mining_message_id

  # Do nothing if the message was sent by the bot
  if message.author == client.user:
    return
  
  if message.content.startswith("$setupChannel"):
    out_channel = message.channel
    await out_channel.send("This channel is now my default channel")
    
    await out_channel.send(f"Hello! My name is {client.user}, but you can call me PiBot!\n\n\
    Here is a guide on how I can be of service\n\
    - Use `$hello` to say hi\n\
    - Use `$isLive streamer_name` to check if a certain streamer is live\n\
    - Use `$shutdown` if I start doing something nasty, or if you don't like me anymore :cry:\n\
    - Use `$setupChannel` in a specific channel to change my default channel\n\
    - Use `$joke` to laugh your ass off\n\n\
    Here ar some background task I run:\n\
    - I will send a message everytime the great streamer pibou421 goes live on Twitch\n\
    - I can give you :piflouz: if you react to the message below")

    message = await out_channel.send("**" + "\\*" * 80  + "**" + 
    f"\nThis is the piflouz mining message, react every {REACT_TIME_INTERVAL} seconds to gain more :piflouz:\n\n\
    You can react with any emoji\n\
    If you waited long enough ({REACT_TIME_INTERVAL} seconds), you will earn {NB_PIFLOUZ_PER_REACT} :piflouz:!\n\
    A :white_check_mark: reaction will appear for 2 seconds to make you know you won\n\
    A :x: reaction will appear for 2s if you did not wait for long enough, better luck next time\n" + 
    "**" + "\\*" * 80 + "**")
    piflouz_mining_message_id = message.id
    
  
  # Only considers messages from the channel
  if out_channel is not None and message.channel != out_channel:
    return

  if message.content.startswith("$hello"):
    index = random.randint(0, len(greetings) - 1)
    await out_channel.send(greetings[index].format(message.author.id))

  if message.content.startswith("$isLive"):
    user_name = message.content.split()[1]
    r = get_live_status(user_name)

    if r["data"] != []:
      title = r["data"][0]["title"]
      await out_channel.send(f"{user_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{user_name} ! :fuego:")

    else:
      await out_channel.send(f"{user_name} is not live yet. Follow  http://www.twitch.tv/{user_name} to stay tuned ! :fuego:")

  if message.content.startswith("$joke"):
    joke = get_new_joke()
    await out_channel.send(joke)
  
  if message.content.startswith("$shutdown"):
    exit()
  

@client.event
async def on_reaction_add(reaction, user):
  message = reaction.message

  if message.id != piflouz_mining_message_id:
    return

  # thumb up or thumb down created by the bot
  if (client.user == user):
    time.sleep(2)
    await message.remove_reaction(reaction.emoji, user)
    return
  else:
     await message.remove_reaction(reaction.emoji, user)


  if "piflouz_bank" not in db.keys():
    db["piflouz_bank"] = dict()
    db["timers_react"] = dict()
  
  d_piflouz = dict(db["piflouz_bank"])
  d_timers = dict(db["timers_react"])

  user_id = str(user.id)

  # New user
  if user_id not in d_piflouz.keys():
    d_piflouz[user_id] = NB_PIFLOUZ_PER_REACT
    d_timers[user_id] = int(time.time())
    await message.add_reaction("✅")

  else:
    balance = d_piflouz[user_id]
    old_time = d_timers[user_id]
    new_time = int(time.time())

    if (new_time - old_time > REACT_TIME_INTERVAL):
      d_piflouz[user_id] = balance + NB_PIFLOUZ_PER_REACT
      d_timers[user_id] = new_time
      await message.add_reaction("✅")
    else:
      await message.add_reaction("❌")

  db["piflouz_bank"] = d_piflouz
  db["timers_react"] = d_timers

  print(d_piflouz[user_id])


# How many seconds between each react to earn piflouz
REACT_TIME_INTERVAL = 10
NB_PIFLOUZ_PER_REACT = 50

# Discord bot client
client = discord.Client()

# To not spam the chat
is_currently_live = False

# channel to write answers
out_channel = None

# piflouz message
piflouz_mining_message_id = None

greetings = [ "Greetings <@{}>! Nice to meet you!",
              "Hello there <@{}>, how are you doing today ?",
              "Hello, oh great <@{}>. Hope you are doing great"]

"""" 
del db["piflouz_bank"]
del db["timers_react"]
"""
keep_alive()
client.run(os.getenv("DISCORDTOKEN"))

# Diflouz ???

"""
Ideas:
  Create a role for stream notification
  Add a prediction system
"""