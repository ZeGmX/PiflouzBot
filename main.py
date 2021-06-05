import random
import time
from discord.ext import commands
import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import SlashCommandOptionType as option_type
from replit import db
import functools
import asyncio
from math import ceil

from keep_alive import keep_alive
from constant import Constants
import embed_messages
import events
import piflouz_handlers
import powerups
import rank_handlers
import socials
import utils

bot = commands.Bot(command_prefix="$", help_command=None)
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_error(event, *args, **kwargs):
	print(
	    f"Error dealing with event {event}, with args {args} and kwargs {kwargs}"
	)


@bot.event
async def on_ready():
	"""
  Function executed when the bot correctly connected to Discord
  """
	print(f"I have logged in as {bot.user}")
	await bot.change_presence(activity=discord.Activity(
	    type=discord.ActivityType.playing, name='Piflouz generator'))

	# Setting the base parameters in the database
	for key in [
	    "piflouz_bank",  # money of everyone
	    "random_gifts",  # information about current piboxes
	    "mega_piflexers",  # buy date of user doing /piflex
	    "piflexers",  # buy date of user doing /buyrankpiflex
	    "raffle_participation",  # tickets bought by everyone
	    "powerups",  # powerups of each user
	    "stats",  # to test things
	    "discovered_piflex"  # ids of the piflex images found
	]:
		if key not in db.keys():
			db[key] = dict()

	for key in [
	    "current_pilords",  # list of the current pilords
	    "duels",  # list of active duels
	    "current_piflex_masters"  # list of the current piflex masters
	]:
		if key not in db.keys():
			db[key] = []

	if "is_currently_live" not in db.keys():
		db["is_currently_live"] = {
		    streamer_name: False
		    for streamer_name in Constants.streamers_to_check
		}

	if "previous_live_message_time" not in db.keys():
		db["previous_live_message_time"] = {
		    name: 0
		    for name in Constants.streamers_to_check
		}

	# Starting the tasks
	socials.task_check_live_status.start(bot)
	piflouz_handlers.random_gift.start(bot)
	rank_handlers.update_ranks.start(bot)
	powerups.handle_actions_every_hour.start(bot)
	events.event_handlers.start(bot)
	socials.generate_otter_of_the_day.start(bot)

	# Adding the checks for some sommands
	# Not for setupChannel, shutdown
	help_cmd.add_check(message_to_be_processed)
	hello_cmd.add_check(message_to_be_processed)
	donate_cmd.add_check(message_to_be_processed)
	is_live_cmd.add_check(message_to_be_processed)
	joke_cmd.add_check(message_to_be_processed)
	balance_cmd.add_check(message_to_be_processed)
	get_cmd.add_check(message_to_be_processed)
	cooldown_cmd.add_check(message_to_be_processed)
	piflex_cmd.add_check(message_to_be_processed)
	buy_rank_piflex_cmd.add_check(message_to_be_processed)
	pilord_cmd.add_check(message_to_be_processed)
	raffle_cmd.add_check(message_to_be_processed)
	giveaway_cmd.add_check(message_to_be_processed)
	store_cmd.add_check(message_to_be_processed)
	powerups_cmd.add_check(message_to_be_processed)
	spawn_pibox_cmd.add_check(message_to_be_processed)
	duel_challenge_cmd.add_check(message_to_be_processed)
	duel_accept_cmd.add_check(message_to_be_processed)
	duel_deny_cmd.add_check(message_to_be_processed)
	duel_cancel_cmd.add_check(message_to_be_processed)
	duel_play_shifumi_cmd.add_check(message_to_be_processed)
	ranking_cmd.add_check(message_to_be_processed)
	get_role_cmd.add_check(message_to_be_processed)
	remove_role_cmd.add_check(message_to_be_processed)
	"""
  chan = bot.get_channel(db["out_channel"])
  message = await chan.fetch_message(847606457474351104)
  await message.add_reaction("👎")
  """
	"""
  await message.reply(".hug <@616752883685261350>")
  """
	"""
  user = await bot.guilds[0].fetch_member(226787744058310656)
  p = powerups.Cooldown_reduction(30, 20, 100, "a")
  p.on_buy(user)

  p = powerups.Piflouz_multiplier(40, 20, 100, "a")
  p.on_buy(user)
  """


def message_to_be_processed(ctx):
	"""
  Check if the bot should treat the command as a real one (sent by a user, in the setuped channel)
  --
  input:
    ctx: discord.ext.commands.Context
  """
	assert not (ctx.author == bot.user or "out_channel" not in db.keys()
	            or bot.get_channel(db["out_channel"]) != ctx.channel
	            ), "Command attempt in the wrong channel"
	return True


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
	await ctx.send(
	    f"Got an error while dealing with your command, sorry :'(\n{error}",
	    hidden=True)


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


@slash.slash(name="help",
             description="Show the help message",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def help_cmd(ctx):
	"""
  Callback for the help command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	await ctx.send(
	    f"{ctx.author.mention}, here is some help. Hopes you understand me better after reading this! {Constants.PIFLOUZ_EMOJI}\n",
	    embed=embed_messages.get_embed_help_message(),
	    hidden=True)


@slash.slash(name="hello",
             description="Say hi!",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def hello_cmd(ctx):
	"""
  Callback for the hello command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	index = random.randint(0, len(Constants.greetings) - 1)
	await ctx.send(Constants.greetings[index].format(ctx.author.mention))


@slash.slash(name="donate",
             description="be generous to others",
             guild_ids=Constants.GUILD_IDS,
             options=[
                 create_option(name="user_receiver",
                               description="receiver",
                               option_type=option_type.USER,
                               required=True),
                 create_option(name="amount",
                               description="how much you want to give",
                               option_type=option_type.INTEGER,
                               required=True),
             ])
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
	assert piflouz_handlers.update_piflouz(
	    user_sender, qty=-amount,
	    check_cooldown=False), "Sender does not have enough money to donate"

	qty_tax = ceil(Constants.DONATE_TAX_RATIO / 100 * amount)
	qty_receiver = amount - qty_tax

	piflouz_handlers.update_piflouz(bot.user,
	                                qty=qty_tax,
	                                check_cooldown=False)
	piflouz_handlers.update_piflouz(user_receiver,
	                                qty=qty_receiver,
	                                check_cooldown=False)

	await ctx.send("Done!", hidden=True)

	await ctx.channel.send(
	    f"{user_sender.mention} sent {amount} {Constants.PIFLOUZ_EMOJI} to {user_receiver.mention}"
	)
	await utils.update_piflouz_message(bot)


@slash.slash(name="setupChannel",
             description="change my default channel",
             guild_ids=Constants.GUILD_IDS,
             options=[])
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

	# Piflouz mining message
	message = await ctx.channel.send(
	    embed=await embed_messages.get_embed_piflouz(bot))
	db["piflouz_message_id"] = message.id
	await message.add_reaction(Constants.PIFLOUZ_EMOJI)
	await message.pin()


@slash.slash(name="isLive",
             description="check if a certain streamer is live",
             guild_ids=Constants.GUILD_IDS,
             options=[
                 create_option(
                     name="streamer_name",
                     description="The name of the streamer you want to check",
                     option_type=option_type.STRING,
                     required=True)
             ])
async def is_live_cmd(ctx, streamer_name):
	"""
  Callback for the isLive command
  --
  input:
    ctx: discord_slash.context.SlashContext
    streamer_name: str
  """
	r = utils.get_live_status(streamer_name)
	if r["data"] != []:
		# The streamer is live
		title = r["data"][0]["title"]
		await ctx.send(
		    f"{streamer_name} is currently live on \"{title}\", go check out on http://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}"
		)
	else:
		# The streamer is not live
		await ctx.send(
		    f"{streamer_name} is not live yet. Follow http://www.twitch.tv/{streamer_name} to stay tuned ! {Constants.FUEGO_EMOJI}"
		)


@slash.slash(
    name="joke",
    description="to laugh your ass off (or not, manage your expectations)",
    guild_ids=Constants.GUILD_IDS,
    options=[])
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


@slash.slash(name="balance",
             description=f"check how many piflouz you have",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def balance_cmd(ctx):
	"""
  Callback for the balance command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	user = ctx.author
	assert "piflouz_bank" in db.keys() and str(
	    user.id) in db["piflouz_bank"].keys(), "User doesn't have an account"

	balance = db["piflouz_bank"][str(user.id)]
	content = f"{user.mention}, your balance is of {balance} {Constants.PIFLOUZ_EMOJI}! "
	await ctx.send(content, hidden=True)


@slash.slash(name="get",
             description="for the lazy one",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def get_cmd(ctx):
	"""
  Callback for the get command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	await ctx.defer(hidden=True)
	user = ctx.author
	successful_update = piflouz_handlers.update_piflouz(user)

	if not successful_update:
		timer = utils.get_timer(user)
		output_text = f"{user.mention}, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
	else:
		if str(user.id) not in db["powerups"].keys():
			db["powerups"][str(user.id)] = []

		qty = functools.reduce(
		    lambda accu, powerup_str: accu * eval(
		        powerup_str).get_piflouz_multiplier_value(),
		    db["powerups"][str(user.id)], Constants.NB_PIFLOUZ_PER_REACT)
		qty = int(qty)

		output_text = f"You just earned {qty} {Constants.PIFLOUZ_EMOJI}! Come back later for some more"

	await ctx.send(output_text, hidden=True)
	await utils.update_piflouz_message(bot)


@slash.slash(
    name="cooldown",
    description="when your addiction is stronger than your sense of time",
    guild_ids=Constants.GUILD_IDS,
    options=[])
async def cooldown_cmd(ctx):
	"""
  Callback for the cooldown command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	user = ctx.author
	timer = utils.get_timer(user)
	if timer > 0:
		output_text = f"{user.mention}, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
	else:
		output_text = f"{user.mention}, you can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
	await ctx.send(output_text, hidden=True)


@slash.slash(
    name="piflex",
    description=
    f"when you have too many piflouz /!\ Costs {Constants.PIFLEX_COST} piflouz",
    guild_ids=Constants.GUILD_IDS,
    options=[])
async def piflex_cmd(ctx):
	"""
  Callback for the piflex command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	user_id = str(ctx.author.id)

	# User has enough money
	if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(
	    ctx.author, qty=-Constants.PIFLEX_COST, check_cooldown=False):
		role = ctx.guild.get_role(Constants.MEGA_PIFLEXER_ROLE_ID)
		member = await ctx.guild.fetch_member(ctx.author.id)
		await member.add_roles(role)
		t = time.time()
		db["mega_piflexers"][user_id] = int(t)

		embed, index = embed_messages.get_embed_piflex(ctx.author)
		await ctx.send(embed=embed)

		if str(ctx.author_id) not in db["discovered_piflex"].keys():
			db["discovered_piflex"][str(ctx.author_id)] = []

		already_discovered = set(db["discovered_piflex"][str(ctx.author_id)])
		already_discovered.add(index)
		db["discovered_piflex"][str(ctx.author_id)] = list(already_discovered)

		await utils.update_piflouz_message(bot)

	# User doesn't have enough money
	else:
		balance = 0 if user_id not in db["piflouz_bank"].keys(
		) else db["piflouz_bank"][user_id]
		await ctx.send(
		    f"You need {Constants.PIFLEX_COST - balance} more {Constants.PIFLOUZ_EMOJI} to piflex!",
		    hidden=True)


@slash.slash(
    name="buyRankPiflex",
    description=
    f"flex with a custom rank /!\ Costs {Constants.PIFLEXER_COST} piflouz, lasts for {Constants.PIFLEXROLE_DURATION} seconds",
    guild_ids=Constants.GUILD_IDS,
    options=[])
async def buy_rank_piflex_cmd(ctx):
	"""
  Callback for the buyRankPiflex command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	user_id = str(ctx.author.id)
	member = await ctx.guild.fetch_member(user_id)
	role = ctx.guild.get_role(Constants.PIFLEXER_ROLE_ID)

	if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(
	    member, qty=-Constants.PIFLEXER_COST,
	    check_cooldown=False) and role not in member.roles:
		await member.add_roles(role)
		await ctx.send(f"{member.mention} just bought the piflexer rank!")
		await utils.update_piflouz_message(bot)
		db["piflexers"][user_id] = int(time.time())
	else:
		# User does not have enough money
		if role not in member.roles:
			await ctx.send(
			    f"You need {Constants.PIFLEXER_COST - db['piflouz_bank'][user_id]} {Constants.PIFLOUZ_EMOJI} to buy the rank!",
			    hidden=True)

		# User already have the rank
		else:
			await ctx.send("You already have the rank!", hidden=True)


@slash.slash(
    name="pilord",
    description="see how much you need to farm to flex with your rank",
    guild_ids=Constants.GUILD_IDS,
    options=[])
async def pilord_cmd(ctx):
	"""
  Callback for the pilord command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	user_id = str(ctx.author.id)
	if user_id not in db["piflouz_bank"].keys():
		db["piflouz_bank"][user_id] = 0

	if user_id in db["current_pilords"]:
		await ctx.send("You are currently a pilord. Kinda flexing right now!",
		               hidden=True)
	else:
		amount = db["piflouz_bank"][user_id]
		max_amount = db["piflouz_bank"][db["current_pilords"][0]]
		await ctx.send(
		    f"You need {max_amount - amount} {Constants.PIFLOUZ_EMOJI} to become pilord!",
		    hidden=True)


@slash.slash(
    name="raffle",
    description=f"buy raffle tickets to test your luck /!\ Costs piflouz",
    guild_ids=Constants.GUILD_IDS,
    options=[
        create_option(name="nb_tickets",
                      description="How many tickets?",
                      option_type=option_type.INTEGER,
                      required=True)
    ])
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
	assert isinstance(current_event,
	                  events.Raffle_event), "Current event is not a raffle"

	assert nb_tickets > 0, "You can't buy less than 1 ticket"

	price = nb_tickets * current_event.ticket_price

	user_id = str(ctx.author.id)

	# user doesn't have enough money
	assert piflouz_handlers.update_piflouz(
	    ctx.author, qty=-price, check_cooldown=False
	), f"User {ctx.author} doesn't have enough money to buy {nb_tickets} tickets"

	if not user_id in db["raffle_participation"].keys():
		db["raffle_participation"][user_id] = 0
	db["raffle_participation"][user_id] += nb_tickets

	await ctx.send(f"Successfully bought {nb_tickets} tickets", hidden=True)
	await current_event.update_raffle_message(bot)
	await utils.update_piflouz_message(bot)


@slash.slash(name="giveaway",
             description="launch a pibox with your own money",
             guild_ids=Constants.GUILD_IDS,
             options=[
                 create_option(name="amount",
                               description="How many piflouz",
                               option_type=option_type.INTEGER,
                               required=True)
             ])
async def giveaway_cmd(ctx, amount):
	"""
  Callback for the giveway command
  --
  input:
    ctx: discord_slash.context.SlashContext
    amount: int -> how many piflouz given
  """
	await ctx.defer(hidden=True)
	assert amount > 0, "The amount to giveaway has to be a strictly positive integer"

	user_sender = ctx.author
	# Trading
	assert piflouz_handlers.update_piflouz(
	    user_sender, qty=-amount,
	    check_cooldown=False), "Sender does not have enough money to giveaway"
	custom_message = f"This is a gift from the great {user_sender.mention}, be sure to thank him/her! "
	await piflouz_handlers.spawn_pibox(bot,
	                                   amount,
	                                   custom_message=custom_message,
	                                   ctx=ctx)
	await ctx.send("Done!", hidden=True)

	await utils.update_piflouz_message(bot)


@slash.slash(name="store",
             description="buy fun upgrades",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def store_cmd(ctx):
	"""
  Callback for the raffle command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	embed = embed_messages.get_embed_store_ui()
	message = await ctx.send(embed=embed)

	for react in Constants.POWERUPS_STORE.keys():
		await message.add_reaction(react)

	old_message_id = None
	if "store_message_id" in db.keys():
		old_message_id = db["store_message_id"]

	db["store_message_id"] = message.id

	try:
		if old_message_id is not None:
			old_message = await ctx.channel.fetch_message(old_message_id)
			await old_message.delete()
	except:
		print("Failed to delete old shop message")


@slash.slash(name="powerups",
             description="see how powerful you are",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def powerups_cmd(ctx):
	"""
  Callback for the powerups command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	await ctx.defer(hidden=True)
	user_id = str(ctx.author_id)
	content = "Here is the list of powerups you have at the moment:\n"
	has_any_powerup = False

	if user_id in db["powerups"].keys():
		for powerup_str in db["powerups"][user_id]:
			powerup = eval(powerup_str)
			content += powerup.get_info_str() + '\n'
			has_any_powerup = True

	if not has_any_powerup:
		content = "You don't have any power up at the moment. Go buy one, using `/store`!"
	await ctx.send(content, hidden=True)


@slash.slash(name="spawnPibox",
             description="The pibox master can spawn pibox",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def spawn_pibox_cmd(ctx):
	"""
  Callback for the spawnPibox command
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
	assert ctx.author.id == Constants.PIBOX_MASTER_ID, "Only the pibox master can use this command"
	piflouz_quantity = int(Constants.RANDOM_DROP_AVERAGE * random.random())
	custom_message = "It was spawned by the pibox master"
	await piflouz_handlers.spawn_pibox(bot, piflouz_quantity, custom_message)
	await ctx.send("Done!", hidden=True)


@slash.subcommand(base="duel",
                  name="challenge",
                  description="Duel someone to earn piflouz!",
                  guild_ids=Constants.GUILD_IDS,
                  options=[
                      create_option(name="user",
                                    description="Who do you want to duel?",
                                    required=True,
                                    option_type=option_type.USER),
                      create_option(name="amount",
                                    description="How much do you want to bet?",
                                    required=True,
                                    option_type=option_type.INTEGER),
                      create_option(
                          name="duel_type",
                          description="What game do you want to play?",
                          required=True,
                          option_type=option_type.STRING,
                          choices=[create_choice("Shifumi", "Shifumi")]),
                  ])
async def duel_challenge_cmd(ctx, user, amount, duel_type):
	"""
  Callback for the duel challenge command
  --
  input:
    ctx: discord.ext.commands.Context
    user: discord.User -> the person challenged
    amount: int -> how many piflouz involved by both users
    duel_type: string -> what kind of duel
  """
	await ctx.defer(hidden=True)
	assert ctx.author != user, "You can't challenge yourself!"
	assert amount > 1, "Amount should be strictly greater than 0"

	# Check if there is no duel with the person
	assert not any(
	    duel["user_id1"] == ctx.author_id and duel["user_id2"] == user.id
	    for duel in db["duels"]
	), "You already challenged this person to a duel, finish this one first"
	assert not any(
	    duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id
	    for duel in db["duels"]
	), "This person already challenged you to a duel, finish this one first"

	assert user != ctx.author, "You can't challenge yourself"

	# Check that the challenger has enough money
	assert piflouz_handlers.update_piflouz(
	    ctx.author, qty=-amount,
	    check_cooldown=False), "You don't have enough piflouz to do that"

	new_duel = utils.create_duel(ctx, user, amount, duel_type)
	db["duels"].append(new_duel)

	await ctx.channel.send(
	    f"{ctx.author.mention} challenged {user.mention} at {duel_type} betting {amount} {Constants.PIFLOUZ_EMOJI}! Use `/duel accept @{ctx.author.name}` to accept or `/duel deny @{ctx.author.name}` to deny."
	)
	await ctx.send("Done!", hidden=True)
	await utils.update_piflouz_message(bot)


@slash.subcommand(base="duel",
                  name="accept",
                  description="Accept someone's challenge",
                  guild_ids=Constants.GUILD_IDS,
                  options=[
                      create_option(
                          name="user",
                          description="The person who challenged you",
                          required=True,
                          option_type=option_type.USER)
                  ])
async def duel_accept_cmd(ctx, user):
	"""
  Callback for the duel accept command
  --
  input:
    ctx: discord.ext.commands.Context
    user: discord.User -> the person challenged
  """
	await ctx.defer(hidden=True)
	duel_index = None
	for i, duel in enumerate(db["duels"]):
		if duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id:
			duel_index = i
			break

	# Check the duel exists
	assert duel_index is not None, "This person did not challenge you to a duel"

	# Check the user has enough money
	assert piflouz_handlers.update_piflouz(
	    ctx.author,
	    qty=-db["duels"][duel_index]["amount"],
	    check_cooldown=False), "You don't have enough piflouz to do that"

	# Check that the user didn't already accept the duel
	assert not db["duels"][duel_index][
	    "accepted"], "You already accepted this challenge"

	db["duels"][duel_index]["accepted"] = True
	duel_type = db["duels"][duel_index]["duel_type"]

	await ctx.channel.send(
	    f"{ctx.author.mention} accepted {user.mention}'s challenge! Use `/duel play {duel_type} @[opponent] [your move]`"
	)
	await ctx.send("Done!", hidden=True)
	await utils.update_piflouz_message(bot)


@slash.subcommand(base="duel",
                  name="deny",
                  description="Deny someone's challenge",
                  guild_ids=Constants.GUILD_IDS,
                  options=[
                      create_option(
                          name="user",
                          description="The person who challenged you",
                          required=True,
                          option_type=option_type.USER)
                  ])
async def duel_deny_cmd(ctx, user):
	"""
  Callback for the duel deny command
  --
  input:
    ctx: discord.ext.commands.Context
    user: discord.User -> the person challenged
  """
	await ctx.defer(hidden=True)
	duel_index = None
	for i, duel in enumerate(db["duels"]):
		if duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id:
			duel_index = i
			break

	# Check the duel exists
	assert duel_index is not None, "This person did not challenge you to a duel"
	assert not db["duels"][duel_index][
	    "accepted"], "You already accepted this challenge"

	# Give back the money to the challenger
	piflouz_handlers.update_piflouz(user,
	                                qty=db["duels"][duel_index]["amount"],
	                                check_cooldown=False)

	del db["duels"][duel_index]
	await ctx.channel.send(
	    f"{ctx.author.mention} denied {user.mention}'s challenge!")
	await ctx.send("Done", hidden=True)
	await utils.update_piflouz_message(bot)


@slash.subcommand(base="duel",
                  name="cancel",
                  description="Cancel your challenge to someone",
                  guild_ids=Constants.GUILD_IDS,
                  options=[
                      create_option(name="user",
                                    description="The person you challenged",
                                    required=True,
                                    option_type=option_type.USER)
                  ])
async def duel_cancel_cmd(ctx, user):
	"""
  Callback for the duel cancel command
  --
  input:
    ctx: discord.ext.commands.Context
    user: discord.User -> the person challenged
  """
	await ctx.defer(hidden=True)
	duel_index = None
	for i, duel in enumerate(db["duels"]):
		if duel["user_id1"] == ctx.author_id and duel["user_id2"] == user.id:
			duel_index = i
			break

	# Check the duel exists
	assert duel_index is not None, "You did not challenge this person to a duel"
	assert not db["duels"][duel_index][
	    "accepted"], "This person already accepted the duel"

	# Give back the money to the challenger
	piflouz_handlers.update_piflouz(ctx.author,
	                                qty=db["duels"][duel_index]["amount"],
	                                check_cooldown=False)

	del db["duels"][duel_index]

	await ctx.channel.send(
	    f"{ctx.author.mention} cancelled his/her challenge to {user.mention}, what a loser"
	)
	await ctx.send("Done!", hidden=True)
	await utils.update_piflouz_message(bot)


@slash.subcommand(name="shifumi",
                  base="duel",
                  subcommand_group="play",
                  description="Play shifumi!",
                  guild_ids=Constants.GUILD_IDS,
                  options=[
                      create_option(name="user",
                                    description="Who do you play against?",
                                    required=True,
                                    option_type=option_type.USER),
                      create_option(name="value",
                                    description="What do you want to play?",
                                    required=True,
                                    option_type=option_type.STRING,
                                    choices=[
                                        create_choice("Rock", "Rock"),
                                        create_choice("Paper", "Paper"),
                                        create_choice("Scissors", "Scissors")
                                    ])
                  ])
async def duel_play_shifumi_cmd(ctx, user, value):
	"""
  Callback for the duel accept command
  --
  input:
    ctx: discord.ext.commands.Context
    user: discord.User
    value: string -> the move played by the player
  """
	await ctx.defer(hidden=True)
	duel_index = None
	for i, duel in enumerate(db["duels"]):
		if duel["user_id1"] == ctx.author_id and duel[
		    "user_id2"] == user.id or duel[
		        "user_id2"] == ctx.author_id and duel["user_id1"] == user.id:
			duel_index = i
			break

	# Check the duel exists
	assert duel_index is not None, "There is no challenge between you two"
	assert db["duels"][duel_index]["accepted"], "This duel is not accepted yet"

	if db["duels"][duel_index]["user_id1"] == ctx.author_id:
		assert db["duels"][duel_index]["move1"] is None, "You already played!"
		db["duels"][duel_index]["move1"] = value
		player1 = ctx.author
		player2 = user
	else:
		assert db["duels"][duel_index]["move2"] is None, "You already played!"
		db["duels"][duel_index]["move2"] = value
		player1 = user
		player2 = ctx.author

	# Bot players played
	move1 = db["duels"][duel_index]["move1"]
	move2 = db["duels"][duel_index]["move2"]

	await ctx.send("Done! Just wait for the other player to make a move",
	               hidden=True)

	money_if_win = 2 * db["duels"][duel_index]["amount"]

	win_shifumi = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
	if move1 is not None and move2 is not None:
		# Tie
		if move1 == move2:
			piflouz_handlers.update_piflouz(
			    player1,
			    qty=db["duels"][duel_index]["amount"],
			    check_cooldown=False)
			piflouz_handlers.update_piflouz(
			    player2,
			    qty=db["duels"][duel_index]["amount"],
			    check_cooldown=False)

			await ctx.channel.send(
			    f"{player1.mention} and {player2.mention} tied at {db['duels'][duel_index]['duel_type']}! They both played {move1}! They both got their money back"
			)

		# Player 1 won
		elif win_shifumi[move1] == move2:
			piflouz_handlers.update_piflouz(player1,
			                                qty=money_if_win,
			                                check_cooldown=False)

			await ctx.channel.send(
			    f"{player1.mention} won at {db['duels'][duel_index]['duel_type']} against {player2.mention}, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move1} vs {move2}"
			)

		# Player 2 won
		else:
			piflouz_handlers.update_piflouz(player2,
			                                qty=money_if_win,
			                                check_cooldown=False)

			await ctx.channel.send(
			    f"{player2.mention} won at {db['duels'][duel_index]['duel_type']} against {player1.mention}, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move2} vs {move1}"
			)

		del db["duels"][duel_index]
		await utils.update_piflouz_message(bot)


@slash.slash(name="ranking",
             description="See how worthy you are",
             guild_ids=Constants.GUILD_IDS,
             options=[])
async def ranking_cmd(ctx):
	"""
  Callback for the ranking command
  --
  input:
   ctx: discord.ext.commands.Context
  """
	await ctx.defer(hidden=True)
	d_piflouz = dict(db["piflouz_bank"])
	d_piflex = dict(db["discovered_piflex"])

	res = ""

	if str(ctx.author_id) in d_piflouz.keys():
		amount_user = d_piflouz[str(ctx.author_id)]
		rank = len([val
		            for val in d_piflouz.values() if val > amount_user]) + 1
		res += f"Piflouz ranking: {rank} with {amount_user} {Constants.PIFLOUZ_EMOJI}\n"
	if str(ctx.author_id) in d_piflex.keys():
		amount_user = len(d_piflex[str(ctx.author_id)])
		rank = len(
		    [val for val in d_piflex.values() if len(val) > amount_user]) + 1
		res += f"Piflex discovery ranking: {rank} with {amount_user} discovered piflex images\n"

	if res == "":
		await ctx.send("You are not part of any ranking", hidden=True)
	else:
		await ctx.send(res, hidden=True)


@slash.subcommand(
    name="get",
    base="role",
    description="Get a role",
    guild_ids=Constants.GUILD_IDS,
    options=[
        create_option(name="role",
                      description="Which role?",
                      required=True,
                      option_type=option_type.STRING,
                      choices=[
                          create_choice(str(Constants.TWITCH_NOTIF_ROLE_ID),
                                        "Twitch Notifications"),
                          create_choice(str(Constants.PIBOX_NOTIF_ROLE_ID),
                                        "Pibox Notifications"),
                      ])
    ])
async def get_role_cmd(ctx, role):
	"""
  Gives a role to the user
  --
  input:
    ctx: discord.ext.commands.Context
    role: discord.Role
  """
	role = bot.guilds[0].get_role(int(role))
	member = await bot.guilds[0].fetch_member(ctx.author_id)
	await member.add_roles(role)
	await ctx.send("Done!", hidden=True)


@slash.subcommand(
    name="remove",
    base="role",
    description="Get a role",
    guild_ids=Constants.GUILD_IDS,
    options=[
        create_option(name="role",
                      description="Which role?",
                      required=True,
                      option_type=option_type.STRING,
                      choices=[
                          create_choice(str(Constants.TWITCH_NOTIF_ROLE_ID),
                                        "Twitch Notifications"),
                          create_choice(str(Constants.PIBOX_NOTIF_ROLE_ID),
                                        "Pibox Notifications"),
                      ])
    ])
async def remove_role_cmd(ctx, role):
	"""
  Removes a role from the user
  --
  input:
    ctx: discord.ext.commands.Context
    role: discord.Role
  """
	role = bot.guilds[0].get_role(int(role))
	member = await bot.guilds[0].fetch_member(ctx.author_id)
	await member.remove_roles(role)
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

	channel = bot.get_channel(playload.channel_id)
	message = await channel.fetch_message(playload.message_id)
	guild = await bot.fetch_guild(playload.guild_id)
	user = await guild.fetch_member(playload.user_id)
	emoji = playload.emoji

	# Reaction to the Twitch notification message
	if "twitch_notif_message_id" in db.keys(
	) and message.id == db["twitch_notif_message_id"]:
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
	if "store_message_id" in db.keys(
	) and message.id == db["store_message_id"]:
		# Check mark or cross mark created by the bot
		if bot.user.id == user.id:
			if emoji.name == "✅" or emoji.name == "❌":
				await asyncio.sleep(2)
				await message.remove_reaction(emoji, user)
			return
		else:
			await message.remove_reaction(emoji, user)

		if emoji.name not in Constants.POWERUPS_STORE.keys():
			return

		user_id = str(user.id)

		if user_id not in db["powerups"].keys():
			db["powerups"][user_id] = []

		powerup = Constants.POWERUPS_STORE[emoji.name]
		if powerup.on_buy(user):
			await message.add_reaction("✅")
			await utils.update_piflouz_message(bot)
		else:
			await message.add_reaction("❌")

	# Reaction to the piflouz message
	if "piflouz_message_id" in db.keys(
	) and message.id == db["piflouz_message_id"]:
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
		await message.add_reaction(
		    reaction_to_show
		)  #This reaction will be deleted by this same function as it will be considered a new event.
		embed = await embed_messages.get_embed_piflouz(bot)
		await message.edit(embed=embed)

	# Random chest message
	if str(message.id) in db["random_gifts"]:
		emoji_required, qty, custom_message = db["random_gifts"][str(
		    message.id)]
		if str(emoji) == emoji_required:
			piflouz_handlers.update_piflouz(user, qty, False)

			del db["random_gifts"][str(message.id)]
			new_text_message = f"{user.mention} won {qty} {Constants.PIFLOUZ_EMOJI} from a pibox!"
			if custom_message is not None:
				new_text_message += " " + custom_message
			await message.edit(content=new_text_message)

			out_channel = bot.get_channel(db["out_channel"])
			embed = await embed_messages.get_embed_piflouz(bot)
			piflouz_message = await out_channel.fetch_message(
			    int(db["piflouz_message_id"]))
			await piflouz_message.edit(embed=embed)


if __name__ == "__main__":
	Constants.load()  # Due to import circular import issues
	keep_alive()
	bot.run(Constants.DISCORDTOKEN)
