import asyncio
import datetime
from dateutil.relativedelta import relativedelta
from interactions import IntervalTrigger
import logging
from math import sqrt

from constant import Constants
from custom_task_triggers import TaskCustom as Task
from database import db
import duels
import embed_messages
import events
import pibox
from piflouz_generated import reset_stats
import piflouz_handlers
import user_profile
import utils


logger = logging.getLogger("custom_log")

waiting_for_season = asyncio.Lock()  # To avoid multiple seasons starting at the same time

reward_balance = lambda balance: int(sqrt(balance))
reward_piflex = lambda count: int(0.5771 * count ** 3 - 9.8453 * count ** 2 + 80.152 * count)
bonus_ranking = [100, 50, 30]


async def start_new_season(bot):
    """
    Announces the beginning of a new season

    Parameters
    ----------
    bot (interactions.Client)

    Returns
    -------
    msg (interactions.Message):
        the message sent
    """
    if "out_channel" in db.keys():
        channel = await bot.fetch_channel(db["out_channel"])

        msg = await channel.send(components=embed_messages.get_container_piflouz())
        return msg


async def end_current_season(bot):
    """
    Announces the end of the current season and computes the amount of turbo piflouz earned

    Parameters
    ----------
    bot (interactions.Client)
    """
    # Ending current events to avoind passing piflouz from one season to the other with Raffle
    await events.end_event(bot, events.EventType.PASSIVE)
    await events.end_event(bot, events.EventType.CHALLENGE)

    # Reseting the previous stats for the season results
    profiles = user_profile.get_active_profiles()
    user_profile.reset_all("season_results")
    user_profile.reset_all_inactive("season_results")

    # Ending the ongoing duels and giving back the money
    all_duels = duels.get_all_duels()
    for duel in all_duels:
        piflouz_handlers.update_piflouz(duel["user_id1"], qty=duel["amount"], check_cooldown=False)
        if duel["accepted"]:
            piflouz_handlers.update_piflouz(duel["user_id2"], qty=duel["amount"], check_cooldown=False)

        thread = await bot.fetch_channel(duel["thread_id"])
        await thread.edit(archived=False, name="[Season over] " + thread.name)
        await thread.archive(reason="Season over")

    # Adding turbo piflouz based on the amount of piflouz collected
    bank = list(user_profile.get_inverted("piflouz_balance").items())
    reward_turbo_piflouz_based_on_scores(bank, reward_balance, "Balance")

    # Adding turbo piflouz based on the amount of piflex images discovered
    piflex_count = [(user_id, len(profile["discovered_piflex"])) for user_id, profile in profiles.items()]
    # so that there is at least an increase of 20 per image, and so that the whole 12 images give 550 turbo piflouz
    # the median of the required number of piflex is aroud 35, which lead to 35*8000 piflouz spent, which would lead to 530 turbo piflouz otherwhise
    reward_turbo_piflouz_based_on_scores(piflex_count, reward_piflex, "Discovered piflex")

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

    pibox.get_all_pibox().clear()
    duels.get_all_duels().clear()

    reset_stats()

    # Sending the announcement message
    if "out_channel" in db.keys():
        embed = await embed_messages.get_embed_end_season(bot)
        channel = await bot.fetch_channel(db["out_channel"])
        await channel.send(embed=embed)


@Task.create(IntervalTrigger(hours=24))
async def season_task(bot):
    """
    Starts and ends seasons

    Parameters
    ----------
    bot (interactions.Client)
    """
    global waiting_for_season

    if waiting_for_season.locked(): return

    await waiting_for_season.acquire()
    next_begin = get_season_end_datetime()
    await asyncio.sleep((next_begin - datetime.datetime.now(tz=next_begin.tzinfo)).total_seconds())

    if "current_season_message_id" in db.keys() and "out_channel" in db.keys():
        logger.info("Ending current season")
        await end_current_season(bot)
        channel = await bot.fetch_channel(db["out_channel"])
        old_message = await channel.fetch_message(db["current_season_message_id"])
        await old_message.unpin()
        logger.info("Season ended")

    logger.info("Starting new season")
    db["last_begin_time"] = int(next_begin.timestamp())
    msg = await start_new_season(bot)
    await msg.pin()
    db["current_season_message_id"] = int(msg.id)
    db["piflouz_message_id"] = int(msg.id)
    await utils.update_piflouz_message(bot)

    waiting_for_season.release()
    logger.info("Season started")


def reward_turbo_piflouz_based_on_ranking(scores, rewards, reward_type):
    """
    Give user rewards based on a given ranking

    Parameters
    ----------
    scores (List[)
    rewards (List[int]):
        bonus score for the users ranked less than len(rewards)
    reward_type (str)
    """
    sorted_scores = sorted(scores, key=lambda key_val: -key_val[1])  # Sorting by decreasing score

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

    Parameters
    ----------
    scores ()
    reward (int):
        int function -> transform the score into the rewarded turbo piflouz amount
    reward_type (str)
    """
    for user_id, score in scores:
        turbo_balance = reward(score)

        profile = user_profile.get_profile(user_id)

        profile["season_results"][reward_type] = turbo_balance
        profile["turbo_piflouz_balance"] += turbo_balance


def get_season_end_datetime():
    """
    Returns the datetime corresponding to the current season end

    Returns
    -------
    res (datetime.datetime)
    """
    last_begin_time = datetime.datetime.fromtimestamp(db["last_begin_time"], tz=Constants.TIMEZONE)
    next_begin = (last_begin_time + relativedelta(months=3))

    # We need to account for winter/summer time changes
    # We can't localize an already localized datetime, so we first go back to UTC and then localize it again
    next_begin = Constants.TIMEZONE.localize(next_begin.replace(tzinfo=None))
    return next_begin


def get_season_end_timestamp():
    """
    Returns the timestamp corresponding to the current season end

    Returns
    -------
    res (int)
    """
    next_begin = get_season_end_datetime()
    return int(next_begin.timestamp())


def get_season_end_date():
    """
    Returns the date corresponding to the current season end

    Returns
    -------
    res (datetime.date)
    """
    next_begin = get_season_end_datetime()
    return next_begin.date()
