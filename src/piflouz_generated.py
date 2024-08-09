from constant import Constants
from database import db


class PiflouzSource:
    """
    Enum to represent the source of generated powerups
    """

    GET = 1
    EVENT = 2
    PIBOX = 3
    MINER = 4
    ACHIEVEMENT = 5


def add_to_stat(qty, source):
    """
    Adds the given quantity to the corresponding source in the database.
    --
    input:
        qty: int
        source: int (Piflouz_source enum value)
    """
    stats = db["piflouz_generated"]
    match source:
        case PiflouzSource.GET:
            stats["get"] += qty
        case PiflouzSource.EVENT:
            stats["event"] += qty
        case PiflouzSource.PIBOX:
            stats["pibox"] += qty
        case PiflouzSource.MINER:
            stats["miner"] += qty
        case PiflouzSource.ACHIEVEMENT:
            stats["achievement"] += qty


def reset_stats():
    """
    Resets the stats of generated piflouz
    """
    db["piflouz_generated"] = {
        "get": 0,
        "event": 0,
        "pibox": 0,
        "miner": 0,
        "achievement": 0
    }


def get_stat_str():
    """
    Returns a string representing the stats of generated piflouz this season
    --
    output:
        stats: str
    """
    p_get, p_event, p_pibox, p_miner, p_achievements = db["piflouz_generated"]["get"], db["piflouz_generated"]["event"], db["piflouz_generated"]["pibox"], db["piflouz_generated"]["miner"], db["piflouz_generated"]["achievement"]
    p_tot = p_get + p_event + p_pibox + p_miner
    stats = f"This season, I generated a total of {p_tot} {Constants.PIFLOUZ_EMOJI}:\n- {p_get} from `/get` commands\n- {p_event} from events\n- {p_pibox} from piboxes\n- {p_miner} from miner powerups\n- {p_achievements} from achievements"
    return stats
