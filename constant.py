import os
import datetime # Useful for an eval

class Constants:
  # How many seconds between each react to earn piflouz
  REACT_TIME_INTERVAL = int(os.getenv("REACT_TIME_INTERVAL"))
  NB_PIFLOUZ_PER_REACT = int(os.getenv("NB_PIFLOUZ_PER_REACT"))

  #Miscelaneous timing things
  TIME_BEFORE_DELETION = int(os.getenv("TIME_BEFORE_DELETION"))


  # Rate of random drop (pibox)
  RANDOM_DROP_RATE = eval(os.getenv("RANDOM_DROP_RATE"))
  RANDOM_DROP_AVERAGE = NB_PIFLOUZ_PER_REACT * 10

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

  POWERUP_MULTIPLIER_TIME = int(os.getenv("POWERUP_MULTIPLIER_TIME"))
  POWERUP_MULTIPLIER_EFFECT1 = int(os.getenv("POWERUP_MULTIPLIER_EFFECT1"))
  POWERUP_MULTIPLIER_EFFECT2 = int(os.getenv("POWERUP_MULTIPLIER_EFFECT2"))
  POWERUP_MULTIPLIER_PRICE1 = int(os.getenv("POWERUP_MULTIPLIER_PRICE1"))
  POWERUP_MULTIPLIER_PRICE2 = int(os.getenv("POWERUP_MULTIPLIER_PRICE2"))
  POWERUP_COOLDOWN_TIME = int(os.getenv("POWERUP_COOLDOWN_TIME"))
  POWERUP_COOLDOWN_EFFECT1 = int(os.getenv("POWERUP_COOLDOWN_EFFECT1"))
  POWERUP_COOLDOWN_EFFECT2 = int(os.getenv("POWERUP_COOLDOWN_EFFECT2"))
  POWERUP_COOLDOWN_PRICE1 = int(os.getenv("POWERUP_COOLDOWN_PRICE1"))
  POWERUP_COOLDOWN_PRICE2 = int(os.getenv("POWERUP_COOLDOWN_PRICE2"))
  POWERUP_MINER_LIMIT = int(os.getenv("POWERUP_MINER_LIMIT"))
  POWERUP_MINER_PIFLOUZ = int(os.getenv("POWERUP_MINER_PIFLOUZ"))
  POWERUP_MINER_PRICE = int(os.getenv("POWERUP_MINER_PRICE"))

  PIBOX_MASTER_ID = int(os.getenv("PIBOX_MASTER_ID"))


  BASE_PIFLOUZ_MESSAGE = f"\nThis is the piflouz mining message, react every {REACT_TIME_INTERVAL} seconds to gain more {PIFLOUZ_EMOJI}\n\n\
  You just need to react with the {PIFLOUZ_EMOJI} emoji\n\
  If you waited long enough ({REACT_TIME_INTERVAL} seconds), you will earn {NB_PIFLOUZ_PER_REACT} {PIFLOUZ_EMOJI}!\n\
  A :white_check_mark: reaction will appear for 2 seconds to make you know you won\n\
  A :x: reaction will appear for 2s if you did not wait for long enough, better luck next time\n"

  RAFFLE_TICKET_PRICE = int(os.getenv("RAFFLE_TICKET_PRICE"))
  RAFFLE_TIME = eval(os.getenv("RAFFLE_TIME"))
  RAFFLE_TAX_RATIO = int(os.getenv("RAFFLE_TAX_RATIO"))

  greetings = [ "Greetings <@{}>! Nice to meet you!",
                "Hello there <@{}>, how are you doing today ?",
                "Hello, oh great <@{}>. Hope you are doing great"]
  
  streamers_to_check = eval(os.getenv("STREAMERS"))
  