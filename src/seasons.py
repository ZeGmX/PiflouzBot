from math import sqrt
import datetime
from dateutil.relativedelta import relativedelta
from interactions import Button, ButtonStyle, IntervalTrigger
import asyncio

from cogs import Cog_piflouz_mining
from constant import Constants
from custom_task_triggers import TaskCustom as Task, TimeTriggerDT
import embed_messages
from my_database import db
import piflouz_handlers
import user_profile
import utils


async def start_new_season(bot):
    """
    Announces the beginning of a new season
    --
    input:
        bot: interactions.Client
    --
    output:
        msg: interactions.Message -> the message sent
    """
    if "out_channel" in db.keys():
        channel = await bot.fetch_channel(db["out_channel"])

        piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id=Cog_piflouz_mining.BUTTON_NAME, emoji=Constants.PIFLOUZ_EMOJI)

        msg = await channel.send(embed=embed_messages.get_embed_piflouz(), components=piflouz_button)
        return msg


async def end_current_season(bot):
    """
    Announces the end of the current season and computes the amount of turbo piflouz earned
    --
    input:
        bot: interactions.Client
    """
    # Reseting the previous stats for the season results
    profiles = user_profile.get_active_profiles()
    for profile in profiles.values():
        profile["season_results"] = dict()
    
    # Ending the ongoing duels and giving back the money
    for duel in db["duels"]:
        piflouz_handlers.update_piflouz(duel["user_id1"], qty=duel["amount"], check_cooldown=False)
        if duel["accepted"]:
            piflouz_handlers.update_piflouz(duel["user_id2"], qty=duel["amount"], check_cooldown=False)
        
        thread = await bot.fetch_channel(duel["thread_id"])
        await thread.edit(archived=False, name="[Season over] " + thread.name)
        await thread.archive(reason="Season over")

    # Adding turbo piflouz based on the amount of piflouz collected
    bank = list(user_profile.get_inverted("piflouz_balance").items())
    reward_balance = lambda balance: int(sqrt(balance))
    reward_turbo_piflouz_based_on_scores(bank, reward_balance, "Balance")
    
    # Adding turbo piflouz based on the amount of piflex images discovered
    piflex_count = [(user_id, len(profile["discovered_piflex"])) for user_id, profile in profiles.items()]
    reward_piflex = lambda count: int(0.5771 * count ** 3 - 9.8453 * count ** 2 + 80.152 * count)
    # so that there is at least an increase of 20 per image, and so that the whole 12 images give 550 turbo piflouz
    # the median of the required number of piflex is aroud 35, which lead to 35*8000 piflouz spent, which would lead to 530 turbo piflouz otherwhise
    reward_turbo_piflouz_based_on_scores(piflex_count, reward_piflex, "Discovered piflex")

    bonus_ranking = [100, 50, 30]
    
    # Adding piflouz based on the ranking in piflouz
    reward_turbo_piflouz_based_on_ranking(bank, bonus_ranking, "Balance ranking")
    
    # Adding piflouz based on the ranking in piflex
    reward_turbo_piflouz_based_on_ranking(piflex_count, bonus_ranking, "Piflex ranking")
    
    # Adding piflouz based on the ranking in donations
    donations = list(user_profile.get_inverted("donation_balance").items())
    reward_turbo_piflouz_based_on_ranking(donations, bonus_ranking, "Donation ranking")

    await utils.update_piflouz_message(bot)

    # Reseting the database
    user_profile.reset_all("piflouz_balance")
    user_profile.reset_all("discovered_piflex")
    user_profile.reset_all("donation_balance")
    user_profile.reset_all("powerups")
    user_profile.reset_all("previous_get_time")  # So that the combo is set to 0 for the next /get
    user_profile.reset_all("mining_combo")

    user_profile.set_all_inactive()

    db["random_gifts"] = {}
    db["duels"] = []
    
    for key in db["piflouz_generated"].keys():
        db["piflouz_generated"][key] = 0

    # Sending the announcement message
    if "out_channel" in db.keys():
        embed = await embed_messages.get_embed_end_season(bot)
        channel = await bot.fetch_channel(db["out_channel"])
        await channel.send(embed=embed)
    

@Task.create(IntervalTrigger(hours=24))
async def season_task(bot):
    """
    Starts and ends seasons
    --
    input:
        bot: interactions.Client
    """
    last_begin_time = datetime.datetime.fromtimestamp(db["last_begin_time"])
    next_begin = last_begin_time + relativedelta(months=3)
    await asyncio.sleep((next_begin - datetime.datetime.now()).total_seconds())

    if "current_season_message_id" in db.keys() and "out_channel" in db.keys():
        await end_current_season(bot)
        channel = await bot.fetch_channel(db["out_channel"])
        old_message = await channel.fetch_message(db["current_season_message_id"])
        await old_message.unpin()
    
    db["last_begin_time"] = int(next_begin.timestamp())
    msg = await start_new_season(bot)
    await msg.pin()
    db["current_season_message_id"] = int(msg.id)
    db["piflouz_message_id"] = int(msg.id)
    

def reward_turbo_piflouz_based_on_ranking(scores, rewards, reward_type):
    """
    Give user rewards based on a given ranking
    --
    input:
        scores: (str, int) list -> the score (int) for a given user given their id (str)
        rewards: int list -> bonus score for the users ranked less than len(rewards)
        reward_type: str
    """
    sorted_scores = sorted(scores, key=lambda key_val: -key_val[1]) # Sorting by decreasing score

    previous_index, previous_val = 0, 0
    for i, (user_id, score) in enumerate(sorted_scores):
        index = i if score != previous_val else previous_index
        previous_val, previous_index = score, index

        if index < len(rewards):
            profile = user_profile.get_profile(user_id)
            profile["turbo_piflouz_balance"] += rewards[index]
            profile["season_results"][reward_type] = [rewards[index], index]
        else:  # The user has a ranking too low to earn rewards
            break


def reward_turbo_piflouz_based_on_scores(scores, reward, reward_type):
    """
    Give user rewards based on a given score
    --
    input:
        scores: (str, int) list -> the score (int) for a given user given their id (str)
        reward: int -> int function -> transform the score into the rewarded turbo piflouz amount
        reward_type: str
    """
    for user_id, score in scores:
        turbo_balance = reward(score)

        profile = user_profile.get_profile(user_id)
        
        profile["season_results"][reward_type] = turbo_balance
        profile["turbo_piflouz_balance"] += turbo_balance