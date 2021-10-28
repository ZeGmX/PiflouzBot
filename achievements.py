from replit import db

from achievement_handler import listen_to
from constant import Constants
import piflouz_handlers
import powerups


class Achievement:
  name = "placeholder name"
  description = "placeholder description"
  reward = 0
  # is_secret = True/False
  # requirements = [achievements]

  async def check(self, user_id, *args, **kwargs):
    """
    Checks if the achievement is unlocked
    --
    input:
      user_id: int/str
    """
    self.validate(user_id)
  

  def validate(self, user_id):
    """
    Registers the validation of the achievement in the database and gives the reward to the user
    --
    input:
      user_id: int/str
    """
    user_id = str(user_id)
    
    if user_id not in db["achievements"].keys(): db["achievements"][user_id] = []

    db["achievements"][user_id].append(self.to_str())
    piflouz_handlers.update_piflouz(user_id, qty=self.reward, check_cooldown=False)
    print(f"validated {self.to_str()} for user {user_id}")


  def is_validated(self, user_id):
    """
    Checks in the datbase to see if a given user has validated the event
    --
    input:
      user_id: int/str
    """
    user_id = str(user_id)
    
    return user_id in db["achievements"].keys() and self.to_str() in db["achievements"][user_id]
  

  def to_str(self):
    """
    Returns a string that can be turned in the object using eval()
    """
    return f"{type(self).__name__}()"


@listen_to("help")
class Achievement_help(Achievement):
  name = "Getting to know me"
  description = "Use the `/help` command"
  reward = 10


@listen_to("hello")
class Achievement_hello(Achievement):
  name = "Well hello there!"
  description = "Use the `/hello` command"
  reward = 10


@listen_to("pilord")
class Achievement_pilord_cmd(Achievement):
  name = "Ambitious"
  description = "Use the `/pilord` command"
  reward = 10


@listen_to("raffle_participation_successful")
class Achievement_raffle_participation(Achievement):
  name = "Test your luck"
  description = "Participate to a raffle event"
  reward = 10


@listen_to("raffle_participation_successful")
class Achievement_raffle_participation_20(Achievement):
  name = "Intermediate gambler"
  description = "Put at least 20 tickets in a single raffle"
  reward = 50

  async def check(self, user_id, *args, **kwargs):
    if db["raffle_participation"][str(user_id)] >= 20:
      self.validate(user_id)


@listen_to("raffle_participation_successful")
class Achievement_raffle_participation_100(Achievement):
  name = "Intermediate gambler"
  description = "Put at least 100 tickets in a single raffle"
  reward = 300

  async def check(self, user_id, *args, **kwargs):
    if db["raffle_participation"][str(user_id)] >= 100:
      self.validate(user_id)


@listen_to("raffle_won")
class Achievement_won_raffle(Achievement):
  name = "The lucky winer"
  description = "Win a raffle"
  reward = 1000


@listen_to("donation_successful")
class Achievement_donate(Achievement):
  name = "How generous level 1"
  description = "Donate piflouz to someone"
  reward = 100


@listen_to("giveaway_successful")
class Achievement_giveaway(Achievement):
  name = "How generous level 2"
  description = "Create a giveaway"
  reward = 100


@listen_to("get")
class Achievement_slash_get(Achievement):
  name = "Piflouz mining"
  description = "Use the `/get` command"
  reward = 10


@listen_to("store_purchase_successful")
class Achievement_buy_store(Achievement):
  name = "Shopper"
  description = "Buy a powerup"
  reward = 20


@listen_to("piflexer_rank_bought")
class Achievement_rank_pilexer(Achievement):
  name = "Piflex level 1"
  description = "Buy the piflexer rank to show how cool you are"
  reward = 500


@listen_to("piflex_bought")
class Achievement_piflex(Achievement):
  name = "Piflex level 2"
  description = "Make a piflex!"
  reward = 1000


@listen_to("piflex_bought")
class Achievement_3_piflex(Achievement):
  name = "Piflex novice"
  description = "Discover 3 piflex images"
  reward = 2000

  async def check(self, user_id, *args, **kwargs):
    if len(db["discovered_piflex"][str(user_id)]) >= 3:
      self.validate(user_id)


@listen_to("piflex_bought")
class Achievement_6_piflex(Achievement):
  name = "Piflex adept"
  description = "Discover 6 piflex images"
  reward = 3000

  async def check(self, user_id, *args, **kwargs):
    if len(db["discovered_piflex"][str(user_id)]) >= 6:
      self.validate(user_id)


@listen_to("piflex_bought")
class Achievement_9_piflex(Achievement):
  name = "Piflex expert"
  description = "Discover 9 piflex images"
  reward = 4000

  async def check(self, user_id, *args, **kwargs):
    if len(db["discovered_piflex"][str(user_id)]) >= 9:
      self.validate(user_id)


@listen_to("piflex_bought")
class Achievement_12_piflex(Achievement):
  name = "Piflex Champion"
  description = "Discover 12 piflex images"
  reward = 5000

  async def check(self, user_id, *args, **kwargs):
    if len(db["discovered_piflex"][str(user_id)]) >= 12:
      self.validate(user_id)


@listen_to("become_pilord")
class Achievement_pilord(Achievement):
  name = "The richest one"
  description = "Become pilord"
  reward = 2000


@listen_to("store_purchase_successful")
class Achievement_full_miner(Achievement):
  name = "Dedicated miner"
  description = "Buy the maximum amount of miners"
  reward = 1000

  async def check(self, user_id, *args, **kwargs):
    for powerup in db["powerups"][str(user_id)]:
      p = eval(powerup)
      if isinstance(p, powerups.Miner_powerup) and p.qty == p.max_qty:
        self.validate(user_id)


@listen_to("store_purchase_successful")
class Achievement_2_temporary_powerups_active(Achievement):
  name = "Powerup addict"
  description = "Have two temporary powerups active at the same time"
  reward = 100

  async def check(self, user_id, *args, **kwargs):
    count = 0
    for powerup in db["powerups"][str(user_id)]:
      if isinstance(eval(powerup), powerups.Powerups_non_permanent):
        count += 1
      if count == 2: 
        self.validate(user_id)
        return


@listen_to("pibox_obtained")
class Achievement_pibox_obtained(Achievement):
  name = "The fastest clicker in the west"
  description = "Be the first to get a pibox"
  reward = 100


@listen_to("pibox_obtained")
class Achievement_empty_pibox(Achievement):
  name = "So fast, but for what?"
  description = "Get a pibox with 0 piflouz"
  reward = 100

  async def check(self, user_id, qty, *args, **kwargs):
    if qty == 0:
      self.validate(user_id)


@listen_to("duel_created")
class Achievement_create_duel(Achievement):
  name = "Let's fight - 1"
  description = "Create a new duel"
  reward = 50


@listen_to("duel_accepted")
class Achievement_accept_duel(Achievement):
  name = "Let's fight - 2"
  description = "Accept a duel"
  reward = 50


@listen_to("duel_won")
class Achievement_win_duel(Achievement):
  name = "The undefeatable"
  description = "Win a duel"
  reward = 100


@listen_to("combo_updated")
class Achievement_combo_1(Achievement):
  name = "Discovering combos"
  description = "Reach a combo of 1"
  reward = 10

  async def check(self, user_id, *args, **kwargs):
    if db["mining_combo"][str(user_id)] >= 1:
      self.validate(user_id)


@listen_to("combo_updated")
class Achievement_combo_max(Achievement):
  name = "The addict"
  description = "Reach the maximum rewardable combo"
  reward = 100

  async def check(self, user_id, *args, **kwargs):
    if db["mining_combo"][str(user_id)] >= Constants.MAX_MINING_COMBO:
      self.validate(user_id)


@listen_to("combo_updated")
class Achievement_combo_2max(Achievement):
  name = "The addict"
  description = "Reach a combo of twice the maximum rewardable combo"
  reward = 400

  async def check(self, user_id, *args, **kwargs):
    if db["mining_combo"][str(user_id)] >= 2 * Constants.MAX_MINING_COMBO:
      self.validate(user_id)


@listen_to("combo_updated")
class Achievement_combo_3max(Achievement):
  name = "The addict"
  description = "Reach a combo of three times the maximum rewardable combo"
  reward = 1000

  async def check(self, user_id, *args, **kwargs):
    if db["mining_combo"][str(user_id)] >= 3 * Constants.MAX_MINING_COMBO:
      self.validate(user_id)


@listen_to("donation_successful")
class Achievement_donate_1(Achievement):
  name = "Not so generous"
  description = "Donate 1 piflouz to someone (which is taken by Pibot as a tax)"
  reward = 1

  async def check(self, user_id, amount, *args, **kwargs):
    if amount == 1:
      self.validate(user_id)


@listen_to("donation_successful")
class Achievement_donate_to_pibot(Achievement):
  name = "Give me more piflouz!"
  description = "Donate piflouz to Pibot"
  reward = 10

  async def check(self, user_id, amount, id_receiver, *args, **kwargs):
    if id_receiver == Constants.BOT_ID:
      self.validate(user_id)


@listen_to("pibox_failed")
class Achievement_fail_pibox(Achievement):
  name = "So fast but not so accurate"
  description = "React to an unclaimed pibox with the wrong emoji"
  reward = 100


