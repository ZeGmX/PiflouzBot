import os

class Constants:
  # How many seconds between each react to earn piflouz
  REACT_TIME_INTERVAL = int(os.getenv("REACT_TIME_INTERVAL"))
  NB_PIFLOUZ_PER_REACT = int(os.getenv("NB_PIFLOUZ_PER_REACT"))

  #Miscelaneous timing things
  TIME_BEFORE_DELETION = int(os.getenv("TIME_BEFORE_DELETION"))


  # Rate of random drop (pibox)
  RANDOM_DROP_RATE = 5 / 2880 # 2880 * 30s in a day, 5 mean drop a day 
  RANDOM_DROP_AVERAGE = NB_PIFLOUZ_PER_REACT * 10

  PIFLOUZ_EMOJI_ID = int(os.getenv("PIFLOUZ_EMOJI_ID"))
  PIFLOUZ_EMOJI = f"<:piflouz:{PIFLOUZ_EMOJI_ID}>"

  FUEGO_EMOJI_ID = int(os.getenv("FUEGO_EMOJI_ID"))
  FUEGO_EMOJI = f"<:fuego:{FUEGO_EMOJI_ID}>"
  PIFLOUZ_URL = os.getenv("PIFLOUZ_URL")

  EMOJI_DATABASE = [[FUEGO_EMOJI_ID, FUEGO_EMOJI], 
                    [PIFLOUZ_EMOJI_ID, PIFLOUZ_EMOJI]]

  PIBOU4LOVE_URL = os.getenv("PIBOU4LOVE_URL")
  PIBOU4STONKS_URL = os.getenv("PIBOU4STONKS_URL")

  PIBOU_TWITCH_THUMBNAIL_URL = os.getenv("PIBOU_TWITCH_THUMBNAIL_URL")

  TWITCH_ANNOUNCEMENTDELAY = int(os.getenv("TWITCH_ANNOUNCEMENTDELAY")) #Time between announcement of streams, to avoid spam if the stream crashes.

  TWITCH_NOTIF_ROLE_ID = int(os.getenv("TWITCH_NOTIF_ROLE_ID"))

  PIFLEX_COST = int(os.getenv("PIFLEX_COST"))


  PICSOU_URL = os.getenv("PICSOU_URL")

  PILORD_ROLE_ID = int(os.getenv("PILORD_ROLE_ID"))

  # Role that you can buy to flex
  PIFLEXER_ROLE_ID = int(os.getenv("PIFLEXER_ROLE_ID"))
  PIFLEXROLE_DURATION = int(os.getenv("PIFLEXROLE_DURATION"))
  PIFLEXER_COST = int(os.getenv("PIFLEXER_COST"))


  BASE_PIFLOUZ_MESSAGE = f"\nThis is the piflouz mining message, react every {REACT_TIME_INTERVAL} seconds to gain more {PIFLOUZ_EMOJI}\n\n\
  You just need to react with the {PIFLOUZ_EMOJI} emoji\n\
  If you waited long enough ({REACT_TIME_INTERVAL} seconds), you will earn {NB_PIFLOUZ_PER_REACT} {PIFLOUZ_EMOJI}!\n\
  A :white_check_mark: reaction will appear for 2 seconds to make you know you won\n\
  A :x: reaction will appear for 2s if you did not wait for long enough, better luck next time\n"


  greetings = [ "Greetings <@{}>! Nice to meet you!",
                "Hello there <@{}>, how are you doing today ?",
                "Hello, oh great <@{}>. Hope you are doing great"]
  
  streamers_to_check = ["Pibou421", "Mattheus_45"]

  