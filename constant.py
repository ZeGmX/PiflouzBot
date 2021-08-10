import os
import datetime # Useful for an eval


class Constants:
  DISCORDTOKEN = os.getenv("DISCORDTOKEN")
  # How many seconds between each react to earn piflouz
  REACT_TIME_INTERVAL = int(os.getenv("REACT_TIME_INTERVAL"))
  NB_PIFLOUZ_PER_REACT = int(os.getenv("NB_PIFLOUZ_PER_REACT"))

  # Miscelaneous timing things
  TIME_BEFORE_DELETION = int(os.getenv("TIME_BEFORE_DELETION"))


  # Rate of random drop (pibox)
  PIBOX_DROP_RATE = eval(os.getenv("PIBOX_DROP_RATE"))
  MAX_PIBOX_AMOUNT = int(os.getenv("MAX_PIBOX_AMOUNT"))

  PIFLOUZ_EMOJI_ID = int(os.getenv("PIFLOUZ_EMOJI_ID"))
  PIFLOUZ_EMOJI = f"<:piflouz:{PIFLOUZ_EMOJI_ID}>"

  FUEGO_EMOJI_ID = int(os.getenv("FUEGO_EMOJI_ID"))
  FUEGO_EMOJI = f"<:fuego:{FUEGO_EMOJI_ID}>"
  PIFLOUZ_URL = os.getenv("PIFLOUZ_URL")

  PIBOU4LOVE_URL = os.getenv("PIBOU4LOVE_URL")
  PIBOU4STONKS_URL = os.getenv("PIBOU4STONKS_URL")

  PIBOU_TWITCH_THUMBNAIL_URL = os.getenv("PIBOU_TWITCH_THUMBNAIL_URL")

  TWITCH_ANNOUNCEMENTDELAY = int(os.getenv("TWITCH_ANNOUNCEMENTDELAY")) #Time between announcement of streams, to avoid spam if the stream crashes.

  TWITCH_NOTIF_ROLE_ID = int(os.getenv("TWITCH_NOTIF_ROLE_ID"))

  PIFLEX_COST = int(os.getenv("PIFLEX_COST"))

  PILORD_ROLE_ID = int(os.getenv("PILORD_ROLE_ID"))

  # Role that you can buy to flex
  PIFLEXER_ROLE_ID = int(os.getenv("PIFLEXER_ROLE_ID"))
  PIFLEXROLE_DURATION = int(os.getenv("PIFLEXROLE_DURATION"))
  PIFLEXER_COST = int(os.getenv("PIFLEXER_COST"))
  MEGA_PIFLEXER_ROLE_ID = int(os.getenv("MEGA_PIFLEXER_ROLE_ID"))
  MEGA_PIFLEXER_ROLE_DURATION = int(os.getenv("MEGA_PIFLEXER_ROLE_DURATION"))

  EMOJI_IDS_FOR_PIBOX = eval(os.getenv("EMOJI_IDS_FOR_PIBOX"))
  EMOJI_NAMES_FOR_PIBOX = eval(os.getenv("EMOJI_NAMES_FOR_PIBOX"))
  PIFLEX_IMAGES_URL = eval(os.getenv("PIFLEX_IMAGES_URL"))

  PIBOX_MASTER_ID = int(os.getenv("PIBOX_MASTER_ID"))

  GUILD_IDS = eval(os.getenv("GUILD_IDS"))
  DISCORD_BOT_ID = os.getenv("DISCORD_BOT_ID")

  EVENT_TIME = eval(os.getenv("EVENT_TIME"))
  DONATE_TAX_RATIO = eval(os.getenv("DONATE_TAX_RATIO"))
  REDDIT_ID = os.getenv("REDDIT_ID")
  REDDIT_SECRET = os.getenv("REDDIT_SECRET")
  REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
  OTTER_IMAGE_TIME = eval(os.getenv("OTTER_IMAGE_TIME"))
  PIFLEX_MASTER_ROLE_ID = int(os.getenv("PIFLEX_MASTER_ROLE_ID"))
  PIBOX_NOTIF_ROLE_ID = int(os.getenv("PIBOX_NOTIF_ROLE_ID"))

  TWITCHID = os.getenv("TWITCHID")
  TWITCHSECRET = os.getenv("TWITCHSECRET")

  DUEL_TAX_RATIO = int(os.getenv("DUEL_TAX_RATIO"))

  MAX_MINING_COMBO = int(os.getenv("MAX_MINING_COMBO"))
  PIFLOUZ_PER_MINING_COMBO = int(os.getenv("PIFLOUZ_PER_MINING_COMBO"))

  BASE_MINING_AMOUNT = int(os.getenv("BASE_MINING_AMOUNT"))
  MAX_MINING_ACCURACY_BONUS = int(os.getenv("MAX_MINING_ACCURACY_BONUS"))


  @staticmethod
  def load():
    import powerups
    import events
    import utils

    Constants.POWERUPS_STORE = eval(os.getenv("POWERUPS_STORE"))
    Constants.RANDOM_EVENTS = eval(os.getenv("RANDOM_EVENTS"))

    Constants.BASE_PIFLOUZ_MESSAGE = f"\nThis is the piflouz mining message, click every {Constants.REACT_TIME_INTERVAL} seconds to gain more {Constants.PIFLOUZ_EMOJI}\n\n\
You just need to click on the {Constants.PIFLOUZ_EMOJI} button below\n\
If you waited long enough ({utils.seconds_to_formatted_string(Constants.REACT_TIME_INTERVAL)}), you will earn some {Constants.PIFLOUZ_EMOJI}! The amount depends on the current event, you powerups, your mining combo and your accuracy to use /get"
 

  greetings = [ "Greetings {}! Nice to meet you!",
                "Hello there {}, how are you doing today ?",
                "Hello, oh great {}. Hope you are doing great"]
  
  streamers_to_check = eval(os.getenv("STREAMERS"))
  