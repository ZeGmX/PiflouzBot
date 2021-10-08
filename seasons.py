from discord.ext import tasks
from discord.utils import sleep_until
from math import sqrt
from replit import db
import datetime
from dateutil.relativedelta import relativedelta

from constant import Constants


async def start_new_season(bot, end_time):
  """
  Announces the beginning of a new season
  --
  input:
    bot: discord.ext.commands.Bot
    end_time: datetime.datetime -> the time at which the season ends
  --
  output:
    msg: discord.Message -> the message sent
  """
  if "out_channel" in db.keys():
    channel = bot.get_channel(db["out_channel"])
    msg = await channel.send(f"A new season begins! Your goal is to earn, donate and flex with as much piflouz as possible. You will earn rewards based on the amount of piflouz you earn and your different rankings. This season will end on <t:{int(end_time.timestamp())}>")
    return msg


async def end_current_season(bot):
  """
  Announces the end of the current season and computes the amount of turbo piflouz earned
  --
  input:
    bot: discord.ext.commands.Bot
  """
  bank = list(db["piflouz_bank"].items())

  # Adding turbo piflouz based on the amount of piflouz collected
  for user_id, balance in bank:
      turbo_balance = int(sqrt(balance))

      if user_id not in db["turbo_piflouz_bank"].keys():
        db["turbo_piflouz_bank"][user_id] = 0

      db["turbo_piflouz_bank"][user_id] += turbo_balance
  
  bonus_ranking = [100, 50, 30]

  # Adding piflouz based on the ranking in piflouz
  reward_turbo_piflouz_based_on_ranking(bank, bonus_ranking)

  # Adding piflouz based on the ranking in piflex
  piflex_count = [(user_id, len(discovered)) for user_id, discovered in db["discovered_piflex"].items()]
  reward_turbo_piflouz_based_on_ranking(piflex_count, bonus_ranking)

  # Adding piflouz based on the ranking in donations
  donations = list(db["donation_balance"].items())
  reward_turbo_piflouz_based_on_ranking(donations, bonus_ranking)

  # Reseting the database
  db["piflouz_bank"] = {}
  db["discovered_piflex"] = {}
  db["donation_balance"] = {}

  # Sending the announcement message
  if "out_channel" in db.keys():
    total_piflouz = sum(item[1] for item in bank)
    channel = bot.get_channel(db["out_channel"])
    await channel.send(f"The last season has ended! Use the `/seasonresults` to see what you earned. Congratulations to every participant, you generated a total of {total_piflouz} {Constants.PIFLOUZ_EMOJI} this season!")
  

@tasks.loop(hours=24)
async def season_task(bot):
  """
  Starts and ends seasons
  --
  input:
    bot: discord.ext.commands.Bot
  """
  last_begin_time = datetime.datetime.fromtimestamp(db["last_begin_time"])
  next_begin = last_begin_time + relativedelta(months=3)
  await sleep_until(next_begin)

  if "current_season_message_id" in db.keys() and "out_channel" in db.keys():
    await end_current_season(bot)
    old_message = await bot.get_channel(db["out_channel"]).fetch_message(db["current_season_message_id"])
    await old_message.unpin()
  
  msg = await start_new_season(bot, next_begin + relativedelta(months=3))
  await msg.pin()
  db["current_season_message_id"] = msg.id
  db["last_begin_time"] = int(next_begin.timestamp())


def reward_turbo_piflouz_based_on_ranking(scores, rewards):
  """
  Give user rewards based on a given ranking
  --
  input:
    scores: (str, int) list -> the score (int) for a given user given their id (str)
    rewards: int list -> bonus score for the users ranked less than len(rewards)
  """
  sorted_scores = sorted(scores, key=lambda key_val: -key_val[1]) # Sorting by decreasing score

  previous_index, previous_val = 0, 0
  for i, (user_id, score) in enumerate(sorted_scores):
    index = i if score != previous_val else previous_index
    previous_val, previous_index = score, index

    if index < len(rewards):
      db["turbo_piflouz_bank"][user_id] += rewards[index]
    else:  # The user has a ranking too low to earn rewards
      break