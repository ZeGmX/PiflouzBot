import discord
from replit import db

from constant import Constants


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
      name="`$?`",
      value="Show this message",
      inline=False
    )
    embed.add_field(
      name="`$hello`",
      value="Say hi!",
      inline=False
    )
    embed.add_field(
      name="`$isLive streamer_name`",
      value="check if a certain streamer is live!",
      inline=False
    )
    embed.add_field(
      name="`$shutdown`",
      value="if I start doing something nasty, or if you don't like me anymore :cry:",
      inline=False
    )
    embed.add_field(
      name="`$setupChannel`",
      value="change my default channel",
      inline=False
    )
    embed.add_field(
      name="`$joke`",
      value="to laugh your ass off (or not, manage your expectations)",
      inline=False
    )
    embed.add_field(
      name="`$donate @user amount`",
      value="be generous to others",
      inline=False
    )
    embed.add_field(
      name="`$balance`",
      value=f"check how many {Constants.PIFLOUZ_EMOJI} you have. Kind of a low-cost Piflex",
      inline=False
    )
    embed.add_field(
      name="`$cooldown`",
      value="'cause Pibou's next stream is neither too soon",
      inline=False
    )
    embed.add_field(
      name="`$get`",
      value="for the lazy ones",
      inline=False
    )
    
    embed.add_field(
      name="Things I do in the background",
      value=f"- I will send a message everytime the great streamer pibou421 goes live on Twitch\n\
- I can give you {Constants.PIFLOUZ_EMOJI} if you react to the message below\n\
- I spawn random gifts from time to time. Be the first to react to earn more {Constants.PIFLOUZ_EMOJI}"
    )
    return embed


async def get_embed_piflouz(client):
    """
  Creates an embed message containing the explanation for the piflouz game and the balance
  --
  input:
    client: discord.Client
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
    if "piflouz_bank" in db.keys():
        d_piflouz = dict(db["piflouz_bank"])
        ranking = ""
        # Generating the ranking string
        sorted_rank = sorted(list(d_piflouz.items()), key=lambda key_val: -int(key_val[1]))
        for i, (user_id, balance) in enumerate(sorted_rank):
            member = await client.guilds[0].fetch_member(user_id)  # nickname is relative to the guild
            ranking += f"{i + 1}: {member.display_name} - {balance}\n"

        embed.add_field(name="Balance", value=ranking, inline=False)

    return embed


def get_embed_twitch_notif():
    """
  Returns an embed message on which to react to get the role to get notified when pibou421 goes live on Twitch
  """
    embed = discord.Embed(
      title="Twitch notification role",
      description="React to get/remove the Twitch notifications role",
      colour=discord.Colour.purple()
    )
    embed.set_thumbnail(url=Constants.PIBOU_TWITCH_THUMBNAIL_URL)
    return embed
