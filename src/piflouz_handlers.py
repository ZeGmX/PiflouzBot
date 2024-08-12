from datetime import datetime

from constant import Constants
import events
import powerups  # Used in eval()  # noqa: F401
import user_profile


def update_piflouz(user_id, qty=None, check_cooldown=True, current_time=None):
    """
    Does the generic piflouz mining, and returns wether it suceeded or not

    Parameters
    ----------
    user_id (int/str):
        id of the person who reacted
    qty (int):
        number of piflouz (not necesseraly positive)
    check_cooldown (boolean):
        if we need to check the cooldown (for the piflouz mining)

    Returns
    -------
    res (boolean):
        if the update succeded
    qty (int):
        the amount actually sent/received (only returned if check_cooldown = True (corresponding to a /get))
    """
    user_id = str(user_id)

    # New user
    profile = user_profile.get_profile(user_id)

    balance = profile["piflouz_balance"]

    if check_cooldown:  # corresponding to a /get
        assert current_time is not None, "Got current_time = None"

        cooldown = user_profile.get_timer(user_id, current_time)
        qty = get_total_piflouz_earned(user_id, current_time)
    else:
        assert qty is not None, "Got qty = None"

    if (not check_cooldown or cooldown == 0) and balance + qty >= 0:
        profile["piflouz_balance"] = balance + qty
        if check_cooldown:
            bonus = get_update_daily_bonus(user_id, current_time)
            profile["previous_get_time"] = current_time
            profile["piflouz_balance"] += bonus
            return True, qty + bonus
        return True

    if check_cooldown:
        return False, qty
    return False


def update_combo(user_id, current_time):
    """
    Updates the current combo of the user

    Parameters
    ----------
    user_id (int/str)
    current_time (int)
    """
    profile = user_profile.get_profile(user_id)
    cooldown = user_profile.get_total_cooldown(user_id)
    old_time = profile["previous_get_time"]

    if old_time + cooldown <= current_time < old_time + 2 * cooldown:
        profile["mining_combo"] += 1

    elif current_time >= old_time + 2 * cooldown:
        profile["mining_combo"] = 0


def get_mining_accuracy_bonus(user_id, current_time):
    """
    Returns the piflouz bonus earned from a /get depending on the user accuracy

    Parameters
    ----------
    user_id (str/int)
    current_time (int):
        the time at which the interaction was created

    Returns
    -------
    res (int)
    """
    user_id = str(user_id)
    profile = user_profile.get_profile(user_id)

    old_time = profile["previous_get_time"]
    diff = current_time - old_time

    cooldown = user_profile.get_total_cooldown(user_id)

    if diff < cooldown or diff > 2 * cooldown:
        return 0

    t = 1 - (diff - cooldown) / cooldown
    return round(t * Constants.MAX_MINING_ACCURACY_BONUS)


def get_max_rewardable_combo(user_id):
    """
    Returns the maximum rewardable combo for a given user

    Parameters
    ----------
    user_id (int/str)

    Returns
    -------
    res (int)
    """
    current_event = events.get_event_object(events.EventType.PASSIVE)
    profile = user_profile.get_profile(user_id)
    powerups_user = [eval(p) for p in profile["powerups"]]
    powerups_event = current_event.get_powerups() if current_event is not None else []
    all_powerups = powerups_user + powerups_event
    return round(Constants.MAX_MINING_COMBO + sum(p.get_max_combo_increase() for p in all_powerups))


def get_total_piflouz_earned(user_id, current_time):
    r"""
    Returns the amount earned with a /get, taking into account the user powerups, the current event, the user combo and the accuracy
    /!\ This does not take the daily bonus into account (we don't want to update the bonus when checking while on cooldown)

    Parameters
    ----------
    user_id (int/str)
    current_time (int):
        the time at which the interaction was created

    Returns
    -------
    qty (the pilouz amount)
    """
    profile = user_profile.get_profile(user_id)

    current_event = events.get_event_object(events.EventType.PASSIVE)
    powerups_user = [eval(p) for p in profile["powerups"]]
    powerups_event = current_event.get_powerups() if current_event is not None else []
    all_powerups = powerups_user + powerups_event

    qty = Constants.BASE_MINING_AMOUNT * (1 + sum(p.get_piflouz_multiplier_value() - 1 for p in all_powerups))
    qty = round(qty)

    max_combo = get_max_rewardable_combo(user_id)

    combo_bonus = min(profile["mining_combo"], max_combo) * Constants.BASE_PIFLOUZ_PER_MINING_COMBO * (1 + sum(p.get_combo_reward_multiplier() - 1 for p in all_powerups))
    combo_bonus = round(combo_bonus)

    return qty + combo_bonus + get_mining_accuracy_bonus(user_id, current_time)


def get_current_daily_bonus(user_id, current_time):
    """
    Returns the current daily bonus for a user, without modifying the bonus data

    Parameters
    ----------
    user_id (int/str)
    current_time (int)

    Returns
    -------
    res (int)
    """
    profile = user_profile.get_profile(user_id)

    d = datetime.fromtimestamp(current_time, tz=Constants.TIMEZONE).date()
    prev_date = datetime.strptime(profile["daily_bonus_date"], "%Y-%m-%d").date()

    if d != prev_date:
        return 0
    return profile["daily_bonus"]


def get_update_daily_bonus(user_id, current_time):
    """
    Returns the daily bonus for a user
    This also modifies the bonus data

    Parameters
    ----------
    user_id (int/str)
    current_time (int)

    Returns
    -------
    res (int)
    """
    profile = user_profile.get_profile(user_id)

    d = datetime.fromtimestamp(current_time, tz=Constants.TIMEZONE).date()
    prev_date = datetime.strptime(profile["daily_bonus_date"], "%Y-%m-%d").date()

    if d != prev_date:
        profile["daily_bonus"] = 1
        profile["daily_bonus_date"] = d.strftime("%Y-%m-%d")
        return Constants.DAILY_BONUS_REWARD
    if profile["daily_bonus"] < Constants.DAILY_BONUS_MAX_STREAK:
        profile["daily_bonus"] += 1
        return Constants.DAILY_BONUS_REWARD
    return 0
