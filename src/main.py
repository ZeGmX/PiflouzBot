from dotenv import load_dotenv
load_dotenv()

from interactions import Intents, Activity, ActivityType, Status
from interactions import listen
import logging
import os

from achievement_handler import Achievement_handler_ext
from constant import Constants
from custom_client import Client
from my_database import db
import events
import piflouz_handlers
import powerups
import rank_handlers
import seasons
import socials
import utils


intents = Intents.new(guild_members=True, message_content=True, guild_messages=True, guild_message_reactions=True, direct_messages=True, guilds=True)
activity = Activity(name="Piflouz generator", type=ActivityType.CUSTOM, state="Generating piflouz")
bot = Client(token=Constants.DISCORD_TOKEN, intents=intents, scope=Constants.GUILD_IDS, status=Status.ONLINE, activity=activity)
  

@listen(disable_default_listeners=True)
async def on_error(error):
  print(f"Got the following error in {error.source}: {error.error}")
  print("Had the following arguments:", error.args)
  print("Had the following kwargs:", error.kwargs)
  print("Had the following context:", error.ctx)


@listen()
async def on_startup():
  """
  Function executed when the bot correctly connected to Discord
  """
  print(f"I have logged in as {bot.user.display_name} - id: {bot.user.id}")

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
    "mining_combo",         # the current combo for mining piflouz
    "turbo_piflouz_bank",   # money after each season
    "donation_balance",     # money donated - money received throug donations
    "season_results",       # recap of the money earned last season
    "achievements",         # list of the achievements unlocked by a user
    "wordle_guesses",       # list of the wordle guesses by a user
    "last_birthday_delivery",    # for the birthday event
    "birthday_event_ingredients",# also for the birthday event
    "baked_cakes",               # also for the birthday event
    "wyr_edit"              # to keep track of the "Would you rather?" message being updated
  ]:
    if key not in db.keys():
      db[key] = dict()
  
  for key in [
    "current_pilords",      # list of the current pilords
    "duels",                # list of active duels
    "current_piflex_masters",  # list of the current piflex masters
    "birthday_raffle_participation"  # for the birthday raffle event
  ]:
    if key not in db.keys():
      db[key] = []

  if "is_currently_live" not in db.keys():
    db["is_currently_live"] = {streamer_name: False for streamer_name in Constants.streamers_to_check}
  
  if "previous_live_message_time" not in db.keys():
    db["previous_live_message_time"] = {name: 0 for name in Constants.streamers_to_check}

  custom_event = [
    "piflexer_rank_bought",
    "piflex_bought",
    "donation_successful", 
    "giveaway_successful",
    "store_purchase_successful",
    "raffle_participation_successful",
    "raffle_won",
    "become_pilord",
    "pibox_obtained",
    "pibox_failed",
    "duel_created",
    "duel_won",
    "duel_accepted",
    "combo_updated"
  ]

  for event_name in custom_event:
    Achievement_handler_ext.add_custom_listener_for_achievements(bot, event_name)
  
  events.event_handlers.start(bot)
  piflouz_handlers.random_gift.start(bot)
  powerups.handle_actions_every_hour.start(bot)
  seasons.season_task.start(bot)
  socials.generate_otter_of_the_day.start(bot)
  socials.task_check_live_status.start(bot)
  utils.backup_db.start()
  rank_handlers.update_ranks.start(bot)
  socials.shuffle_names.start(bot)




@listen()
async def on_message_create(message_event):
  """
  Listner function executed when a message is sent
  --
  input:
    message_event: interactions.MessageCreate -> the message create event
  """
  message = message_event.message
  if message.author.id == int(bot.user.id): return
  
  if message.content is not None and "$tarpin" in message.content:
    await message.reply("Du quoi ?")
    return


@listen()
async def on_message_reaction_add(reac_event):
  """
  Listener function executed when a reaction is added to a message
  --
  input:
    reac_event: interactions.MessageReactionAdd 
  """

  message_id = reac_event.message.id
  if str(message_id) not in db["random_gifts"]:
    return

  message = reac_event.message
  user = reac_event.author
  emoji = reac_event.reaction.emoji

  # Random chest message
  if str(message_id) in db["random_gifts"]:
    id_required, qty, custom_message = db["random_gifts"][str(message_id)]
    
    if emoji.id is not None and int(emoji.id) == id_required:
      # piflouz_handlers.update_piflouz(user.id, qty, False)

      del db["random_gifts"][str(message_id)]
      new_text_message = f"{user.mention} won {qty} {Constants.PIFLOUZ_EMOJI} from a pibox!"
      if custom_message is not None:
        new_text_message += " " + custom_message
      await message.edit(content=new_text_message)

      await utils.update_piflouz_message(bot)
      bot.dispatch("pibox_obtained", user.id, qty)
    else:
      bot.dispatch("pibox_failed", user.id, qty)
  



if __name__ == "__main__":
  Constants.load()  # Due to import circular import issues
 
  import achievements # to register the listeners

  bot.load_extension("achievement_handler")
  bot.load_extension("cog_achievements")
  bot.load_extension("cog_buy")
  bot.load_extension("cog_duels")
  bot.load_extension("cog_event")
  bot.load_extension("cog_misc")
  bot.load_extension("cog_piflouz_mining")
  bot.load_extension("cog_status_check")
  bot.load_extension("cog_would_you_rather")

  db["birthday_raffle_participation"] = []

  bot.start()