import random
import os
import requests
import time
from discord.ext import tasks
import discord
from replit import db
import asyncio

from keep_alive import keep_alive


# Discord bot client
client = discord.Client()


@tasks.loop(seconds=30)
async def get_pibou_live_status():
  """
  Checks if pibou421 is live on Twitch every few seconds
  This will be executed every 30 seconds
  """
  print("checking live status")

  if "out_channel" in db.keys():

    API_ENDPOINT = "https://api.twitch.tv/helix/streams?user_login=pibou421"
    head = {
      'client-id': os.getenv("TWITCHID"),
      'authorization': 'Bearer ' + os.getenv("TWITCHTOKEN")
    }
    
    r = requests.get(url=API_ENDPOINT, headers=head).json()
    if r["data"] != [] and not db["is_currently_live"]:
      # A new live has started
      db["is_currently_live"] = True
      await send_new_live_message(r)

    elif r["data"] == [] and db["is_currently_live"]:
      # The live just ended
      db["is_currently_live"] = False
      await send_end_live_message(r)


async def send_new_live_message(r):
  """
  Sends a message saying pibou421 is now live
  --
  input:
    r: dict -> request
  """
  title = r["data"][0]["title"]
  out_channel = client.get_channel(db["out_channel"])
  role = client.guilds[0].get_role(TWITCH_NOTIF_ROLE_ID)
  await out_channel.send(f"{role.mention} Pibou421 is currently live on \"{title}\", go check out on http://www.twitch.tv/pibou421 ! {FUEGO_EMOJI}")


async def send_end_live_message(r):
  """
  Sends a message saying pibou421 is no longer live
  --
  input:
    r: dict -> request
  """
  out_channel = client.get_channel(db["out_channel"])
  await out_channel.send(f"Pibou421 is no longer live, follow him on http://www.twitch.tv/pibou421 to stay tuned! {FUEGO_EMOJI}")


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


@client.event
async def on_ready():
  """
  Function executed when the bot correctly connected to Discord
  """
  print(f"I have logged in as {client.user}")
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Piflouz generator'))
  get_pibou_live_status.start()

  if "out_channel" in db.keys() and "piflouz_message_id" in db.keys():
    out_channel = client.get_channel(db["out_channel"])
    await out_channel.fetch_message(db["piflouz_message_id"])
  
  if "is_currently_live" not in db.keys():
    db["is_currently_live"] = False
  

  
def get_embed_help_message():
  """
  Returns the embed message with help for every command
  --
  output:
    embed: discord.Embed -> the embeded message
  """
  embed = discord.Embed(
    title="Need help?",
    colour=discord.Colour.red()
  )
  embed.set_thumbnail(url=PIBOU4LOVE_URL)

  embed.add_field(name="`$?`", value="Show this message", inline=False)
  embed.add_field(name="`$hello`", value="Say hi!", inline=False)
  embed.add_field(
    name="`$isLive streamer_name`", 
    value="check if a certain streamer is live!",
    inline=False
  )
  embed.add_field(
    name="`$shutdown`", 
    value="if I start doing something nasty, or if you don't like me anymore :cry:",
    inline=False
  )
  embed.add_field(
    name="`$setupChannel`",
    value="change my default channel",
    inline=False
  )
  embed.add_field(
    name="`$joke`",
    value="to laugh your ass off (or not, manage your expectations)",
    inline=False
  )
  embed.add_field(
    name="`$donate @user amount`",
    value="be generous to others",
    inline=False
  )
  embed.add_field(
    name ="`$balance`",
    value=f"check how many {PIFLOUZ_EMOJI} you have. Kind of a low-cost Piflex.",
    inline=False
  )

  embed.add_field(
    name="Things I do in the background",
    value=f"- I will send a message everytime the great streamer pibou421 goes live on Twitch\n\
    - I can give you {PIFLOUZ_EMOJI} if you react to the message below"
  )
  return embed


@client.event
async def on_message(message):
  """
  Function executed when a message is sent
  --
  input:
    message: discord.Message -> the message sent
  """
  # Do nothing if the message was sent by the bot
  if message.author == client.user:
    return
  
  if message.content.startswith("$setupChannel"):
    out_channel = message.channel
    # Saving the channel in the database in order not to need to do $setupChannel when
    # rebooting
    db["out_channel"] = out_channel.id
    await out_channel.send("This channel is now my default channel")
  
    await out_channel.send(embed=get_embed_help_message())

    message = await out_channel.send(embed=get_embed_twitch_notif())
    db["twitch_notif_message_id"] = message.id
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    message = await out_channel.send(embed=await get_embed_piflouz())
    db["piflouz_message_id"] = message.id
    await message.add_reaction(PIFLOUZ_EMOJI)
    
  
  # Can't use the commands before using $setupChannel
  if "out_channel" not in db.keys():
    return

  out_channel = client.get_channel(db["out_channel"])

  # Only considers messages from the default channel
  if message.channel != out_channel:
    return

  if message.content.startswith("$hello"):
    index = random.randint(0, len(greetings) - 1)
    await out_channel.send(greetings[index].format(message.author.id))

  if message.content.startswith("$isLive"):
    user_name = message.content.split()[1]
    r = get_live_status(user_name)

    if r["data"] != []:
      # The streamer is live
      title = r["data"][0]["title"]
      await out_channel.send(f"{user_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{user_name} ! {FUEGO_EMOJI}")

    else:
      # The streamer is not live
      await out_channel.send(f"{user_name} is not live yet. Follow  http://www.twitch.tv/{user_name} to stay tuned ! {FUEGO_EMOJI}")

  if message.content.startswith("$joke"):
    joke = get_new_joke()
    await out_channel.send(joke)
  
  if message.content.startswith("$?"):
    await out_channel.send(embed=get_embed_help_message())

  if message.content.startswith("$donate"):
    L = message.content.split()
    if len(L) >= 3 and "piflouz_bank" in db.keys():
      amount, user_receiver_id = L[2], L[1]
      if user_receiver_id.startswith("<@!") and user_receiver_id.endswith(">") and user_receiver_id[3:-1].isdigit() and amount.isdigit():  
        #We check wheter  a user is pinged (avoid donating to roles / @everyone)
        amount = int(amount)
        user_receiver_id = int(user_receiver_id[3:-1]) 
        try:
          user_receiver = await client.fetch_user(user_receiver_id)
        except discord.errors.NotFound:
          user_receiver = None
        user_sender = message.author 

        if user_receiver is not None:
          # Check if the user exists (not a random message)
            
          # Check if the sender and receiver have an account
          if str(user_sender.id) in db["piflouz_bank"].keys():
            # Check if the sender has enough piflouz
            if db["piflouz_bank"][str(user_sender.id)] >= amount:
            
              db["piflouz_bank"][str(user_sender.id)] -= amount

              if str(user_receiver_id) in db["piflouz_bank"].keys():
                db["piflouz_bank"][str(user_receiver.id)] += amount
              else:
                db["piflouz_bank"][str(user_receiver.id)] = amount
                db["timers_react"][str(user_receiver.id)] = 0 

              await message.add_reaction("✅")
          
              embed = await get_embed_piflouz()

              piflouz_message = await out_channel.fetch_message(int(db["piflouz_message_id"]))
              await piflouz_message.edit(embed=embed)
              return
    
    await message.add_reaction("❌")
    await asyncio.sleep(10)
    await message.delete()

  if message.content.startswith("$balance"):
    user = message.author
    if "piflouz_bank" in db.keys() and str(user.id) in db["piflouz_bank"].keys():
      balance = db["piflouz_bank"][str(user.id)]
      message = f"<@{user.id}>, your balance is of {balance} {PIFLOUZ_EMOJI}! " 
      await out_channel.send(message)
      return
    await message.add_reaction("❌")
    await asyncio.sleep(10)
    await message.delete()

  if message.content.startswith("$shutdown"):
    exit()
  

@client.event
async def on_raw_reaction_add(playload):
  """
  Function executed when a reaction is added to a message
  We use raw_reaction (instead of reaction) so that we can catch reactions added on message sent before the client was started (so that we do not need a $setupChannel if the client reboots)
  --
  input:
    playload
  """
  channel = client.get_channel(playload.channel_id)
  message = await channel.fetch_message(playload.message_id)
  guild = await client.fetch_guild(playload.guild_id)
  user = await guild.fetch_member(playload.user_id)
  emoji = playload.emoji

  # Reaction to the Twitch notification message
  if "twitch_notif_message_id" in db.keys() and message.id == db["twitch_notif_message_id"]:
    # Check mark or cross mark created by the bot
    if client.user.id == user.id:
      return
    
    role = guild.get_role(TWITCH_NOTIF_ROLE_ID)
    if emoji.name == "✅":
      await user.add_roles(role)
    elif emoji.name == "❌":
      await user.remove_roles(role)
    
    await message.remove_reaction(emoji, user)



  # Reaction to the piflouz message
  if "piflouz_message_id" in db.keys() and message.id == db["piflouz_message_id"]:
    # Check mark or cross mark created by the bot
    if client.user == user:
      # Do not react to the initial piflouz reaction
      if (str(emoji) != PIFLOUZ_EMOJI):
        await asyncio.sleep(2)
        await message.remove_reaction(emoji, user)
      return
    else:
      await message.remove_reaction(emoji, user)

    # Only consider the :piflouz: reaction
    if (str(emoji) != PIFLOUZ_EMOJI):
      return

    if "piflouz_bank" not in db.keys():
      db["piflouz_bank"] = dict()
      db["timers_react"] = dict()
    
    user_id = str(user.id)

    # New user
    if user_id not in db["piflouz_bank"].keys():
      db["piflouz_bank"][user_id] = NB_PIFLOUZ_PER_REACT
      db["timers_react"][user_id] = int(time.time())
      await message.add_reaction("✅")

    else:
      balance = db["piflouz_bank"][user_id]
      old_time = db["timers_react"][user_id]
      new_time = int(time.time())

      if (new_time - old_time > REACT_TIME_INTERVAL):
        db["piflouz_bank"][user_id] = balance + NB_PIFLOUZ_PER_REACT
        db["timers_react"][user_id] = new_time
        await message.add_reaction("✅")
      else:
        await message.add_reaction("❌")

    embed = await get_embed_piflouz()
    await message.edit(embed=embed)
  


async def get_embed_piflouz():
  """
  Creates an embed message containing the explanation for the piflouz game and the balance
  --
  output:
    embed: discord.Embed -> the message
  """
  embed = discord.Embed(
    title=f"Come get some {PIFLOUZ_EMOJI}!",
    description=BASE_PIFLOUZ_MESSAGE,
    colour=discord.Colour.gold()
  )
  # Piflouz thumbnail
  embed.set_thumbnail(url=PIFLOUZ_URL)
  if "piflouz_bank" in db.keys():
    d_piflouz = dict(db["piflouz_bank"])
    ranking = ""
    # Generating the ranking string
    sorted_rank = sorted(list(d_piflouz.items()), key=lambda key_val: -int(key_val[1]))
    for i, (user_id, balance) in enumerate(sorted_rank):
      member = await client.guilds[0].fetch_member(user_id)  # nickname is relative to the guild
      ranking += f"{i + 1}: {member.display_name} - {balance}\n"
    
    embed.add_field(name="Balance", value=ranking, inline=False)  
  
  return embed


def get_embed_twitch_notif():
  """
  Returns an embed message on which to react to get the role to get notified when pibou421 goes live on Twitch
  """
  embed = discord.Embed(
    title="Twitch notificatio role",
    description="React to get/remove the Twitch notifications role",
    colour=discord.Colour.purple()
  )
  embed.set_thumbnail(url=PIBOU_TWITCH_THUMBNAIL_URL)
  return embed


# How many seconds between each react to earn piflouz
REACT_TIME_INTERVAL = int(os.getenv("REACT_TIME_INTERVAL"))
NB_PIFLOUZ_PER_REACT = int(os.getenv("NB_PIFLOUZ_PER_REACT"))

#PIFLOUZ_EMOJI_ID = 820340949716041798
PIFLOUZ_EMOJI_ID = int(os.getenv("PIFLOUZ_EMOJI_ID"))
PIFLOUZ_EMOJI = f"<:piflouz:{PIFLOUZ_EMOJI_ID}>"

#FUEGO_EMOJI_ID = 818582820388601896
FUEGO_EMOJI_ID = int(os.getenv("FUEGO_EMOJI_ID"))
FUEGO_EMOJI = f"<:fuego:{FUEGO_EMOJI_ID}>"
PIFLOUZ_URL = os.getenv("PIFLOUZ_URL")
#"https://cdn.discordapp.com/emojis/820340949716041798.png?v=1"

PIBOU4LOVE_URL = os.getenv("PIBOU4LOVE_URL")
#"https://cdn.discordapp.com/emojis/823601705189900308.png?v=1"

PIBOU_TWITCH_THUMBNAIL_URL = os.getenv("PIBOU_TWITCH_THUMBNAIL_URL")
#"https://static-cdn.jtvnw.net/jtv_user_pictures/40bfa05b-7af4-448e-8504-2b81eaa3f11d-profile_image-70x70.png"

TWITCH_NOTIF_ROLE_ID = int(os.getenv("TWITCH_NOTIF_ROLE_ID"))

BASE_PIFLOUZ_MESSAGE = f"\nThis is the piflouz mining message, react every {REACT_TIME_INTERVAL} seconds to gain more {PIFLOUZ_EMOJI}\n\n\
You just need to react with the {PIFLOUZ_EMOJI} emoji\n\
If you waited long enough ({REACT_TIME_INTERVAL} seconds), you will earn {NB_PIFLOUZ_PER_REACT} {PIFLOUZ_EMOJI}!\n\
A :white_check_mark: reaction will appear for 2 seconds to make you know you won\n\
A :x: reaction will appear for 2s if you did not wait for long enough, better luck next time\n"


greetings = [ "Greetings <@{}>! Nice to meet you!",
              "Hello there <@{}>, how are you doing today ?",
              "Hello, oh great <@{}>. Hope you are doing great"]


keep_alive()
client.run(os.getenv("DISCORDTOKEN"))

# Diflouz ???

"""
Ideas:
  Add a prediction system
  diep.io party link generator


  How to use piflouz
  Give Piflouz to people (ex: reduced time between actions)
  Random chests
  Graph piflouz
"""