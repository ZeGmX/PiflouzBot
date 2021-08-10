import discord
import random
import asyncio
from replit import db

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
    value="Show this message",
  )
  embed.add_field(
    name="`/hello`",
    value="Say hi!",
  )
  embed.add_field(
    name="`/isLive streamer_name`",
    value="check if a certain streamer is live!",
  )
  embed.add_field(
    name="`/setupChannel`",
    value="change my default channel",
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
    name="`/balance`",
    value=f"check how many {Constants.PIFLOUZ_EMOJI} you have. Kind of a low-cost Piflex",
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
    name="`duel [accept|deny|challenge|cancel|play]`",
    value="earn piflouz by winning challenges against others",
  )
  embed.add_field(
    name="`/ranking`",
    value="check how worthy you are",
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


async def get_embed_piflouz(bot):
    """
  Creates an embed message containing the explanation for the piflouz game and the balance
  --
  input:
    bot: discord.ext.commands.Bot
  --
  output:
    embed: discord.Embed -> the message
  """
    embed = discord.Embed(
      title=f"Come get some {Constants.PIFLOUZ_EMOJI}!",
      description=Constants.BASE_PIFLOUZ_MESSAGE,
      colour=discord.Colour.gold()
    )
    # Piflouz thumbnail
    embed.set_thumbnail(url=Constants.PIFLOUZ_URL)

    # Rankings
    if "piflouz_bank" in db.keys():
        d_piflouz = dict(db["piflouz_bank"])
        d_piflex = [(user_id, len(discovered)) for user_id, discovered in db["discovered_piflex"].items()]

        sorted_balance = sorted(list(d_piflouz.items()), key=lambda key_val: -int(key_val[1]))
        sorted_piflex_discovery = sorted(d_piflex, key=lambda key_val: -int(key_val[1]))

        async def get_str(i, L):
          user_id, value = L[i]
          return f"{i + 1}: <@{user_id}> - {value}\n"
        
        tasks_balance_ranking = [get_str(i, sorted_balance) for i in range(min(len(sorted_balance), 10))]
        tasks_discovery_ranking = [get_str(i, sorted_piflex_discovery) for i in range(min(len(sorted_piflex_discovery), 10))]

        res = await asyncio.gather(*tasks_balance_ranking)
        ranking = "".join(res)
        if ranking != "":
          embed.add_field(name="Balance", value=ranking, inline=True)

        res = await asyncio.gather(*tasks_discovery_ranking)
        ranking = "".join(res)
        if ranking != "":
          embed.add_field(name="Piflex Discovery", value=ranking, inline=True)

    return embed


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
