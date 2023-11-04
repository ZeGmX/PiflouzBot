from discord.ext import tasks
from discord.utils import escape_markdown
from my_database import db
import time
import asyncpraw
import twitch
from interactions import Role, Guild
from random import shuffle

from constant import Constants
import embed_messages
import utils


def get_live_status(user_name, helix=None):
  """
  Sends a request to the twich API about a streamer
  --
  input:
    user_name: string -> name of the streamer
    helix: twitch.Helix
  --
  output:
    stream: twitch.helix.models.stream.Stream
  """
  if helix is None:
    helix = twitch.Helix(Constants.TWITCH_ID, Constants.TWITCH_SECRET)
  try:
    stream = helix.stream(user_login=user_name)  # Returns an error if the streamer is not live
    return stream
  except twitch.helix.resources.StreamNotFound:
    return None


@tasks.loop(seconds=30)
async def task_check_live_status(bot):
  """
  Checks if the best streamers are live on Twitch every few seconds
  This will be executed every 30 seconds
  --
  bot: interactions.Client
  """
  print("checking live status")

  if "twitch_channel" in db.keys():
    helix = twitch.Helix(Constants.TWITCH_ID, Constants.TWITCH_SECRET)
    for streamer_name in Constants.STREAMERS:
      stream = get_live_status(streamer_name, helix=helix)
      if stream is not None:
        if streamer_name not in db["is_currently_live"].keys() or streamer_name not in db["previous_live_message_time"].keys():
          db["is_currently_live"][streamer_name] = False
          db["previous_live_message_time"][streamer_name] = 0

        if not db["is_currently_live"][streamer_name]:
          db["is_currently_live"][streamer_name] = True
          await send_new_live_message(bot, stream, streamer_name)

      else:
        db["is_currently_live"][streamer_name] = False


async def send_new_live_message(bot, stream, streamer_name):
  """
  Sends a message saying a streamer is now live
  --
  input:
    bot: interactions.Client
    stream: twitch.helix.Stream
    streamer_name: str -> the name of the streamer who went live
  """
  current_live_message_time = int(time.time())
  if (current_live_message_time - db["previous_live_message_time"][streamer_name]) >= Constants.TWITCH_ANNOUNCEMENT_DELAY:  #Checks if we waited long enough
    db["previous_live_message_time"][streamer_name] = current_live_message_time
    out_channel = await bot.get_channel(db["twitch_channel"])
    role = Role(id=Constants.TWITCH_NOTIF_ROLE_ID)
    msg = escape_markdown(f"{role.mention} {streamer_name} is currently live on \"{stream.title}\", go check out on https://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}")
    await out_channel.send(msg)
  else:
    print(f"Found {streamer_name}, but cooldown was still up.")


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
  #submissions = sub.top("day", limit=4)
  submission = await sub.random()
  
  while not (submission.url.endswith(".jpg") or submission.url.endswith(".png") or submission.url.endswith(".gif")):
    submission = await sub.random()
  
  return submission.url


@tasks.loop(hours=24)
async def generate_otter_of_the_day(bot):
  """
  Generates a new otter image every day to brighten everyone's day
  --
  input:
    bot: discord.ext.commands.Bot
  """
  await utils.wait_until(Constants.OTTER_IMAGE_TIME)

  if "out_channel" not in db.keys():
    return
    
  out_channel = await bot.get_channel(db["out_channel"])
  embed = await embed_messages.get_embed_otter()
  await out_channel.send(embeds=embed)


@tasks.loop(hours=24)
async def shuffle_names(bot):
  """
  Generates a new otter image every day to brighten everyone's day
  --
  input:
    bot: discord.ext.commands.Bot
  """
  await utils.wait_until(Constants.SHUFFLE_NAME_TIME)
  
  guild = bot.guilds[0]
  members = await guild.get_list_of_members(limit=50)
  chaos_members = list(filter(lambda member: Constants.CHAOS_ROLE_ID in member.roles and int(member.id) != guild.owner_id, members))

  names = [member.name for member in chaos_members]
  shuffle(names)
  
  for nick, member in zip(names, chaos_members):
    await member.modify(nick=nick)
    