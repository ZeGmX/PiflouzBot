import asyncio
from interactions import IntervalTrigger
import time

from constant import Constants
from custom_task_triggers import TaskCustom as Task
from database import db
import user_profile


@Task.create(IntervalTrigger(seconds=30))
async def update_ranks(bot):
    """
    Updates the different ranks

    Parameters
    ----------
    bot (interactions.Client)
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

    Parameters
    ----------
    bot (interactions.Client)
    """
    if len(user_profile.get_active_profiles()) == 0:
        return

    guild = bot.guilds[0]
    role = Constants.PILORD_ROLE_ID

    data = sorted(list(user_profile.get_inverted("piflouz_balance").items()), key=lambda key_val: -int(key_val[1]))
    # in case of ties
    data = list(filter(lambda key_val: key_val[1] == data[0][1], data))
    user_ids = [key_val[0] for key_val in data]

    # Remove old pilords
    for user_id in db["current_pilords"]:
        if user_id not in user_ids:
            member = await guild.fetch_member(int(user_id))
            await member.remove_role(role)

    # Avoid creating pilords if there is no piflouz
    if len(data) == 0 or data[0][1] <= 0:
        if len(db["current_pilords"]) == 0:
            return
        else:
            for user_id in db["current_pilords"]:
                member = await guild.fetch_member(int(user_id))
                await member.remove_role(role)
            db["current_pilords"] = []
            return

    # Setup new pilords
    for user_id, amount in data:
        if user_id not in db["current_pilords"]:
            member = await guild.fetch_member(int(user_id))
            await member.add_role(role)
            bot.dispatch("become_pilord", user_id)

    db["current_pilords"] = user_ids


async def update_rank_mega_piflexer(bot):
    """
    Removes the mega-piflexer roles when they need to be

    Parameters
    ----------
    bot (interactions.Client)
    """
    if "mega_piflexers" not in db.keys():
        return

    t = time.time()
    guild = bot.guilds[0]
    role = Constants.MEGA_PIFLEXER_ROLE_ID

    for id, old_time in list(db["mega_piflexers"].items()):
        if t - old_time >= Constants.MEGA_PIFLEXER_ROLE_DURATION:
            member = await guild.fetch_member(int(id))
            await member.remove_role(role)
            del db["mega_piflexers"][id]


async def update_rank_piflexer(bot):
    """
    Removes the piflexer roles when they need to be

    Parameters
    ----------
    bot (interactions.Client)
    """
    if "piflexers" not in db.keys():
        return

    t = time.time()

    guild = bot.guilds[0]
    role = Constants.PIFLEXER_ROLE_ID

    for id, old_time in list(db["piflexers"].items()):
        if t - old_time >= Constants.PIFLEX_ROLE_DURATION:
            member = await guild.fetch_member(int(id))
            await member.remove_role(role)
            del db["piflexers"][id]


async def update_rank_piflex_master(bot):
    """
    Changes the rank of the players with the most discovered piflex images

    Parameters
    ----------
    bot (interactions.Client)
    """
    guild = bot.guilds[0]
    role = Constants.PIFLEX_MASTER_ROLE_ID

    data = sorted(list(user_profile.get_inverted("discovered_piflex").items()), key=lambda key_val: -len(key_val[1]))

    # in case of ties
    data = list(filter(lambda key_val: len(key_val[1]) == len(data[0][1]), data))
    user_ids = [key_val[0] for key_val in data]

    # Remove old piflex masters
    for user_id in db["current_piflex_masters"]:
        if user_id not in user_ids:
            member = await guild.fetch_member(int(user_id))
            await member.remove_role(role)

    # Avoid creating piflex masters if there is no piflex
    if len(data) == 0 or len(data[0][1]) == 0:
        if len(db["current_piflex_masters"]) == 0:
            return
        else:
            for user_id in db["current_piflex_masters"]:
                member = await guild.fetch_member(int(user_id))
                await member.remove_role(role)
            db["current_piflex_masters"] = []
            return

    # Setup new piflex masters
    for user_id, amount in data:
        if user_id not in db["current_piflex_masters"]:
            user = await guild.fetch_member(int(user_id))
            await user.add_role(role)

    db["current_piflex_masters"] = user_ids
