import random
import os
import requests
import time
from discord.ext import tasks, commands
import discord
from replit import db
import asyncio

from keep_alive import keep_alive
from constant import Constants
import embed_messages
import piflouz_handlers
import rank_handlers
import utils


bot = commands.Bot(command_prefix="$", help_command=None)


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
    out_channel = bot.get_channel(db["out_channel"])
    role = bot.guilds[0].get_role(Constants.TWITCH_NOTIF_ROLE_ID)
    await out_channel.send(f"{role.mention} {streamer_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}")
  else:
    print(f"Found {streamer_name}, but cooldown was still up.")


@bot.event
async def on_ready():
  """
  Function executed when the bot correctly connected to Discord
  """
  print(f"I have logged in as {bot.user}")
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Piflouz generator'))

  if "piflouz_bank" not in db.keys():
    db["piflouz_bank"] = dict()

  if "is_currently_live" not in db.keys():
    db["is_currently_live"] = {streamer_name: False for streamer_name in Constants.streamers_to_check}
  
  if "previous_live_message_time" not in db.keys():
    db["previous_live_message_time"] = {name: 0 for name in Constants.streamers_to_check}
  
  if "random_gifts" not in db.keys():
    db["random_gifts"] = dict()

  if "current_pilords" not in db.keys():
    db["current_pilords"] = []

  if "mega_piflexers" not in db.keys():
    db["mega_piflexers"] = dict()
  
  if "piflexers" not in db.keys():
    db["piflexers"] = dict()
  
  if "raffle_participation" not in db.keys():
    db["raffle_participation"] = dict()
  
  if "powerups" not in db.keys():
      db["powerups"] = dict()

  task_check_live_status.start()
  piflouz_handlers.random_gift.start(bot)
  rank_handlers.update_ranks.start(bot)
  piflouz_handlers.check_daily_raffle.start(bot)
  piflouz_handlers.miners_action.start(bot)


def message_to_be_processed(ctx):
  """
  Check if the bot should treat the command as a real one (sent by a user, in the setuped channel)
  --
  input:
    ctx: discord.ext.commands.Context
  """
  if ctx.author == bot.user or "out_channel" not in db.keys() or bot.get_channel(db["out_channel"]) != ctx.message.channel:
    return False
  return True


@bot.event
async def on_command_error(ctx, error):
  """
  Callback called when an error occurs while dealing with a command
  """
  print(f"Got error: {error}")
  await utils.react_and_delete(ctx.message, "❌", 2)


@bot.command(name="?", aliases=["help"])
async def help_cmd(ctx, *args):
  """
  Callback for the help command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
  
  await ctx.channel.send(f"<@{ctx.author.id}>, here is some help. Hopes you understand me better after reading this! {Constants.PIFLOUZ_EMOJI}\n", embed=embed_messages.get_embed_help_message())
  await ctx.message.delete()


@bot.command(name="hello")
async def hello_cmd(ctx, *args):
  """
  Callback for the hello command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  index = random.randint(0, len(Constants.greetings) - 1)
  await ctx.channel.send(Constants.greetings[index].format(ctx.author.id))


@bot.command(name="donate", aliases=["khalass"])
async def donate_cmd(ctx, *args):
  """
  Callback for the donate command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
  
  assert len(args) >= 2, "$donate command requires 2 argument, the tag of a user and the amount as a positive integer"

  amount, user_receiver_id = args[1], utils.check_tag(args[0])
  assert user_receiver_id is not None, "The user tag is incorrect"
  assert utils.is_digit(amount), "The amount to donate has to ba a positive integer"

  amount = int(amount)

  # Will sent to on_command_error if user does not exist
  user_receiver = await bot.fetch_user(user_receiver_id)
  user_sender = ctx.author 

  # Trading
  assert piflouz_handlers.update_piflouz(user_sender, qty=-amount, check_cooldown=False), "Sender does not have enough money to donate"
  piflouz_handlers.update_piflouz(user_receiver, qty=amount, check_cooldown=False)

  await ctx.message.add_reaction("✅")
  await utils.update_piflouz_message(bot)


@bot.command(name="setupChannel")
async def setup_channel_cmd(ctx, *args):
  """
  Callback for the setupChannnel command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  # Saving the channel in the database in order not to need to do $setupChannel whenre booting
  await ctx.message.delete()

  db["out_channel"] = ctx.channel.id

  await ctx.channel.send("This channel is now my default channel")

  # Twitch message
  await ctx.channel.send(embed=embed_messages.get_embed_help_message())
  message = await ctx.channel.send(embed=embed_messages.get_embed_twitch_notif())
  db["twitch_notif_message_id"] = message.id
  await message.add_reaction("✅")
  await message.add_reaction("❌")

  # Piflouz mining message
  message = await ctx.channel.send(embed=await embed_messages.get_embed_piflouz(bot))
  db["piflouz_message_id"] = message.id
  await message.add_reaction(Constants.PIFLOUZ_EMOJI)


@bot.command(name="isLive")
async def is_live_cmd(ctx, *args):
  """
  Callback for the isLive command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  assert len(args) >= 1, "$isLive command requires the streamer name argument"

  user_name = args[0]
  r = utils.get_live_status(user_name)
  if r["data"] != []:
    # The streamer is live
    title = r["data"][0]["title"]
    await ctx.channel.send(f"{user_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{user_name} ! {Constants.FUEGO_EMOJI}")
  else:
    # The streamer is not live
    await ctx.channel.send(f"{user_name} is not live yet. Follow  http://www.twitch.tv/{user_name} to stay tuned ! {Constants.FUEGO_EMOJI}")


@bot.command(name="joke")
async def joke_cmd(ctx, *args):
  """
  Callback for the joke command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  user = ctx.author
  joke = utils.get_new_joke()
  output_message = f"<@{user.id}>, here is a joke for you:\n{joke}"
  await ctx.channel.send(output_message)
  await ctx.message.delete()


@bot.command(name="balance")
async def balance_cmd(ctx, *args):
  """
  Callback for the balance command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  user = ctx.author
  if "piflouz_bank" in db.keys() and str(user.id) in db["piflouz_bank"].keys():
    await ctx.message.delete()
    balance = db["piflouz_bank"][str(user.id)]
    content = f"<@{user.id}>, your balance is of {balance} {Constants.PIFLOUZ_EMOJI}! " 
    await ctx.channel.send(content, delete_after=Constants.TIME_BEFORE_DELETION)
    return

  await utils.react_and_delete(ctx.message, "❌")


@bot.command(name="get")
async def get_cmd(ctx, *args):
  """
  Callback for the get command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  user = ctx.author
  successful_update = piflouz_handlers.update_piflouz(user)
  react = "✅" if successful_update else "❌"

  if not successful_update:
    timer = utils.get_timer(user)
    output_text = f"<@{user.id}>, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
    await ctx.channel.send(output_text, delete_after=Constants.TIME_BEFORE_DELETION)
  
  await utils.update_piflouz_message(bot)
  await utils.react_and_delete(ctx.message, react)


@bot.command(name="cooldown")
async def cooldown_cmd(ctx, *args):
  """
  Callback for the cooldown command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
  
  user = ctx.author
  await ctx.message.delete()

  timer = utils.get_timer(user)
  if timer > 0 :
    output_text = f"<@{user.id}>, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
  else:
    output_text = f"<@{user.id}>, you can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
  await ctx.channel.send(output_text, delete_after=Constants.TIME_BEFORE_DELETION)


@bot.command(name="piflex")
async def piflex_cmd(ctx, *args):
  """
  Callback for the piflex command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  user_id = str(ctx.author.id)
  if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(ctx.author, qty=-Constants.PIFLEX_COST, check_cooldown=False):
    await ctx.message.add_reaction("✅")

    role = ctx.guild.get_role(Constants.MEGA_PIFLEXER_ROLE_ID)
    member = await ctx.guild.fetch_member(ctx.author.id)
    await member.add_roles(role)
    t = time.time()
    db["mega_piflexers"][user_id] = int(t)

    embed = embed_messages.get_embed_piflex(user_id)
    await ctx.channel.send(embed=embed)
    await utils.update_piflouz_message(bot)

  else:
    await ctx.message.add_reaction("❌")

    balance = 0 if user_id not in db["piflouz_bank"].keys() else db["piflouz_bank"][user_id]
    await ctx.channel.send(f"You need {Constants.PIFLEX_COST - balance} more {Constants.PIFLOUZ_EMOJI} to piflex!")

  await utils.react_and_delete(ctx.message, None, t=2)


@bot.command(name="buyRankPiflex")
async def buy_rank_piflex_cmd(ctx, *args):
  """
  Callback for the buyRankPiflex command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
  
  user_id = str(ctx.author.id)
  member = await ctx.guild.fetch_member(user_id)
  role = ctx.guild.get_role(Constants.PIFLEXER_ROLE_ID)

  if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(member, qty=-Constants.PIFLEXER_COST, check_cooldown=False) and role not in member.roles:
    await ctx.message.add_reaction("✅")
    await member.add_roles(role)
    await utils.update_piflouz_message(bot)
    db["piflexers"][user_id] = int(time.time())
  else:
    await ctx.message.add_reaction("❌")

    # User does not have enough money
    if role not in member.roles:
      await ctx.channel.send(f"<@{user_id}> You need {Constants.PIFLEXER_COST - db['piflouz_bank'][user_id]} {Constants.PIFLOUZ_EMOJI} to buy the rank!", delete_after=Constants.TIME_BEFORE_DELETION)

    # User already have the rank
    else:
      await ctx.channel.send(f"<@{user_id}> You already have the rank!", delete_after=Constants.TIME_BEFORE_DELETION)
    

  await utils.react_and_delete(ctx.message, None, 2)


@bot.command(name="pilord")
async def pilord_cmd(ctx, *args):
  """
  Callback for the pilord command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
    
  user_id = str(ctx.author.id)
  if user_id not in db["piflouz_bank"].keys():
    db["piflouz_bank"][user_id] = 0

  if user_id in db["current_pilords"]:
    await ctx.channel.send(f"<@{user_id}> You are currently a pilord. Kinda flexing right now!", delete_after=Constants.TIME_BEFORE_DELETION)
  
  else:
    amount = db["piflouz_bank"][user_id]
    max_amount = db["piflouz_bank"][db["current_pilords"][0]]
    await ctx.channel.send(f"<@{user_id}> You need {max_amount - amount} {Constants.PIFLOUZ_EMOJI} to become pilord!", delete_after=Constants.TIME_BEFORE_DELETION)
  
  await utils.react_and_delete(ctx.message, None)


@bot.command(name="raffle")
async def raffle_cmd(ctx, *args):
  """
  Callback for the raffle command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
    
  assert "previous_live_message_time" in db.keys(), "No raffle registered"
  assert len(args) >= 1 and utils.is_digit(args[0]), "Need one argument corresponding to a positive integer"

  nb_tickets = int(args[0])
  price = nb_tickets * Constants.RAFFLE_TICKET_PRICE
  
  user_id = str(ctx.author.id)

  # user doesn't have enough money
  assert piflouz_handlers.update_piflouz(ctx.author, qty=-price, check_cooldown=False), f"User {user_id} doesn't have enough money to buy {nb_tickets} tickets"
  
  if not user_id in db["raffle_participation"].keys():
    db["raffle_participation"][user_id] = 0
  db["raffle_participation"][user_id] += nb_tickets

  await utils.update_raffle_message(bot)
  await utils.update_piflouz_message(bot)
  await utils.react_and_delete(ctx.message, "✅")

@bot.command(name="giveaway")
async def giveaway_cmd(ctx,*args):
  """
  Callback for the giveway command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
  assert len(args) >= 1, "$giveaway command requires 1 argument, the amount as a positive integer"

  amount = args[0]
  assert utils.is_digit(amount) and int(amount) > 0, "The amount to giveaway has to ba a strictly positive integer"

  amount = int(amount)
  user_sender = ctx.author 
  # Trading
  assert piflouz_handlers.update_piflouz(user_sender, qty=-amount, check_cooldown=False), "Sender does not have enough money to giveaway"
  custom_message = f"This is a gift from the great <@{user_sender.id}>, be sure to thank him/her! "
  await piflouz_handlers.spawn_pibox(bot,amount,custom_message = custom_message)

  await utils.update_piflouz_message(bot)
  await ctx.message.delete()


@bot.command(name="store", aliases=["shop"])
async def store_cmd(ctx, *args):
  """
  Callback for the raffle command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return
  
  await ctx.message.delete()
  embed = embed_messages.get_embed_store_ui()
  message = await ctx.channel.send(embed=embed)

  for react in ["❎", "❇️", "⏳", "⏩", "⛏️"]:
    await message.add_reaction(react)
  
  old_message_id = None
  if "store_message_id" in db.keys():
    old_message_id = db["store_message_id"]
    
  db["store_message_id"] = message.id

  try: 
    if old_message_id is not None:
      old_message =  await ctx.channel.fetch_message(old_message_id)
      await old_message.delete()
  except:
      print("Failed to delete old shop message")


@bot.command(name="powerups", aliases=["powerup"])
async def powerups_cmd(ctx, *args):
  """
  Callback for the powerups command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  if not message_to_be_processed(ctx):
    return

  now_time = int(time.time())
  user_id = str(ctx.author.id)
  content = f"<@{user_id}>, here is the list of powerups you have at the moment:\n"
  has_any_powerup = False

  if user_id in db["powerups"].keys():
    for key, val in db["powerups"][user_id].items():
      if key == "miners":
        if val > 0:
          content += f"{key} - {val}\n"
          has_any_powerup = True
      elif val[1] - now_time > 0:
        content += f"{key} - {val[0]}% - time left: {val[1] - now_time}\n"
        has_any_powerup = True

  if not has_any_powerup:
    content = f"<@{user_id}>, you don't have any power up at the moment. Go buy one, using `$store`!"   
  await ctx.message.delete()
  await ctx.channel.send(content, delete_after=Constants.TIME_BEFORE_DELETION)


@bot.command(name="spawnPibox")
async def spawn_pibox_cmd(ctx, *args):
  """
  Callback for the spawnPibox command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  assert ctx.author.id == Constants.PIBOX_MASTER_ID, "Only the pibox master can use this command"
  await ctx.message.delete()
  piflouz_quantity = int(Constants.RANDOM_DROP_AVERAGE * random.random())
  custom_message = "It was spawned by the pibox master"
  await piflouz_handlers.spawn_pibox(bot, piflouz_quantity, custom_message)


@bot.command(name="shutdown")
async def shutdown_cmd(ctx, *args):
  """
  Callback for the shutdown command
  --
  input:
    ctx: discord.ext.commands.Context
    args: string list -> arguments given to the command
  """
  exit()


@bot.event
async def on_message(message):
  """
  Function executed when a message is sent
  --
  input:
    message: discord.Message -> the message sent
  """
  # Do nothing if the message was sent by the bot
  if message.author == bot.user:
    return
  
  if "$tarpin" in message.content:
    await message.reply("Du quoi ?")

  await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(playload):
  """
  Function executed when a reaction is added to a message
  We use raw_reaction (instead of reaction) so that we can catch reactions added on message sent before the client was started (so that we do not need a $setupChannel if the client reboots)
  --
  input:
    playload
  """

  channel = bot.get_channel(playload.channel_id)
  message = await channel.fetch_message(playload.message_id)
  guild = await bot.fetch_guild(playload.guild_id)
  user = await guild.fetch_member(playload.user_id)
  emoji = playload.emoji



  # Reaction to the Twitch notification message
  if "twitch_notif_message_id" in db.keys() and message.id == db["twitch_notif_message_id"]:
    # Check mark or cross mark created by the bot
    if bot.user.id == user.id:
      return
    
    role = guild.get_role(Constants.TWITCH_NOTIF_ROLE_ID)
    if emoji.name == "✅":
      await user.add_roles(role)
    elif emoji.name == "❌":
      await user.remove_roles(role)
    
    await message.remove_reaction(emoji, user)


  # Reaction to the store message
  if "store_message_id" in db.keys() and message.id == db["store_message_id"]:
    # Check mark or cross mark created by the bot
    if bot.user.id == user.id:
      if emoji.name == "✅" or emoji.name == "❌":
        await asyncio.sleep(2)
        await message.remove_reaction(emoji, user)
      return
    else:
      await message.remove_reaction(emoji, user)

    
    user_id = str(user.id)
    if user_id not in db["powerups"].keys(): #Basic infrastructure
      db["powerups"][user_id] ={
        "multiplier": [0, 0], # Effect, limit time
        "cooldown_reduction" : [0, 0], # Effect, limit time
        "miners": 0 
      }
    current_time = int(time.time())
    powerup_name = None

    if emoji.name == "❎":
      powerup_name = "multiplier"
      powerup = Constants.POWERUP_MULTIPLIER_EFFECT1
      powerup_cost = Constants.POWERUP_MULTIPLIER_PRICE1
      powerup_cooldown = Constants.POWERUP_MULTIPLIER_TIME + current_time
      new_value = [powerup, powerup_cooldown]
      

    elif emoji.name == "❇️":
      powerup_name = "multiplier"
      powerup = Constants.POWERUP_MULTIPLIER_EFFECT2
      powerup_cost = Constants.POWERUP_MULTIPLIER_PRICE2
      powerup_cooldown = Constants.POWERUP_MULTIPLIER_TIME + current_time
      new_value = [powerup, powerup_cooldown]
    
    elif emoji.name == "⏳":
      powerup_name = "cooldown_reduction"
      powerup = Constants.POWERUP_COOLDOWN_EFFECT1
      powerup_cost = Constants.POWERUP_COOLDOWN_PRICE1
      powerup_cooldown = Constants.POWERUP_COOLDOWN_TIME + current_time
      new_value = [powerup, powerup_cooldown]


    elif emoji.name == "⏩":
      powerup_name = "cooldown_reduction"
      powerup = Constants.POWERUP_COOLDOWN_EFFECT2
      powerup_cost = Constants.POWERUP_COOLDOWN_PRICE2
      powerup_cooldown = Constants.POWERUP_COOLDOWN_TIME + current_time
      new_value = [powerup, powerup_cooldown]

    
    elif emoji.name == "⛏️":
      
      if db["powerups"][user_id]["miners"] < Constants.POWERUP_MINER_LIMIT:
        powerup_cost = Constants.POWERUP_MINER_PRICE
        has_paid = piflouz_handlers.update_piflouz(user, qty=-powerup_cost, check_cooldown=False)
        if has_paid:
          db["powerups"][user_id]["miners"] +=  1
          await message.add_reaction("✅")
          await utils.update_piflouz_message(bot)
          return
      
      await message.add_reaction("❌")
      return 

    if powerup_name is not None:
      if db["powerups"][user_id][powerup_name][1] - current_time <=0:
      
        has_paid = piflouz_handlers.update_piflouz(user, qty=-powerup_cost, check_cooldown=False)
        if has_paid: 
          db["powerups"][user_id][powerup_name] = new_value

          await message.add_reaction("✅")
          await utils.update_piflouz_message(bot)
          return
      await message.add_reaction("❌")
      return 

  # Reaction to the piflouz message
  if "piflouz_message_id" in db.keys() and message.id == db["piflouz_message_id"]:
    # Check mark or cross mark created by the bot
    if bot.user == user:
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
    embed = await embed_messages.get_embed_piflouz(bot)
    await message.edit(embed=embed)
  

  
  # Random chest message
  if str(message.id) in db["random_gifts"]:
    emoji_required, qty, custom_message = db["random_gifts"][str(message.id)]
    if str(emoji) == emoji_required:
      piflouz_handlers.update_piflouz(user, qty, False)

      del db["random_gifts"][str(message.id)]
      new_text_message = f"<@{user.id}> won {qty} {Constants.PIFLOUZ_EMOJI} from a pibox!"
      if custom_message is not None:
        new_text_message += " " + custom_message
      await message.edit(content=new_text_message)

      out_channel = bot.get_channel(db["out_channel"])
      embed = await embed_messages.get_embed_piflouz(bot)
      piflouz_message = await out_channel.fetch_message(int(db["piflouz_message_id"]))
      await piflouz_message.edit(embed=embed)




if __name__ == "__main__":
  keep_alive()
  bot.run(os.getenv("DISCORDTOKEN"))

"""
Ideas:

Features: 
  Add a prediction system
  diep.io party link generator
  Graph piflouz
  Horoscope
  giveway (custom -> one winner, random, sharing the loot, ... ?)
  rank with xp
  $steal (up to 50), 1-2 times a day
  daily events (double piflouz, steal, triple loot box, impostor)

Improvements:
  plus d'emote pour les gifts random -> mettre dans .env
  modify piflouz earned: 100 at 30minutes -> 50 at 35+
  more piflouz if consecutive win
  top gifter rank
  randomize $get value

Server-side improvements:
  backup db

  /!\ changing the channel will cause the last raffle not to work anymore
  does not recognize if command = prefix (ex $getblablabla)

  do the requests to the server here instead of using uptime robot?
"""