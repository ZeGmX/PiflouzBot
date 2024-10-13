from interactions import Activity, ActivityType, Intents, Status, listen
import logging
import logging.config
import matplotlib
import traceback

from achievement_handler import AchievementHandlerExt
from constant import Constants
from custom_client import Client
from custom_exceptions import CustomAssertError
from database import db
import events
import pibox
import powerups
import rank_handlers
import seasons
import socials
import utils


matplotlib.use('Agg')
logging.basicConfig(filename="logs.log", level=logging.WARNING, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s")

cls_log = logging.getLogger("interactions_log")
cls_log.setLevel(logging.WARNING)

logger = logging.getLogger("custom_log")
logger.setLevel(logging.INFO)


intents = Intents.new(guild_members=True, message_content=True, guild_messages=True, guild_message_reactions=True, direct_messages=True, guilds=True)
activity = Activity.create(name="Piflouz generator", type=ActivityType.CUSTOM, state="Generating piflouz")
bot = Client(token=Constants.DISCORD_TOKEN, intents=intents, scope=Constants.GUILD_IDS, status=Status.ONLINE, activity=activity, send_command_tracebacks=False, logger=cls_log)


@listen(disable_default_listeners=True)
async def on_error(error):  # noqa: D103
    if not isinstance(error.error, CustomAssertError):
        msg = f"Got the following error in {error.source}: {error.error}"
        msg += f"\nHad the following arguments: {error.args}"
        msg += f"\nHad the following kwargs: {error.kwargs}"
        msg += f"\nHad the following context: {error.ctx}"
        msg += "\n" + "".join(traceback.format_exception(error.error))
        print(f"\033[91m{msg}\033[0m")
        logger.error(msg)
    else:
        msg = f"Got the following error in {error.source}: {error.error}"
        print(f"\033[93m{msg}\033[0m")
        logger.warning(msg)


@listen()
async def on_startup():
    """
    Function executed when the bot correctly connected to Discord
    """
    print(f"I have logged in as {bot.user.display_name} - id: {bot.user.id}")
    logger.info("Bot startup")
    # utils.update_db()

    # Setting the base parameters in the database
    for key in [
        "random_gifts",         # information about current piboxes
        "mega_piflexers",       # buy date of user doing /piflex
        "piflexers",            # buy date of user doing /buyrankpiflex
        "wyr_edit",             # to keep track of the "Would you rather?" message being updated
        "piflouz_generated",    # to keep track of the piflouz generated by the bot through the season
        "events",               # gathering all the data relative to the events
        "is_currently_live",    # to keep track of the live status of the streamers
        "previous_live_message_time"  # to keep track of the last time a live message was sent for each streamer
    ]:
        if key not in db.keys():
            db[key] = dict()

    for key in [
        "current_pilords",      # list of the current pilords
        "duels",                # list of active duels
        "current_piflex_masters",  # list of the current piflex masters
    ]:
        if key not in db.keys():
            db[key] = []

    for streamer_name in Constants.STREAMERS:
        if streamer_name not in db["is_currently_live"].keys():
            db["is_currently_live"][streamer_name] = False
        if streamer_name not in db["previous_live_message_time"].keys():
            db["previous_live_message_time"][streamer_name] = 0

    if "profiles" not in db.keys():
        db["profiles"] = {"active": {}, "inactive": {}}

    for key in ["get", "event", "pibox", "miner", "achievement"]:
        if key not in db["piflouz_generated"].keys():
            db["piflouz_generated"][key] = 0

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
        AchievementHandlerExt.add_custom_listener_for_achievements(bot, event_name)

    events.event_handlers.start(bot)
    pibox.pibox_task.start(bot)
    powerups.handle_actions_every_hour.start(bot)
    rank_handlers.update_ranks.start(bot)
    seasons.season_task.start(bot)
    socials.generate_otter_of_the_day.start(bot)
    socials.task_check_live_status.start(bot)
    socials.shuffle_names.start(bot)
    socials.check_birthday.start(bot)
    utils.backup_db.start()

    await pibox.load_all_pibox(bot)
    await events.register_listeners(bot)
    await events.wait_for_buffer_ready(bot)


@listen()
async def on_message_create(message_event):
    """
    Listner function executed when a message is sent

    Parameters
    ----------
    message_event (interactions.MessageCreate):
        the message create event
    """
    message = message_event.message
    if message.author.id == int(bot.user.id): return

    if message.content is not None and "$tarpin" in message.content:
        await message.reply("Du quoi ?")
        return


if __name__ == "__main__":
    Constants.load()  # Due to import circular import issues

    import achievements  # to register the listeners  # noqa: F401

    bot.load_extension("achievement_handler")
    bot.load_extension("cogs.cog_achievements")
    bot.load_extension("cogs.cog_buy")
    bot.load_extension("cogs.cog_duels")
    bot.load_extension("cogs.cog_event")
    bot.load_extension("cogs.cog_misc")
    bot.load_extension("cogs.cog_piflouz_mining")
    bot.load_extension("cogs.cog_status_check")
    bot.load_extension("cogs.cog_would_you_rather")
    bot.load_extension("cogs.cog_birthday_tracker")

    bot.start()
