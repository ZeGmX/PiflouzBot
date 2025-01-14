from aiohttp import ClientTimeout
import asyncpraw
from datetime import datetime
import interactions
from interactions import BrandColors, IntervalTrigger
from random import choice, shuffle
import time
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch

from constant import Constants
from custom_exceptions import CustomTaskError
from custom_task_triggers import TaskCustom as Task, TimeTriggerDT
from database import db
import embed_messages
from markdown import escape_markdown as escape_markdown
import powerups
import user_profile


async def get_live_status(user_name=None, helix=None):
    """
    Sends a request to the twich API about a streamer

    Parameters
    ----------
    user_name (string):
        name of the streamer
    helix (twitchAPI.twitch.Twitch)

    Returns
    -------
    stream (twitchAPI.object.api.Stream)
    """
    try:
        if helix is None:
            helix = await Twitch(Constants.TWITCH_ID, Constants.TWITCH_SECRET, session_timeout=ClientTimeout(total=30))

        return await first(helix.get_streams(user_login=user_name))
    except TimeoutError:
        raise CustomTaskError("TimeoutError in get_live_status")


@Task.create(IntervalTrigger(seconds=30))
async def task_check_live_status(bot):
    """
    Checks if the best streamers are live on Twitch every few seconds
    This will be executed every 30 seconds
    """
    print("checking live status")

    if "twitch_channel" in db.keys():
        helix = await Twitch(Constants.TWITCH_ID, Constants.TWITCH_SECRET, session_timeout=ClientTimeout(total=30))

        is_live = db["is_currently_live"]

        for streamer_name in Constants.STREAMERS:
            stream = await get_live_status(user_name=streamer_name, helix=helix)

            if stream is not None:
                if streamer_name not in is_live.keys() or streamer_name not in db["previous_live_message_time"].keys():
                    is_live[streamer_name] = False
                    db["previous_live_message_time"][streamer_name] = 0

                if not is_live[streamer_name]:
                    is_live[streamer_name] = True
                    await send_new_live_message(bot, stream, streamer_name)

            elif is_live[streamer_name]:
                is_live[streamer_name] = False


async def send_new_live_message(bot, stream, streamer_name):
    """
    Sends a message saying a streamer is now live

    Parameters
    ----------
    bot (interactions.Client)
    stream (twitch.helix.Stream)
    streamer_name (str):
        the name of the streamer who went live
    """
    current_live_message_time = int(time.time())
    if (current_live_message_time - db["previous_live_message_time"][streamer_name]) >= Constants.TWITCH_ANNOUNCEMENT_DELAY:  # Checks if we waited long enough
        db["previous_live_message_time"][streamer_name] = current_live_message_time

        out_channel = await bot.fetch_channel(db["twitch_channel"])
        role = await bot.guilds[0].fetch_role(Constants.TWITCH_NOTIF_ROLE_ID)

        msg = escape_markdown(f"{role.mention} {streamer_name} is currently live on \"{stream.title}\", go check out on https://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}")
        await out_channel.send(msg)
    else:
        print(f"Found {streamer_name}, but cooldown was still up")


async def get_otter_image():
    """
    Returns the url to a random otter image from r/otters on Reddit
    """
    reddit = asyncpraw.Reddit(
        client_id=Constants.REDDIT_ID,
        client_secret=Constants.REDDIT_SECRET,
        user_agent=Constants.REDDIT_USER_AGENT
    )
    sub = await reddit.subreddit("otters")
    async for submission in sub.random_rising():
        if submission.url.endswith(".jpg") or submission.url.endswith(".jpeg") or submission.url.endswith(".png") or submission.url.endswith(".gif"):
            break

    return submission.url


@Task.create(TimeTriggerDT(Constants.OTTER_IMAGE_TIME))
async def generate_otter_of_the_day(bot):
    """
    Generates a new otter image every day to brighten everyone's day

    Parameters
    ----------
    bot (interactions.Client)
    """
    if "out_channel" not in db.keys():
        return

    out_channel = await bot.fetch_channel(db["out_channel"])
    embed = await embed_messages.get_embed_otter()
    await out_channel.send(embeds=embed)


@Task.create(TimeTriggerDT(Constants.SHUFFLE_NAME_TIME))
async def shuffle_names(bot):
    """
    Generates a new otter image every day to brighten everyone's day

    Parameters
    ----------
    bot (interactions.Client)
    """
    guild = bot.guilds[0]
    await guild.gateway_chunk()  # to load all members
    members = guild.members
    owner = await guild.fetch_owner()
    chaos_members = list(filter(lambda member: Constants.CHAOS_ROLE_ID in member.roles and int(member.id) != owner.id, members))

    names = [member.display_name for member in chaos_members]
    shuffle(names)

    for nick, member in zip(names, chaos_members):
        await member.edit_nickname(nick)


@Task.create(TimeTriggerDT(Constants.BIRTHDAY_CHECK_TIME))
async def check_birthday(bot: interactions.Client):
    """
    Task that checks if it is the birthday of any member of the server

    Parameters
    ----------
    bot (interactions.Client)
    """
    print("Checking birthdays")
    birthdays = user_profile.get_all_birthdays()

    current_date = datetime.now(tz=Constants.TIMEZONE).date().strftime('%Y-%m-%d')
    to_celebrate = []
    for member_id, member_birthday_date in birthdays.items():
        # Check the birthday date of each member.
        print(f"Birthday date of {member_id} : {member_birthday_date}")
        if member_birthday_date[5:] == current_date[5:]:
            to_celebrate.append(member_id)
    nb_birthdays = len(to_celebrate)
    if nb_birthdays == 0:
        return

    current_time = int(time.time())
    birthday_powerup = powerups.BirthdayMultiplier(0, 100, 86400, current_time)
    output_message = "Today is the birthday of "
    for i, member_id in enumerate(to_celebrate):
        member_mention = f"<@{member_id}>"
        current_member_profile = user_profile.get_profile(member_id)

        # Sanity check
        if (
            "previous_birthday_powerup" in current_member_profile
            and current_time - current_member_profile["previous_birthday_powerup"] <= 360 * 24 * 60 * 60
        ):
            print(f"Member {member_id} did not get a birthday powerup because their last one was less than 360 days ago.")

        # Add the powerup to the member via a "fake" buy
        elif birthday_powerup.on_buy(member_id, current_time):
            current_member_profile["previous_birthday_powerup"] = current_time  # The powerup is sucessfully applied to the member.
        else:
            print(f"Failed to add birthday powerup to {member_id} when I should have been able to.\nMaybe they already have this powerup?")

        # Add the mention of the current member to the global message.
        if i == 0:
            output_message += member_mention
        else:
            output_message += f", {member_mention}"
    output_message += " "
    title_message = "HAPPY BIRTHDAY "
    birthday_emojis = [":birthday:", ":tada:", Constants.FUEGO_EMOJI]
    for _ in range(3):
        output_message += choice(birthday_emojis)
        title_message += choice(birthday_emojis)
    output_message += "!\nWish them an happy birthday!\nThey also got a special powerup, use `/profile` to check it out."
    title_message += "!"

    embed = embed_messages.Embed(title=title_message, thumbnail=embed_messages.EmbedAttachment(url=Constants.PIBOU4BIRTHDAY_URL),
            description=output_message,
            color=BrandColors.RED
    )

    out_channel = await bot.fetch_channel(db["out_channel"])
    await out_channel.send(embed=embed)
