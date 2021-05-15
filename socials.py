from discord.ext import tasks
from replit import db
import requests
import time
import asyncpraw
import os

from constant import Constants
import embed_messages
import utils


@tasks.loop(seconds=30)
async def task_check_live_status(bot):
  """
  Checks if the best streamers are live on Twitch every few seconds
  This will be executed every 30 seconds
  --
  bot: discord.ext.commands.Bot
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
        await send_new_live_message(bot, r, streamer_name)

      elif r["data"] == [] and db["is_currently_live"][streamer_name]:
        # The live just ended
        print("The live ended")
        db["is_currently_live"][streamer_name] = False


async def send_new_live_message(bot, r, streamer_name):
  """
  Sends a message saying pibou421 is now live
  --
  input:
    bot: discord.ext.commands.Bot
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
    
  out_channel = bot.get_channel(db["out_channel"])
  embed = await embed_messages.get_embed_otter()
  await out_channel.send(embed=embed)
