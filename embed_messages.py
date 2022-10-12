import random
from replit import db
import datetime
from dateutil.relativedelta import relativedelta
from interactions import Embed, EmbedImageStruct, EmbedField
from discord import Color

from constant import Constants
import socials
import utils


def get_embed_help_message():
  """
  Returns the embed message with help for every command
  --
  output:
    embed: interactions.Embed -> the embeded message
  """
  embed = Embed(
    title="Need help?",
    color=Color.red().value,
    thumbnail=EmbedImageStruct(url=Constants.PIBOU4LOVE_URL),
    fields=[
      EmbedField(
        name="`/help`",
        value="Show this message",
        inline=True
      ),
      EmbedField(
        name="`/hello`",
        value="Say hi!",
        inline=True
      ),
      EmbedField(
        name="`/is-live streamer_name`",
        value="Check if a certain streamer is live!",
        inline=True
      ),
      EmbedField(
        name="`/setup-channel [twitch|main]`",
        value="Change the channel where I send messages",
        inline=True
      ),
      EmbedField(
        name="`/joke`",
        value="To laugh your ass off (or not, manage your expectations)",
        inline=True
      ),
      EmbedField(
        name="`/donate @user amount`",
        value="Be generous to others",
        inline=True
      ),
      EmbedField(
        name="`/balance [@user]`",
        value=f"Check how many {Constants.PIFLOUZ_EMOJI} the user has",
        inline=True
      ),
      EmbedField(
        name="`/cooldown`",
        value="When your addiction is stronger than your sense of time",
        inline=True
      ),
      EmbedField(
        name="`/get`",
        value="For the lazy ones",
        inline=True
      ),
      EmbedField(
        name="`/piflex`",
        value=f"When you have too many {Constants.PIFLOUZ_EMOJI}\n ⚠️ Costs {Constants.PIFLEX_COST} {Constants.PIFLOUZ_EMOJI}",
        inline=True
      ),
      EmbedField(
        name="`/buy-rank-piflex`",
        value=f"Flex with a custom rank\n ⚠️ Costs {Constants.PIFLEXER_COST} {Constants.PIFLOUZ_EMOJI}, lasts for {utils.seconds_to_formatted_string(Constants.PIFLEX_ROLE_DURATION)}",
        inline=True
      ),
      EmbedField(
        name="`$tarpin`",
        value="What could that be? Can be used in any channel",
        inline=True
      ),
      EmbedField(
        name="`/pilord`",
        value="See how much you need to farm to flex with your rank",
        inline=True
      ),
      EmbedField(
        name="`/raffle n`",
        value="Buy raffle tickets to test your luck ⚠️ Only works during a raffle event ",
        inline=True
      ),
      EmbedField(
        name="`/store`",
        value="Buy fun upgrades",
        inline=True
      ),
      EmbedField(
        name="`/powerups`",
        value="See how powerful you are",
        inline=True
      ),
      EmbedField(
        name="`/giveaway n`",
        value="Drop a pibox with your own money",
        inline=True
      ),
      EmbedField(
        name="`/duel [challenge|play|status]`",
        value="Earn piflouz by winning challenges against others",
        inline=True
      ),
      EmbedField(
        name="`/ranking`",
        value="Check how worthy you are",
        inline=True
      ),
      EmbedField(
        name="`/role [get|remove]`",
        value="Get a specific notification role",
        inline=True
      ),
      EmbedField(
        name="`/season-result`",
        value="Check how good you were last season",
        inline=True
      ),
      EmbedField(
        name="`/achievements list`",
        value="Check what you need to do to get some achievements",
        inline=True
      ),
      EmbedField(
        name="`/wordle guess`",
        value="Try to solve today's wordle ⚠️ Only works during raffle events",
        inline=True
      ),
      EmbedField(
        name="`/wordle status`",
        value="Check how your wordle is going ⚠️ Only works during raffle events",
        inline=True
      ),
      EmbedField(
        name="`/birthday`",
        value="Check how your baking skills are going ⚠️ Only works during birthday events",
        inline=True
      ),
      EmbedField(
        name="`/wouldyourather`",
        value="Create a 'Would you rather?' poll",
        inline=True
      ),
      EmbedField(
        name="`/otter`",
        value="Finally something good in this world",
        inline=True
      ),
      EmbedField(
        name="Things I do in the background",
        value=f"- I will send a message everytime the greatest streamers go live on Twitch\n\
- I can give you {Constants.PIFLOUZ_EMOJI} if you click on the button below the piflouz message\n\
- I spawn random gifts from time to time. Be the first to react to earn more {Constants.PIFLOUZ_EMOJI}\n\
- I update the roles\n\
- I create events every day\n\
- I send a cute otter picture everyday",
    inline=False
      ),
    ]
  )

  return embed


def get_embed_piflouz(bot):
  """
  Creates an embed message containing the explanation for the piflouz game and the balance
  --
  input:
    bot: interactions.Client
  --
  output:
    embed: interactions.Embed
  """
  last_begin_time = datetime.datetime.fromtimestamp(db["last_begin_time"])
  end_time = last_begin_time + relativedelta(months=3)
  desc = f"This is the piflouz mining message, click every {Constants.REACT_TIME_INTERVAL} seconds to gain more {Constants.PIFLOUZ_EMOJI}.\n\n\
You just need to click on the {Constants.PIFLOUZ_EMOJI} button below or use the `/get` command.\n\
If you waited long enough ({utils.seconds_to_formatted_string(Constants.REACT_TIME_INTERVAL)}), you will earn some {Constants.PIFLOUZ_EMOJI}! The amount depends on the current event, your powerups, your mining combo and your accuracy to use `/get`.\n\n\
This season will end on <t:{int(end_time.timestamp())}>.\nYour goal is to earn, donate and flex with as much piflouz as possible. You will earn rewards based on the amount of piflouz you earn and your different rankings."

    # Rankings
  if "piflouz_bank" in db.keys():
    d_piflouz = dict(db["piflouz_bank"])
    d_piflex = [(user_id, len(discovered)) for user_id, discovered in db["discovered_piflex"].items() if len(discovered) > 0]
    d_donations = [(user_id, val) for user_id, val in db["donation_balance"].items() if val > 0]

    ranking_balance = get_ranking_str(list(d_piflouz.items()))
    ranking_piflex = get_ranking_str(d_piflex)
    ranking_donations = get_ranking_str(d_donations)

    embed = Embed(
    title=f"Come get some {Constants.PIFLOUZ_EMOJI}!",
    description=desc,
    thumbnail = EmbedImageStruct(url=Constants.PIFLOUZ_URL),
    color=Color.gold().value
  )
    
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
    embed: interactions.Embed
  """
  embed = Embed(
    title="Twitch notification role",
    description="React to get/remove the Twitch notifications role",
    color=Color.purple().value,
    thumbnail=EmbedImageStruct(url=Constants.PIBOU_TWITCH_THUMBNAIL_URL)
  )
  return embed


def get_embed_piflex(user):
  """
  Returns an embed message corresponding to the piflex message
  --
  input:
    user: user -> the user requesting the piflex
  --
  output:
    embed: interactions.Embed
    index: int -> index of the image/gif
  """
  index = random.randrange(0, len(Constants.PIFLEX_IMAGES_URL))
  image_url = Constants.PIFLEX_IMAGES_URL[index]
  
  embed = Embed(
    title="PIFLEX",
    description=f"Look how much piflouz {user.mention} has. So much piflouz that they are flexing on you poor peasants! They are so cool and rich that they can just take a bath in piflouz. You mad?",
    color=Color.gold().value,
    thumbnail=EmbedImageStruct(url=Constants.PIBOU4STONKS_URL),
    image=EmbedImageStruct(url=image_url)
  )
  
  print(f"Piflex with {image_url}")
  return embed, index


def get_embed_store_ui():
  """
  Returns an embed message corresponding to the store message
  --
  output:
    embed: interactions.Embed
  """
  embed = Embed(
    title="Piflouz shop",
    description="Here you can buy useful upgrades!",
    color=Color.dark_magenta().value,
  )
  
  for emoji, powerup in Constants.POWERUPS_STORE.items():
    embed.add_field(
      name=emoji,
      value=powerup.get_store_str(),
      inline=True
    )

  return embed


async def get_embed_otter(title="Otter image of the day!"):
  """
  Returns an embed corresponding to a random otter image
  --
  input:
    title: str -> title of the embed
  --
  output:
    embed: interactions.Embed
  """ 
  url = await socials.get_otter_image()

  embed = Embed(
    title=title,
    color=Color.from_rgb(101, 67, 33).value,  # brown
    image=EmbedImageStruct(url=url)
  )
  return embed


async def get_embed_end_season(bot):
  """
  Returns an embed announcing the end of a season
  --
  input:
    bot: interactions.Client
  --
  output:
    embed: interactions.Embed
  """
  channel = await bot.get_channel(db["out_channel"])
  msg = await channel.get_message(db["piflouz_message_id"])
  url = msg.url
  
  embed = Embed(
    title="The season is over!",
    description=f"The last season has ended! Use the `/season-results` to see what you earned. Congratulations to every participant!\nThe final rankings are available [here]({url})",
    color=Color.purple().value,
    thumbnail=EmbedImageStruct(url=Constants.TURBO_PIFLOUZ_ANIMATED_URL)
  )

  return embed


async def get_embed_end_raffle(bot, winner_id, prize):
  """
  Returns an embed announcing the end of a raffle
  --
  input:
    bot: interactions.Client
    winner_id: str/int
    prize: int
  --
  output:
    embed: interactions.Embed
  """
  channel = await bot.get_channel(db["out_channel"])
  msg = await channel.get_message(db["current_event_message_id"])
  url = msg.url
  
  embed = Embed(
    title="The raffle is over!",
    description=f"The raffle has ended! Congratulations to <@{winner_id}> for winning the raffle, earning {prize} {Constants.PIFLOUZ_EMOJI}!\nClick [here]({url}) to see the final participation.",
    color=Color.random().value,
    thumbnail=EmbedImageStruct(url=Constants.PIBOU4STONKS_URL)
  )

  return embed