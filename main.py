import random
import os
import requests
import time
from discord.ext import tasks
import discord
from replit import db
import asyncio

from keep_alive import keep_alive
from constant import Constants
import embed_messages
import piflouz_handlers
import utils


client = discord.Client()


@tasks.loop(seconds=30)
async def task_check_live_status():
  """
  Checks if the best streamers are live on Twitch every few seconds
  This will be executed every 30 seconds
  """
  print("checking live status")

  if "out_channel" in db.keys():
    for streamer_name in Constants.streamers_to_check:
      API_ENDPOINT = f"https://api.twitch.tv/helix/streams?user_login={streamer_name}"
      head = {
        'client-id': os.getenv("TWITCHID"),
        'authorization': 'Bearer ' + os.getenv("TWITCHTOKEN")
      }
      
      r = requests.get(url=API_ENDPOINT, headers=head).json()

      if streamer_name not in db["is_currently_live"].keys() or streamer_name not in db["previous_live_message_time"].keys():
        db["is_currently_live"][streamer_name] = False
        db["previous_live_message_time"][streamer_name] = 0

      if r["data"] != [] and not db["is_currently_live"][streamer_name]:
        # A new live has started
        db["is_currently_live"][streamer_name] = True
        await send_new_live_message(r, streamer_name)

      elif r["data"] == [] and db["is_currently_live"][streamer_name]:
        # The live just ended
        print("The live ended")
        db["is_currently_live"][streamer_name] = False


async def send_new_live_message(r, streamer_name):
  """
  Sends a message saying pibou421 is now live
  --
  input:
    r: dict -> request
    streamer_name: str -> the name of the streamer who went live
  """
  current_live_message_time = int(time.time())
  if (current_live_message_time - db["previous_live_message_time"][streamer_name]) >= Constants.TWITCH_ANNOUNCEMENTDELAY:  #Checks if we waited long enough
    db["previous_live_message_time"][streamer_name] = current_live_message_time
    title = r["data"][0]["title"]
    out_channel = client.get_channel(db["out_channel"])
    role = client.guilds[0].get_role(Constants.TWITCH_NOTIF_ROLE_ID)
    await out_channel.send(f"{role.mention} {streamer_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}")
  else:
    print(f"Found {streamer_name}, but cooldown was still up.")


@client.event
async def on_ready():
  """
  Function executed when the bot correctly connected to Discord
  """
  print(f"I have logged in as {client.user}")
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Piflouz generator'))
  
  
  if "out_channel" in db.keys() and "piflouz_message_id" in db.keys():
    out_channel = client.get_channel(db["out_channel"])
    await out_channel.fetch_message(db["piflouz_message_id"])
  
  if "is_currently_live" not in db.keys():
    db["is_currently_live"] = {streamer_name: False for streamer_name in Constants.streamers_to_check}
  
  if "previous_live_message_time" not in db.keys():
    db["previous_live_message_time"] = {name: 0 for name in Constants.streamers_to_check}
  
  if "random_gifts" not in db.keys():
    db["random_gifts"] = dict()

  task_check_live_status.start()
  piflouz_handlers.random_gift.start(client)


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
    await out_channel.send(embed=embed_messages.get_embed_help_message())
    message = await out_channel.send(embed=embed_messages.get_embed_twitch_notif())
    db["twitch_notif_message_id"] = message.id
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    message = await out_channel.send(embed=await embed_messages.get_embed_piflouz(client))
    db["piflouz_message_id"] = message.id
    await message.add_reaction(Constants.PIFLOUZ_EMOJI)
    
  # Can't use the commands before using $setupChannel
  if "out_channel" not in db.keys():
    return

  out_channel = client.get_channel(db["out_channel"])

  # Only considers messages from the default channel
  if message.channel != out_channel:
    return

  if message.content.startswith("$hello"):
    index = random.randint(0, len(Constants.greetings) - 1)
    await out_channel.send(Constants.greetings[index].format(message.author.id))

  if message.content.startswith("$isLive") or message.content.startswith("$islive"):
    user_name = message.content.split()[1]
    r = utils.get_live_status(user_name)
    if r["data"] != []:
      # The streamer is live
      title = r["data"][0]["title"]
      await out_channel.send(f"{user_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{user_name} ! {Constants.FUEGO_EMOJI}")
    else:
      # The streamer is not live
      await out_channel.send(f"{user_name} is not live yet. Follow  http://www.twitch.tv/{user_name} to stay tuned ! {Constants.FUEGO_EMOJI}")

  if message.content.startswith("$joke"):
    user = message.author
    joke = utils.get_new_joke()
    output_message = f"<@{user.id}>, here is a joke for you:\n{joke}"
    await out_channel.send(output_message)
    await asyncio.sleep(3)
    await message.delete()

  if message.content.startswith("$?"):
    await out_channel.send(embed=embed_messages.get_embed_help_message())

  if message.content.startswith("$donate"):
    L = message.content.split()
    if len(L) >= 3 and "piflouz_bank" in db.keys():
      amount, user_receiver_id = L[2], utils.check_tag(L[1])
      if user_receiver_id is not None and amount.isdigit():
        #We check wheter a user is pinged (avoid donating to roles / @everyone)
        amount = int(amount)
        try:
          user_receiver = await client.fetch_user(user_receiver_id)
        except discord.errors.NotFound:
          user_receiver = None
        user_sender = message.author 

        if user_receiver is not None:
          # Check if the user exists (not a random message)
            
          # Check if the sender has an account
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
          
              embed = await embed_messages.get_embed_piflouz(client)
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
      message = f"<@{user.id}>, your balance is of {balance} {Constants.PIFLOUZ_EMOJI}! " 
      await out_channel.send(message)
      return
    await message.add_reaction("❌")
    
    await asyncio.sleep(10)
    await message.delete()

  if message.content.startswith("$get"):
    user = message.author
    successful_update = piflouz_handlers.update_piflouz(user)
    await message.add_reaction("✅" if successful_update else "❌")
    embed = await embed_messages.get_embed_piflouz(client)
    piflouz_message = await out_channel.fetch_message(int(db["piflouz_message_id"]))
    await piflouz_message.edit(embed=embed)
    await asyncio.sleep(3)
    await message.delete()

  if message.content.startswith("$cooldown"):
    user = message.author
    timer = utils.get_timer(user)
    if timer >0 :
      output_message = f"<@{user.id}>, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      output_message = f"<@{user.id}>, you can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
    await out_channel.send(output_message)
    await asyncio.sleep(3)
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
    
    role = guild.get_role(Constants.TWITCH_NOTIF_ROLE_ID)
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
      if (str(emoji) != Constants.PIFLOUZ_EMOJI):
        await asyncio.sleep(2)
        await message.remove_reaction(emoji, user)
      return
    else:
      await message.remove_reaction(emoji, user)

    # Only consider the :piflouz: reaction
    if str(emoji) != Constants.PIFLOUZ_EMOJI:
      return  

    successful_update = piflouz_handlers.update_piflouz(user)
    reaction_to_show = "✅" if successful_update else "❌"
    await message.add_reaction(reaction_to_show)  #This reaction will be deleted by this same function as it will be considered a new event.
    embed = await embed_messages.get_embed_piflouz(client)
    await message.edit(embed=embed)
  

  
  # Random chest message
  if str(message.id) in db["random_gifts"]:
    emoji_required, qty = db["random_gifts"][str(message.id)]
    if str(emoji) == emoji_required:
      piflouz_handlers.update_piflouz(user, qty)

      del db["random_gifts"][str(message.id)]
      await message.edit(content=f"<@{user.id}> won {qty} {Constants.PIFLOUZ_EMOJI}")




if __name__ == "__main__":
  keep_alive()
  client.run(os.getenv("DISCORDTOKEN"))

# Diflouz ???

"""
Ideas:
  Add a prediction system
  diep.io party link generator

  How to use piflouz
  Give Piflouz to people (ex: reduced time between actions, piflouz miner)
  Random chests
  Graph piflouz
  BIG PIFLEX
  Horoscope
  $get to get the piflouz without going to the message
  backup db
"""