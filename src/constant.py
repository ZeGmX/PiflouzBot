import datetime  # Useful for an eval  # noqa: F401
from dotenv import load_dotenv
from interactions import OrTrigger, TimeTrigger
import os
from pytz import timezone

from chess_utils import load_chess_database


load_dotenv()


class Constants:
    ### Login information
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    TWITCH_ID = os.getenv("TWITCH_ID")
    TWITCH_SECRET = os.getenv("TWITCH_SECRET")
    REDDIT_ID = os.getenv("REDDIT_ID")
    REDDIT_SECRET = os.getenv("REDDIT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
    IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

    ### Role ids
    TWITCH_NOTIF_ROLE_ID = int(os.getenv("TWITCH_NOTIF_ROLE_ID"))
    PILORD_ROLE_ID = int(os.getenv("PILORD_ROLE_ID"))
    PIFLEXER_ROLE_ID = int(os.getenv("PIFLEXER_ROLE_ID"))
    MEGA_PIFLEXER_ROLE_ID = int(os.getenv("MEGA_PIFLEXER_ROLE_ID"))
    PIBOX_MASTER_ID = int(os.getenv("PIBOX_MASTER_ID"))  # Not actually a discord role
    CHAOS_ROLE_ID = int(os.getenv("CHAOS_ROLE_ID"))
    PIFLEX_MASTER_ROLE_ID = int(os.getenv("PIFLEX_MASTER_ROLE_ID"))
    PIBOX_NOTIF_ROLE_ID = int(os.getenv("PIBOX_NOTIF_ROLE_ID"))
    BIRTHDAY_NOTIF_ROLE_ID = int(os.getenv("BIRTHDAY_NOTIF_ROLE_ID"))

    ### Emojis
    PIFLOUZ_EMOJI_ID = int(os.getenv("PIFLOUZ_EMOJI_ID"))
    PIFLOUZ_EMOJI = f"<:piflouz:{PIFLOUZ_EMOJI_ID}>"
    FUEGO_EMOJI_ID = int(os.getenv("FUEGO_EMOJI_ID"))
    FUEGO_EMOJI = f"<:fuego:{FUEGO_EMOJI_ID}>"
    EMOJI_IDS_FOR_PIBOX = eval(os.getenv("EMOJI_IDS_FOR_PIBOX"))
    EMOJI_NAMES_FOR_PIBOX = eval(os.getenv("EMOJI_NAMES_FOR_PIBOX"))
    TURBO_PIFLOUZ_ANIMATED_EMOJI_ID = int(os.getenv("TURBO_PIFLOUZ_ANIMATED_EMOJI_ID"))
    TURBO_PIFLOUZ_ANIMATED_EMOJI = f"<a:turbo_piflouz:{TURBO_PIFLOUZ_ANIMATED_EMOJI_ID}>"
    BIRTHDAY_EMOJI_ID = int(os.getenv("BIRTHDAY_EMOJI_ID"))
    BIRTHDAY_EMOJI = f"<:pibou4Birthday:{BIRTHDAY_EMOJI_ID}>"
    PIKADAB_EMOJI_ID = int(os.getenv("PIKADAB_EMOJI_ID"))
    PIKADAB_EMOJI = f"<:pikadab:{PIKADAB_EMOJI_ID}>"

    ### Image URLs
    PIFLOUZ_URL = os.getenv("PIFLOUZ_URL")
    PIBOU4LOVE_URL = os.getenv("PIBOU4LOVE_URL")
    PIBOU4STONKS_URL = os.getenv("PIBOU4STONKS_URL")
    PIBOU_TWITCH_THUMBNAIL_URL = os.getenv("PIBOU_TWITCH_THUMBNAIL_URL")
    PIFLEX_IMAGES_URL = eval(os.getenv("PIFLEX_IMAGES_URL"))
    TURBO_PIFLOUZ_ANIMATED_URL = os.getenv("TURBO_PIFLOUZ_ANIMATED_URL")
    PIBOU4BIRTHDAY_URL = os.getenv("PIBOU4BIRTHDAY_URL")
    HALLOWEEN_PIFLOUZ_URL = os.getenv("HALLOWEEN_PIFLOUZ_URL")

    ### Dates and durations
    REACT_TIME_INTERVAL = int(os.getenv("REACT_TIME_INTERVAL"))  # How many seconds between each react to earn piflouz
    TWITCH_ANNOUNCEMENT_DELAY = int(os.getenv("TWITCH_ANNOUNCEMENT_DELAY"))  # Time between announcement of streams, to avoid spam if the stream crashes.
    PIFLEX_ROLE_DURATION = int(os.getenv("PIFLEX_ROLE_DURATION"))
    MEGA_PIFLEXER_ROLE_DURATION = int(os.getenv("MEGA_PIFLEXER_ROLE_DURATION"))
    EVENT_TIME = eval(os.getenv("EVENT_TIME"))
    OTTER_IMAGE_TIME = eval(os.getenv("OTTER_IMAGE_TIME"))
    SHUFFLE_NAME_TIME = eval(os.getenv("SHUFFLE_NAME_TIME"))
    BIRTHDAY_CHECK_TIME = eval(os.getenv("BIRTHDAY_CHECK_TIME"))
    EVERY_HOUR_TRIGGER = OrTrigger(*[TimeTrigger(hour=i) for i in range(24)])
    TIMEZONE = timezone(os.getenv("TIMEZONE"))
    BOT_BIRTHDAY = os.getenv("BOT_BIRTHDAY")

    ### Costs
    PIFLEX_COST = int(os.getenv("PIFLEX_COST"))
    PIFLEXER_COST = int(os.getenv("PIFLEXER_COST"))

    ### Stat config
    MAX_PIBOX_AMOUNT = int(os.getenv("MAX_PIBOX_AMOUNT"))
    DONATE_TAX_RATIO = eval(os.getenv("DONATE_TAX_RATIO"))
    DUEL_TAX_RATIO = int(os.getenv("DUEL_TAX_RATIO"))
    MAX_MINING_COMBO = int(os.getenv("MAX_MINING_COMBO"))
    BASE_PIFLOUZ_PER_MINING_COMBO = int(os.getenv("BASE_PIFLOUZ_PER_MINING_COMBO"))
    BASE_MINING_AMOUNT = int(os.getenv("BASE_MINING_AMOUNT"))
    MAX_MINING_ACCURACY_BONUS = int(os.getenv("MAX_MINING_ACCURACY_BONUS"))
    DAILY_BONUS_REWARD = int(os.getenv("DAILY_BONUS_REWARD"))
    DAILY_BONUS_MAX_STREAK = int(os.getenv("DAILY_BONUS_MAX_STREAK"))
    HAUNTED_PIBOX_STEAL_PROBA = eval(os.getenv("HAUNTED_PIBOX_STEAL_PROBA"))
    MAX_RAFFLE_PIBOX_AMOUNT = int(os.getenv("MAX_RAFFLE_PIBOX_AMOUNT"))
    MULTI_CLAIM_PIBOX_NB_REWARD = int(os.getenv("MULTI_CLAIM_PIBOX_NB_REWARD"))

    ### Misc
    GUILD_IDS = eval(os.getenv("GUILD_IDS"))
    POWERUPS_STORE = None  # Set in load()
    RANDOM_EVENTS_PASSIVE = None  # Set in load()
    RANDOM_EVENTS_CHALLENGE = None  # Set in load()
    PIBOX_POOL_TABLE = None  # Set in load()
    GREETINGS = [
        "Greetings {}! Nice to meet you!",
                  "Hello there {}, how are you doing today?",
                  "Hello, oh great {}. Hope you are doing great!",
                  "Oh, I didn't see you there {}. Hello!",
                  "Hello {}! How are you today?",
                  "Greetings {}, I hope you have a great day today"
    ]
    STREAMERS = eval(os.getenv("STREAMERS"))
    CHESS_DATABASE_MAPPING = load_chess_database("chess_database/")

    @staticmethod
    def load():
        import events  # noqa: F401
        import pibox  # noqa: F401
        import powerups  # noqa: F401
        from random_pool import RandomPool, RandomPoolTable

        Constants.POWERUPS_STORE = eval(os.getenv("POWERUPS_STORE"))
        Constants.RANDOM_EVENTS_PASSIVE = RandomPool.from_dict(eval(os.getenv("RANDOM_EVENTS_PASSIVE")))
        Constants.RANDOM_EVENTS_CHALLENGE = RandomPool.from_dict(eval(os.getenv("RANDOM_EVENTS_CHALLENGE")))
        Constants.PIBOX_POOL_TABLE = RandomPoolTable.from_dict(eval(os.getenv("PIBOX_POOL_TABLE")))
