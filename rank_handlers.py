from discord.ext import tasks
import time
from replit import db

from constant import Constants

@tasks.loop(seconds=30)
async def update_ranks(bot):
  """
  Updates the different ranks
  --
  input:
    bot: discord.ext.commands.Bot
  """
  await update_rank_pilord(bot)
  await update_rank_mega_piflexer(bot)
  await update_rank_piflexer(bot)

  
async def update_rank_pilord(bot):
  """
  Changes the rank of the players with the most piflouz
  --
  input:
    bot: discord.ext.commands.Bot
  """
  if "piflouz_bank" not in db.keys():
    return
  
  guild = bot.guilds[0]
  role = guild.get_role(Constants.PILORD_ROLE_ID)

  L = sorted(list(db["piflouz_bank"].items()), key=lambda key_val: -int(key_val[1]))
  # in case of ties
  L = list(filter(lambda key_val: key_val[1] == L[0][1], L))
  user_ids = [key_val[0] for key_val in L]

  if "current_pilords" in db.keys():
    # Remove old pilords
    for user_id in db["current_pilords"]:
      if user_id not in user_ids:
        member = await guild.fetch_member(user_id)
        await member.remove_roles(role)

    # Setup new pilords
    for user_id, amount in L:
      if user_id not in db["current_pilords"]:
        user = await guild.fetch_member(user_id)
        await user.add_roles(role)
    
    db["current_pilords"] = user_ids


async def update_rank_mega_piflexer(bot):
  """
  Removes the mega-piflexer roles when they need to be
  --
  input:
    bot: discord.ext.commands.Bot
  """
  if "mega_piflexers" not in db.keys():
    return
  
  t = time.time()
  role = bot.guilds[0].get_role(Constants.MEGA_PIFLEXER_ROLE_ID)
  for id, old_time in db["mega_piflexers"].items():
    if t - old_time >= Constants.MEGA_PIFLEXER_ROLE_DURATION:
      member = await bot.guilds[0].fetch_member(id)
      await member.remove_roles(role)
      del db["mega_piflexers"][id]


async def update_rank_piflexer(bot):
  """
  Removes the piflexer roles when they need to be
  --
  input:
    bot: discord.ext.commands.Bot
  """
  if "piflexers" not in db.keys():
    return
  
  t = time.time()
  role = bot.guilds[0].get_role(Constants.PIFLEXER_ROLE_ID)
  for id, old_time in db["piflexers"].items():
    if t - old_time >= Constants.PIFLEXROLE_DURATION:
      member = await bot.guilds[0].fetch_member(id)
      await member.remove_roles(role)
      del db["piflexers"][id]