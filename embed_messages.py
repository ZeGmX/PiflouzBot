import discord
import random
from replit import db
import datetime
from dateutil.relativedelta import relativedelta

from constant import Constants
import socials
import utils


def get_embed_help_message():
  """
  Returns the embed message with help for every command
  --
  output:
    embed: discord.Embed -> the embeded message
  """
  embed = discord.Embed(title="Need help?", colour=discord.Colour.red())
  embed.set_thumbnail(url=Constants.PIBOU4LOVE_URL)

  embed.add_field(
    name="`/help`",
    value="show this message",
  )
  embed.add_field(
    name="`/hello`",
    value="say hi!",
  )
  embed.add_field(
    name="`/isLive streamer_name`",
    value="check if a certain streamer is live!",
  )
  embed.add_field(
    name="`/setupChannel [twitch|main]`",
    value="change the channel where I send messages",
  )
  embed.add_field(
    name="`/joke`",
    value="to laugh your ass off (or not, manage your expectations)",
  )
  embed.add_field(
    name="`/donate @user amount`",
    value="be generous to others",
  )
  embed.add_field(
    name="`/balance [@user]`",
    value=f"check how many {Constants.PIFLOUZ_EMOJI} the user has",
  )
  embed.add_field(
    name="`/cooldown`",
    value="when your addiction is stronger than your sense of time",
  )
  embed.add_field(
    name="`/get`",
    value="for the lazy ones",
  )
  embed.add_field(
    name="`/piflex`",
    value=f"when you have too many {Constants.PIFLOUZ_EMOJI}\n /!\ Costs {Constants.PIFLEX_COST} {Constants.PIFLOUZ_EMOJI}",
  )
  embed.add_field(
    name="`/buyRankPiflex`",
    value=f"flex with a custom rank\n /!\ Costs {Constants.PIFLEXER_COST} {Constants.PIFLOUZ_EMOJI}, lasts for {utils.seconds_to_formatted_string(Constants.PIFLEXROLE_DURATION)}",
  )
  embed.add_field(
    name="`$tarpin`",
    value="what could that be? Can be used in any channel",
  )
  embed.add_field(
    name="`/pilord`",
    value="see how much you need to farm to flex with your rank",
  )
  embed.add_field(
    name="`/raffle n`",
    value="buy raffle tickets to test your luck",
  )
  embed.add_field(
    name="`/store`",
    value="buy fun upgrades",
  )
  embed.add_field(
    name="`/powerups`",
    value="see how powerful you are",
  )
  embed.add_field(
    name="`/giveaway n`",
    value="launch a pibox with your own money",
  )
  embed.add_field(
    name="`duel [accept|deny|challenge|cancel|play|status]`",
    value="earn piflouz by winning challenges against others",
  )
  embed.add_field(
    name="`/ranking`",
    value="check how worthy you are",
  )
  embed.add_field(
    name="`/role [get|remove]`",
    value="get a specific notification role"
  )
  embed.add_field(
    name="`/seasonresult`",
    value="check how good you were last season"
  )
  embed.add_field(
    name="`/achievements list`",
    value="check what you need to do to get some achievements"
  )

  embed.add_field(
    name="Things I do in the background",
    value=f"- I will send a message everytime the greatest streamers go live on Twitch\n\
- I can give you {Constants.PIFLOUZ_EMOJI} if you click on the button below the piflouz message\n\
- I spawn random gifts from time to time. Be the first to react to earn more {Constants.PIFLOUZ_EMOJI}\n\
- I update the roles\n\
- I create events every day\n\
- I send a cute otter picture everyday",
    inline=False
  )
  return embed


def get_embed_piflouz(bot):
  """
  Creates an embed message containing the explanation for the piflouz game and the balance
  --
  input:
    bot: discord.ext.commands.Bot
  --
  output:
    embed: discord.Embed -> the message
  """
  last_begin_time = datetime.datetime.fromtimestamp(db["last_begin_time"])
  end_time = last_begin_time + relativedelta(months=3)
  desc = f"This is the piflouz mining message, click every {Constants.REACT_TIME_INTERVAL} seconds to gain more {Constants.PIFLOUZ_EMOJI}.\n\n\
You just need to click on the {Constants.PIFLOUZ_EMOJI} button below or use the `/get` command.\n\
If you waited long enough ({utils.seconds_to_formatted_string(Constants.REACT_TIME_INTERVAL)}), you will earn some {Constants.PIFLOUZ_EMOJI}! The amount depends on the current event, you powerups, your mining combo and your accuracy to use /get.\n\n\
This season will end on <t:{int(end_time.timestamp())}>.\nYour goal is to earn, donate and flex with as much piflouz as possible. You will earn rewards based on the amount of piflouz you earn and your different rankings."

  embed = discord.Embed(
    title=f"Come get some {Constants.PIFLOUZ_EMOJI}!",
    description=desc,
    colour=discord.Colour.gold()
  )
  # Piflouz thumbnail
  embed.set_thumbnail(url=Constants.PIFLOUZ_URL)

  # Rankings
  if "piflouz_bank" in db.keys():
    d_piflouz = dict(db["piflouz_bank"])
    d_piflex = [(user_id, len(discovered)) for user_id, discovered in db["discovered_piflex"].items()]
    d_donations = [(user_id, val) for user_id, val in db["donation_balance"].items() if val > 0]

    ranking_balance = get_ranking_str(list(d_piflouz.items()))
    ranking_piflex = get_ranking_str(d_piflex)
    ranking_donations = get_ranking_str(d_donations)
    
    if ranking_balance != "":
      embed.add_field(name="Balance", value=ranking_balance, inline=True)
    if ranking_piflex != "":
      embed.add_field(name="Piflex Discovery", value=ranking_piflex, inline=True)
    if ranking_donations != "":
      embed.add_field(name="Donations", value=ranking_donations, inline=False)

  return embed


def get_ranking_str(L):
  """
  Returns a string representing the ranking for a given score
  --
  input:
    L: (user_id: str, score: int) list
  --
  output:
    res: str
  """
  res = ""
  previous_val, previous_index = 0, 0
  vals = sorted(L, key=lambda key_val: -key_val[1])
  for i, (user_id, val) in enumerate(vals):
    if i == 10: break # The embed has a limited size so we limit the amount of user in each ranking

    index = i if val != previous_val else previous_index
    previous_val, previous_index = val, index
    res += f"{index + 1}: <@{user_id}> - {val}\n"
  return res

def get_embed_twitch_notif():
  """
  Returns an embed message on which to react to get the role to get notified when pibou421 goes live on Twitch
  --
  output:
    embed: discord.Embed -> the message
  """
  embed = discord.Embed(
    title="Twitch notification role",
    description="React to get/remove the Twitch notifications role",
    colour=discord.Colour.purple()
  )
  embed.set_thumbnail(url=Constants.PIBOU_TWITCH_THUMBNAIL_URL)
  return embed


def get_embed_piflex(user):
  """
  Returns an embed message corresponding to the piflex message
  --
  input:
    user: user -> the user requesting the piflex
  --
  output:
    embed: discord.Embed -> the message
    index: int -> index of the image/gif
  """
  embed = discord.Embed(
    title="PIFLEX",
    description=f"Look how much piflouz {user.mention} has. So much piflouz that he/she is flexing on you poor peasants! He/She is so cool and rich that he/she can just take a bath in piflouz. You mad?",
    colour=discord.Colour.gold()
  )
  embed.set_thumbnail(url=Constants.PIBOU4STONKS_URL)
  
  index = random.randrange(0, len(Constants.PIFLEX_IMAGES_URL))
  image_url = Constants.PIFLEX_IMAGES_URL[index]
  print(f"Piflex with {image_url}")
  embed.set_image(url=image_url)

  return embed, index


def get_embed_store_ui():
  """
  Returns an embed message corresponding to the store message
  --
  output:
    embed: discord.Embed -> the message
  """
  embed = discord.Embed(
    title="Piflouz shop",
    description="Here you can buy useful upgrades!",
    colour=discord.Colour.dark_magenta()
  )

  for emoji, powerup in Constants.POWERUPS_STORE.items():
    embed.add_field(
      name=emoji,
      value=powerup.get_store_str(),
      inline=True
    )

  return embed


async def get_embed_otter():
  """
  Returns an embed corresponding to a random otter image
  --
  output:
    embed: discord.Embed -> the message
  """ 
  embed = discord.Embed(
    title="Otter image of the day!",
    colour=discord.Colour.from_rgb(101, 67, 33)  # brown
  )
  url = await socials.get_otter_image()
  embed.set_image(url=url) 
  return embed


async def get_embed_end_season(bot):
  """
  Returns an embed announcing the end of a season
  --
  output:
    embed: discord.Embed -> the message
  """
  channel = bot.get_channel(db["out_channel"])
  msg = await channel.fetch_message(db["piflouz_message_id"])
  
  embed = discord.Embed(
    title="The season is over!",
    description=f"The last season has ended! Use the `/seasonresults` to see what you earned. Congratulations to every participant!\nThe final rankings are available [here]({msg.jump_url})",
    colour=discord.Colour.purple()
  )
  embed.set_thumbnail(url=Constants.TURBO_PIFLOUZ_ANIMATED_URL)

  return embed