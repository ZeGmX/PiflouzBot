from copy import copy
from itertools import chain

from constant import Constants
import events
from my_database import db
import powerups  # Used in eval()


def get_timer(user_id, current_time):
    """
    This function returns the amount of time needed before being able to earn more piflouz
    --
    input:
        user_id: int/str
    --
    output:
        time_needed: int -> time remaining before the end of cooldown
        current_time: int -> the time at which the interaction was created
    """
    user_id = str(user_id)
    profile = get_profile(user_id)

    old_time = profile["previous_get_time"]
    differential = current_time - old_time

    cooldown = get_total_cooldown(user_id)

    time_needed = max(0, cooldown - differential)

    return int(time_needed)


def get_total_cooldown(user_id):
    """
    Returns the time to wait between two /get, taking into account the user powerups and the current event
    --
    input:
        user_id: int/str - the id of the user having the powerups
    --
    output:
        cooldown: the time in seconds
    """
    user_id = str(user_id)
    profile = get_profile(user_id)

    current_event = events.get_event_object(events.Event_type.PASSIVE)
    powerups_user = [eval(p) for p in profile["powerups"]]
    powerups_event = current_event.get_powerups() if current_event is not None else []

    cooldown = Constants.REACT_TIME_INTERVAL * (1 + sum(p.get_cooldown_multiplier_value() - 1 for p in powerups_user + powerups_event))
    return cooldown


def get_new_user_profile():
    """
    Generates a new dict representing a blank user profile
    --
    output:
        profile: dict
    """
    return {
        "piflouz_balance": 0,
        "turbo_piflouz_balance": 0,
        "donation_balance": 0,
        "previous_get_time": 0,
        "mining_combo": 0,
        "discovered_piflex": [],
        "powerups": [],
        "achievements": [],
        "season_results": dict(),
        "daily_bonus": 0,
        "daily_bonus_date": "0001-01-01",
        "birthday_date": "0000-00-00",
    }


def get_profile(user_id):
    """
    Returns the profile of a user
    If the uses currently doesn't have a profile, it creates a new one
    --
    input:
        user_id: int/str
    --
    output:
        profile: dict (actually Element_dict)
    """
    user_id = str(user_id)
    if user_id in db["profiles"]["inactive"].keys():
        db["profiles"]["active"][user_id] = db["profiles"]["inactive"][user_id]
        del db["profiles"]["inactive"][user_id]

    elif user_id not in db["profiles"]["active"].keys():
        db["profiles"]["active"][user_id] = get_new_user_profile()
    
    return db["profiles"]["active"][user_id]


def get_inverted(key):
    """
    Returns a dictionary with the value associated to each user_id
    --
    input:
        key: str
    --
    output:
        dict
    """
    res = dict()
    for user_id, profile in db["profiles"]["active"].items():
        res[user_id] = profile[key]
    return res


def reset_all(key):
    """
    Resets the value associated to a key for all the active users
    --
    input:
        key: str
    """
    blank_profile = get_new_user_profile()
    default_value = blank_profile[key]
    for profile in db["profiles"]["active"].values():
        profile[key] = copy(default_value)


def reset_all_inactive(key):
    """
    Resets the value associated to a key for all the inactive users
    --
    input:
        key: str
    
    """
    blank_profile = get_new_user_profile()
    default_value = blank_profile[key]
    for profile in db["profiles"]["inactive"].values():
        profile[key] = copy(default_value)


def update_profiles():
    """
    Check if all profiles actually contain all the necessary keys
    """
    blank_profile = get_new_user_profile()
    for user_id, profile in chain(db["profiles"]["active"].items(), db["profiles"]["inactive"].items()):
        for key, value in blank_profile.items():
            if key not in profile.keys():
                profile[key] = copy(value)


def get_active_profiles():
    """
    Returns the active profiles
    --
    output:
        dict (Element_dict)
    """
    return db["profiles"]["active"]


def set_all_inactive():
    """
    Moves all profiles to the inactive profiles
    """
    for user_id, profile in db["profiles"]["active"].items():
        db["profiles"]["inactive"][user_id] = profile
    db["profiles"]["active"] = dict()