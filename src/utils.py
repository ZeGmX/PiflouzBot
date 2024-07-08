import asyncio
import datetime
from functools import wraps
from interactions import Button, ButtonStyle
import pickle
from pyimgur import Imgur
import requests

from constant import Constants
from custom_exceptions import Custom_Assert_Exception
from custom_task_triggers import TaskCustom as Task, TimeTriggerDT
import embed_messages
from my_database import db
import powerups  # Used in eval()
import events  # Used in eval()


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


async def update_piflouz_message(bot):
    """
    Updates the piflouz message with the rankings
    --
    input:
        bot: interactions.Client
    """
    from cogs import Cog_piflouz_mining
    
    channel = await bot.fetch_channel(db["out_channel"])
    embed = embed_messages.get_embed_piflouz()
    piflouz_message = await channel.fetch_message(db["piflouz_message_id"])
    piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id="piflouz_mining_button", emoji=Constants.PIFLOUZ_EMOJI)
    piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id=Cog_piflouz_mining.BUTTON_NAME, emoji=Constants.PIFLOUZ_EMOJI)
    await piflouz_message.edit(embeds=embed, components=piflouz_button)


async def wait_until(then):
    """
    Waits until a certain time of the day (or the next day)
    --
    input:
        then: datetime.datetime
    """
    tz = Constants.TIMEZONE
    now = datetime.datetime.now(tz=tz)
    then = now.replace(hour=then.hour, minute=then.minute, second=then.second).astimezone(tz)

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


@Task.create(TimeTriggerDT(datetime.time(hour=23)))
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
        folder = now.strftime("%Y_%m_%d_%Hh%Mmin%Ss")
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
        raise Custom_Assert_Exception(msg)


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


def update_db():
    """
    Upgrades the database when going from v1.12 to v1.13
    """
    db["events"]["passive"]["buffered_event"] = ""
    db["events"]["challenge"]["buffered_event"] = ""
    db["events"]["passive"]["buffered_data"] = dict()
    db["events"]["challenge"]["buffered_data"] = dict()