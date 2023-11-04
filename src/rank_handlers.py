import time
from my_database import db
import asyncio
from discord.ext import tasks
from interactions import Role, Guild

from constant import Constants


@tasks.loop(seconds=30)
async def update_ranks(bot):
  """
  Updates the different ranks
  --
  input:
    bot: interactions.Client
  """
  await asyncio.gather(
     update_rank_pilord(bot),
     update_rank_mega_piflexer(bot),
     update_rank_piflexer(bot),
     update_rank_piflex_master(bot)
  )

  
async def update_rank_pilord(bot):
  """
  Changes the rank of the players with the most piflouz
  --
  input:
    bot: interactions.Client
  """
  if "piflouz_bank" not in db.keys():
    return

  guild = Guild(id=Constants.GUILD_IDS[0], _client=bot._http)
  role = Role(id=Constants.PILORD_ROLE_ID)

  L = sorted(list(db["piflouz_bank"].items()), key=lambda key_val: -int(key_val[1]))
  # in case of ties
  L = list(filter(lambda key_val: key_val[1] == L[0][1], L))
  user_ids = [key_val[0] for key_val in L]

  # Remove old pilords
  for user_id in db["current_pilords"]:
    if user_id not in user_ids:
      member = await guild.get_member(int(user_id))
      await member.remove_role(role, guild_id=guild.id)

  # Setup new pilords
  for user_id, amount in L:
    if user_id not in db["current_pilords"]:
      member = await guild.get_member(int(user_id))
      await member.add_role(role, guild_id=guild.id)
      bot.dispatch("become_pilord", user_id)
  
  db["current_pilords"] = user_ids


async def update_rank_mega_piflexer(bot):
  """
  Removes the mega-piflexer roles when they need to be
  --
  input:
    bot: interactions.Client
  """
  if "mega_piflexers" not in db.keys():
    return
  
  t = time.time()
  guild = Guild(id=Constants.GUILD_IDS[0], _client=bot._http)
  role = Role(id=Constants.MEGA_PIFLEXER_ROLE_ID)
  for id, old_time in db["mega_piflexers"].items():
    if t - old_time >= Constants.MEGA_PIFLEXER_ROLE_DURATION:
      member = await guild.get_member(int(id))
      await member.remove_role(role, guild_id=guild.id)
      del db["mega_piflexers"][id]


async def update_rank_piflexer(bot):
  """
  Removes the piflexer roles when they need to be
  --
  input:
    bot: interactions.Client
  """
  if "piflexers" not in db.keys():
    return
  
  t = time.time()

  guild = Guild(id=Constants.GUILD_IDS[0], _client=bot._http)
  role = Role(id=Constants.PIFLEXER_ROLE_ID)
  for id, old_time in db["piflexers"].items():
    if t - old_time >= Constants.PIFLEX_ROLE_DURATION:
      member = await guild.get_member(int(id))
      await member.remove_role(role, guild_id=guild.id)
      del db["piflexers"][id]


async def update_rank_piflex_master(bot):
  """
  Changes the rank of the players with the most discovered piflex images
  --
  input:
    bot: interactions.Client
  """
  guild = Guild(id=Constants.GUILD_IDS[0], _client=bot._http)
  role = Role(id=Constants.PIFLEX_MASTER_ROLE_ID)

  L = sorted(list(db["discovered_piflex"].items()), key=lambda key_val: -len(key_val[1]))

  # in case of ties
  L = list(filter(lambda key_val: len(key_val[1]) == len(L[0][1]), L))
  user_ids = [key_val[0] for key_val in L]

  # Remove old piflex masters
  for user_id in db["current_piflex_masters"]:
    if user_id not in user_ids:
      member = await guild.get_member(int(user_id))
      await member.remove_role(role, guild_id=guild.id)

  # Setup new piflex masters
  for user_id, amount in L:
    if user_id not in db["current_piflex_masters"]:
      user = await guild.get_member(int(user_id))
      await user.add_role(role, guild_id=guild.id)
  
  db["current_piflex_masters"] = user_ids