import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "discord-py-slash-command==3.0.1a"])

import random
from discord.ext import commands
import discord
from discord_slash import SlashCommand 
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import SlashCommandOptionType as option_type, ContextMenuType, ButtonStyle
from replit import db
from math import ceil
import logging

from cog_buy import Cog_buy
from cog_duels import Cog_duels
from cog_piflouz_mining import Cog_piflouz_mining
from cog_status_check import Cog_status_check

from constant import Constants
import embed_messages
import events
import piflouz_handlers
import powerups
import rank_handlers
import socials
import utils


intents = discord.Intents.none()
intents.members = True
intents.messages = True
intents.reactions = True
intents.guilds = True

member_cache_flags = discord.MemberCacheFlags.from_intents(intents)

bot = commands.Bot(command_prefix="$", help_command=None, intents=intents, member_cache_flags=member_cache_flags)
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_error(event, *args, **kwargs):
  print(f"Error dealing with event {event}, with args {args} and kwargs {kwargs}")
  

@bot.event
async def on_ready():
  """
  Function executed when the bot correctly connected to Discord
  """
  print(f"I have logged in as {bot.user}")
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Piflouz generator'))

  # Setting the base parameters in the database
  for key in [
    "piflouz_bank",         # money of everyone
    "timers_react",         # the time at which the users last used /get
    "random_gifts",         # information about current piboxes
    "mega_piflexers",       # buy date of user doing /piflex
    "piflexers",            # buy date of user doing /buyrankpiflex
    "raffle_participation", # tickets bought by everyone
    "powerups",             # powerups of each user
    "stats",                # to test things
    "discovered_piflex",    # ids of the piflex images found
    "mining_combo"          # the current combo for mining piflouz
  ]:
    if key not in db.keys():
      db[key] = dict()
  
  for key in [
    "current_pilords",      # list of the current pilords
    "duels",                # list of active duels
    "current_piflex_masters"# list of the current piflex masters
  ]:
    if key not in db.keys():
      db[key] = []

  if "is_currently_live" not in db.keys():
    db["is_currently_live"] = {streamer_name: False for streamer_name in Constants.streamers_to_check}
  
  if "previous_live_message_time" not in db.keys():
    db["previous_live_message_time"] = {name: 0 for name in Constants.streamers_to_check}
  
  # Starting the tasks
  socials.task_check_live_status.start(bot)
  piflouz_handlers.random_gift.start(bot)
  rank_handlers.update_ranks.start(bot)
  powerups.handle_actions_every_hour.start(bot)
  events.event_handlers.start(bot)
  socials.generate_otter_of_the_day.start(bot)
  utils.backup_db.start()


@bot.event
async def on_slash_command_error(ctx, error):
  """
  Callback called when an error occurs while dealing with a command
  --
  input:
    ctx: discord_slash.context.SlashContext
    error: Exception
  """
  print(f"Got error from slash command: {error}")
  await ctx.send(f"Got an error while dealing with your command, sorry :'(\n{error}", hidden=True)


@bot.event
async def on_command_error(ctx, error):
  """
  Callback called when an error occurs while dealing with a command
  --
  input:
    ctx: discord.ext.commands.Context
    error: Exception
  """
  print(f"Got error: {error}")
  await utils.react_and_delete(ctx.message, "❌", 2)


@slash.slash(name="help", description="Show the help message", guild_ids=Constants.GUILD_IDS, options=[])
@utils.check_message_to_be_processed
async def help_cmd(ctx):
  """
  Callback for the help command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
  await ctx.send(f"{ctx.author.mention}, here is some help. Hopes you understand me better after reading this! {Constants.PIFLOUZ_EMOJI}\n", embed=embed_messages.get_embed_help_message(), hidden=True)


@slash.slash(name="hello", description="Say hi!", guild_ids=Constants.GUILD_IDS, options=[])
@utils.check_message_to_be_processed
async def hello_cmd(ctx):
  """
  Callback for the hello command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
  index = random.randint(0, len(Constants.greetings) - 1)
  await ctx.send(Constants.greetings[index].format(ctx.author.mention))


@slash.slash(name="donate", description="be generous to others", guild_ids=Constants.GUILD_IDS, options=[
  create_option(name="user_receiver", description="receiver", option_type=option_type.USER, required=True),
  create_option(name="amount", description="how much you want to give", option_type=option_type.INTEGER, required=True),
])
@utils.check_message_to_be_processed
async def donate_cmd(ctx, user_receiver, amount):
  """
  Callback for the donate command
  --
  input:
    ctx: discord_slash.context.SlashContext
    user_receiver: discord.User
    amount: int
  """
  await ctx.defer(hidden=True)
  assert amount > 0, "Cannot donate 0 or less"

  user_sender = ctx.author 

  # Trading
  assert piflouz_handlers.update_piflouz(user_sender.id, qty=-amount, check_cooldown=False), "Sender does not have enough money to donate"

  qty_tax = ceil(Constants.DONATE_TAX_RATIO / 100 * amount)
  qty_receiver = amount - qty_tax

  piflouz_handlers.update_piflouz(bot.user.id, qty=qty_tax, check_cooldown=False)
  piflouz_handlers.update_piflouz(user_receiver.id, qty=qty_receiver, check_cooldown=False)

  await ctx.send("Done!", hidden=True)

  await ctx.channel.send(f"{user_sender.mention} sent {amount} {Constants.PIFLOUZ_EMOJI} to {user_receiver.mention}")
  await utils.update_piflouz_message(bot)


@slash.slash(name="setupChannel", description="change my default channel", guild_ids=Constants.GUILD_IDS, options=[])
async def setup_channel_cmd(ctx):
  """
  Callback for the setupChannnel command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
  await ctx.send("Done!", hidden=True)

  # Saving the channel in the database in order not to need to do /setupChannel when rebooting
  db["out_channel"] = ctx.channel.id

  await ctx.channel.send("This channel is now my default channel")

  emoji = await bot.guilds[0].fetch_emoji(Constants.PIFLOUZ_EMOJI_ID)

  piflouz_button = create_button(style=ButtonStyle.gray, label="", custom_id=Cog_piflouz_mining.button_name, emoji=emoji)
  action_row = create_actionrow(piflouz_button)
  
  embed = await embed_messages.get_embed_piflouz(bot)

  # Piflouz mining message
  message = await ctx.channel.send(embed=embed, components=[action_row])
  db["piflouz_message_id"] = message.id
  await message.pin()


@slash.slash(name="joke", description="to laugh your ass off (or not, manage your expectations)", guild_ids=Constants.GUILD_IDS, options=[])
@utils.check_message_to_be_processed
async def joke_cmd(ctx):
  """
  Callback for the joke command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
  user = ctx.author
  joke = utils.get_new_joke()
  output_message = f"{user.mention}, here is a joke for you:\n{joke}"
  await ctx.send(output_message)


@slash.slash(name="raffle", description=f"buy raffle tickets to test your luck /!\ Costs piflouz", guild_ids=Constants.GUILD_IDS, options=[
  create_option(name="nb_tickets", description="How many tickets?", option_type=option_type.INTEGER, required=True)
])
@utils.check_message_to_be_processed
async def raffle_cmd(ctx, nb_tickets):
  """
  Callback for the raffle command
  --
  input:
    ctx: discord_slash.context.SlashContext
    nb_tickets: int
  """
  await ctx.defer(hidden=True)
  assert "current_event" in db.keys(), "No current event registered"

  current_event = eval(db["current_event"])
  assert isinstance(current_event, events.Raffle_event), "Current event is not a raffle"

  assert nb_tickets > 0, "You can't buy less than 1 ticket"

  price = nb_tickets * current_event.ticket_price
  
  user_id = str(ctx.author.id)

  # user doesn't have enough money
  assert piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False), f"User {ctx.author} doesn't have enough money to buy {nb_tickets} tickets"
  
  if not user_id in db["raffle_participation"].keys():
    db["raffle_participation"][user_id] = 0
  db["raffle_participation"][user_id] += nb_tickets

  await ctx.send(f"Successfully bought {nb_tickets} tickets", hidden=True)
  await current_event.update_raffle_message(bot)
  await utils.update_piflouz_message(bot)


@slash.slash(name="giveaway", description="launch a pibox with your own money", guild_ids=Constants.GUILD_IDS, options=[
  create_option(name="amount", description="How many piflouz", option_type=option_type.INTEGER, required=True)
])
@utils.check_message_to_be_processed
async def giveaway_cmd(ctx, amount):
  """
  Callback for the giveway command
  --
  input:
    ctx: discord_slash.context.SlashContext
    amount: int -> how many piflouz given
  """
  await ctx.defer(hidden=True)
  assert amount > 0, "The amount to giveaway has to ba a strictly positive integer"

  user_sender = ctx.author 
  # Trading
  assert piflouz_handlers.update_piflouz(user_sender.id, qty=-amount, check_cooldown=False), "Sender does not have enough money to giveaway"
  custom_message = f"This is a gift from the great {user_sender.mention}, be sure to thank him/her! "
  await piflouz_handlers.spawn_pibox(bot, amount, custom_message=custom_message, ctx=ctx)
  await ctx.send("Done!", hidden=True)

  await utils.update_piflouz_message(bot)


@slash.slash(name="spawnPibox", description="The pibox master can spawn pibox", guild_ids=Constants.GUILD_IDS, options=[])
@utils.check_message_to_be_processed
async def spawn_pibox_cmd(ctx):
  """
  Callback for the spawnPibox command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
  assert ctx.author.id == Constants.PIBOX_MASTER_ID, "Only the pibox master can use this command"
  piflouz_quantity = random.randrange(Constants.MAX_PIBOX_AMOUNT)
  custom_message = "It was spawned by the pibox master"
  await piflouz_handlers.spawn_pibox(bot, piflouz_quantity, custom_message)
  await ctx.send("Done!", hidden=True)


@slash.subcommand(name="get", base="role", description="Get a role", guild_ids=Constants.GUILD_IDS, options=[
  create_option(name="role", description="Which role?", required=True, option_type=option_type.STRING, choices=[
      create_choice(str(Constants.TWITCH_NOTIF_ROLE_ID), "Twitch Notifications"),
      create_choice(str(Constants.PIBOX_NOTIF_ROLE_ID), "Pibox Notifications"),
    ]
  )
])
@utils.check_message_to_be_processed
async def get_role_cmd(ctx, role):
  """
  Gives a role to the user
  --
  input:
    ctx: discord.ext.commands.Context
    role: discord.Role
  """
  role = bot.guilds[0].get_role(int(role))
  member = ctx.author
  await member.add_roles(role)
  await ctx.send("Done!", hidden=True)


@slash.subcommand(name="remove", base="role", description="Get a role", guild_ids=Constants.GUILD_IDS, options=[
  create_option(name="role", description="Which role?", required=True, option_type=option_type.STRING, choices=[
      create_choice(str(Constants.TWITCH_NOTIF_ROLE_ID), "Twitch Notifications"),
      create_choice(str(Constants.PIBOX_NOTIF_ROLE_ID), "Pibox Notifications"),
    ]
  )
])
@utils.check_message_to_be_processed
async def remove_role_cmd(ctx, role):
  """
  Removes a role from the user
  --
  input:
    ctx: discord.ext.commands.Context
    role: discord.Role
  """
  role = bot.guilds[0].get_role(int(role))
  member = ctx.author
  await member.remove_roles(role)
  await ctx.send("Done!", hidden=True)


@slash.context_menu(target=ContextMenuType.MESSAGE, name="Du quoi ?", guild_ids=Constants.GUILD_IDS)
async def du_quoi_context_app(ctx):
  """
  Answers "Du quoi ?" to a message (probably in response to message containing the word "tarpin")
  --
  input:
    ctx: discord_slash.context.MenuContext
  """
  await ctx.target_message.reply("Du quoi ?")
  await ctx.send("Done!", hidden=True)


@slash.context_menu(target=ContextMenuType.MESSAGE, name="Du tarpin !", guild_ids=Constants.GUILD_IDS)
async def du_tarpin_context_app(ctx):
  """
  Answers "Du tarpin !" to a message (probably in response to message containing "Du quoi ?")
  --
  input:
    ctx: discord_slash.context.MenuContext
  """
  await ctx.target_message.reply("Du tarpin !")
  await ctx.send("Done!", hidden=True)


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
    return

  #await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(playload):
  """
  Function executed when a reaction is added to a message
  We use raw_reaction (instead of reaction) so that we can catch reactions added on message sent before the client was started (so that we do not need a /setupChannel if the client reboots)
  --
  input:
    playload
  """

  message_id = playload.message_id
  if str(message_id) not in db["random_gifts"]:
    return

  channel = bot.get_channel(playload.channel_id)
  message = await channel.fetch_message(playload.message_id)
  user = playload.member
  emoji = playload.emoji
  
  # Random chest message
  if str(message.id) in db["random_gifts"]:
    emoji_required, qty, custom_message = db["random_gifts"][str(message.id)]
    if str(emoji) == emoji_required:
      piflouz_handlers.update_piflouz(user.id, qty, False)

      del db["random_gifts"][str(message.id)]
      new_text_message = f"{user.mention} won {qty} {Constants.PIFLOUZ_EMOJI} from a pibox!"
      if custom_message is not None:
        new_text_message += " " + custom_message
      await message.edit(content=new_text_message)

      out_channel = bot.get_channel(db["out_channel"])
      embed = await embed_messages.get_embed_piflouz(bot)
      piflouz_message = await out_channel.fetch_message(int(db["piflouz_message_id"]))
      await piflouz_message.edit(embed=embed)
  


if __name__ == "__main__":
  Constants.load()  # Due to import circular import issues

  bot.add_cog(Cog_buy(bot, slash))
  bot.add_cog(Cog_duels(bot))
  bot.add_cog(Cog_piflouz_mining(bot, slash))
  bot.add_cog(Cog_status_check(bot))

  logger = logging.getLogger('discord')
  logger.setLevel(logging.DEBUG)
  handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
  handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
  logger.addHandler(handler)

  bot.run(Constants.DISCORDTOKEN)