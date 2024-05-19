from constant import Constants
from my_database import db


class Piflouz_source:
    """Enum to represent the source of generated powerups"""
    GET = 1
    EVENT = 2
    PIBOX = 3
    MINER = 4


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
        case Piflouz_source.GET:
            stats["get"] += qty
        case Piflouz_source.EVENT:
            stats["event"] += qty
        case Piflouz_source.PIBOX:
            stats["pibox"] += qty
        case Piflouz_source.MINER:
            stats["miner"] += qty


def reset_stats():
    """
    Resets the stats of generated piflouz
    """
    db["piflouz_generated"] = {
        "get": 0,
        "event": 0,
        "pibox": 0,
        "miner": 0
    }


def get_stat_str():
    """
    Returns a string representing the stats of generated piflouz this season
    --
    output:
        stats: str
    """
    p_get, p_event, p_pibox, p_miner = db["piflouz_generated"]["get"], db["piflouz_generated"]["event"], db["piflouz_generated"]["pibox"], db["piflouz_generated"]["miner"]
    p_tot = p_get + p_event + p_pibox + p_miner
    stats = f"This season, I generated a total of {p_tot} {Constants.PIFLOUZ_EMOJI}:\n- {p_get} from `/get` commands\n- {p_event} from events\n- {p_pibox} from piboxes\n- {p_miner} from miner powerups"
    return stats
        