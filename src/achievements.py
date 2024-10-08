from achievement_handler import listen_to
from events import EventType, get_event_data, get_event_object
from piflouz_generated import PiflouzSource, add_to_stat
import piflouz_handlers
import powerups
import user_profile


class Achievement:
    name = "placeholder name"
    description = "placeholder description"
    reward = 0
    # is_secret = True/False
    # requirements = [achievements]

    async def check(self, user_id, *args, **kwargs):
        """
        Checks if the achievement is unlocked

        Parameters
        ----------
        user_id (int/str)
        """
        self.validate(user_id)

    def validate(self, user_id):
        """
        Registers the validation of the achievement in the database and gives the reward to the user

        Parameters
        ----------
        user_id (int/str)
        """
        user_id = str(user_id)
        profile = user_profile.get_profile(user_id)

        profile["achievements"].append(self.to_str())
        piflouz_handlers.update_piflouz(user_id, qty=self.reward, check_cooldown=False)
        add_to_stat(self.reward, PiflouzSource.ACHIEVEMENT)
        print(f"validated {self.to_str()} for user {user_id}")

    def is_validated(self, user_id):
        """
        Checks in the database to see if a given user has validated the event

        Parameters
        ----------
        user_id (int/str)
        """
        user_id = str(user_id)
        profile = user_profile.get_profile(user_id)

        return self.to_str() in profile["achievements"]

    def to_str(self):
        """
        Returns a string that can be turned in the object using eval()
        """
        return f"{type(self).__name__}()"


@listen_to("help")
class AchievementHelp(Achievement):
    name = "Hello World"
    description = "Use the `/help` command"
    reward = 10


@listen_to("hello")
class AchievementHello(Achievement):
    name = "Well Hello There!"
    description = "Use the `/hello` command"
    reward = 10


@listen_to("pilord")
class AchievementPilordCmd(Achievement):
    name = "Ambitious"
    description = "Use the `/pilord` command"
    reward = 10


@listen_to("raffle_participation_successful")
class AchievementRaffleParticipation(Achievement):
    name = "Get Lucky"
    description = "Participate to a raffle event"
    reward = 10


@listen_to("raffle_participation_successful")
class AchievementRaffleParticipation20(Achievement):
    name = "Intermediate Gambler"
    description = "Put at least 20 tickets in a single raffle"
    reward = 50

    async def check(self, user_id, *args, **kwargs):
        current_raffle = get_event_object(EventType.PASSIVE)
        raffle_data = get_event_data(current_raffle)

        if raffle_data["participation"][str(user_id)] >= 20:
            self.validate(user_id)


@listen_to("raffle_participation_successful")
class AchievementRaffleParticipation100(Achievement):
    name = "Extreme Gambler"
    description = "Put at least 100 tickets in a single raffle"
    reward = 300

    async def check(self, user_id, *args, **kwargs):
        current_raffle = get_event_object(EventType.PASSIVE)
        raffle_data = get_event_data(current_raffle)

        if raffle_data["participation"][str(user_id)] >= 100:
            self.validate(user_id)


@listen_to("raffle_won")
class AchievementWonRaffle(Achievement):
    name = "The Lucky Winner"
    description = "Win a raffle"
    reward = 1000


@listen_to("donation_successful")
class AchievementDonate(Achievement):
    name = "How Generous! (1)"
    description = "Donate piflouz to someone"
    reward = 100


@listen_to("giveaway_successful")
class AchievementGiveaway(Achievement):
    name = "How Generous! (2)"
    description = "Create a giveaway"
    reward = 100


@listen_to("get")
class AchievementSlashGet(Achievement):
    name = "Piflouz Mining"
    description = "Use the `/get` command"
    reward = 10


@listen_to("store_purchase_successful")
class AchievementBuyStore(Achievement):
    name = "Shopper"
    description = "Buy a powerup"
    reward = 20


@listen_to("piflexer_rank_bought")
class AchievementRankPilexer(Achievement):
    name = "Piflex Level 1"
    description = "Buy the piflexer rank to show how cool you are"
    reward = 500


@listen_to("piflex_bought")
class AchievementPiflex(Achievement):
    name = "Piflex Level 2"
    description = "Do a piflex!"
    reward = 1000


@listen_to("piflex_bought")
class Achievement3Piflex(Achievement):
    name = "Piflex Novice"
    description = "Discover 3 piflex images"
    reward = 2000

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if len(profile["discovered_piflex"]) >= 3:
            self.validate(user_id)


@listen_to("piflex_bought")
class Achievement6Piflex(Achievement):
    name = "Piflex Adept"
    description = "Discover 6 piflex images"
    reward = 3000

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if len(profile["discovered_piflex"]) >= 6:
            self.validate(user_id)


@listen_to("piflex_bought")
class Achievement9Piflex(Achievement):
    name = "Piflex Expert"
    description = "Discover 9 piflex images"
    reward = 4000

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if len(profile["discovered_piflex"]) >= 9:
            self.validate(user_id)


@listen_to("piflex_bought")
class Achievement12Piflex(Achievement):
    name = "Piflex Champion"
    description = "Discover 12 piflex images"
    reward = 5000

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if len(profile["discovered_piflex"]) >= 12:
            self.validate(user_id)


@listen_to("become_pilord")
class AchievementPilord(Achievement):
    name = "The Richest One"
    description = "Become pilord"
    reward = 2000


@listen_to("store_purchase_successful")
class AchievementFullMiner(Achievement):
    name = "Diggy Diggy Hole"
    description = "Buy the maximum amount of miners"
    reward = 1000

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        for powerup in profile["powerups"]:
            p = eval(powerup)
            if isinstance(p, powerups.Miner_powerup) and p.qty == p.max_qty:
                self.validate(user_id)


@listen_to("store_purchase_successful")
class Achievement2TemporaryPowerupsActive(Achievement):
    name = "Powerup Addict"
    description = "Have two temporary powerups active at the same time"
    reward = 100

    async def check(self, user_id, *args, **kwargs):
        count = 0
        profile = user_profile.get_profile(user_id)
        for powerup in profile["powerups"]:
            if isinstance(eval(powerup), powerups.PowerupsNonPermanent):
                count += 1
            if count == 2:
                self.validate(user_id)
                return


@listen_to("pibox_obtained")
class AchievementPiboxObtained(Achievement):
    name = "The Fastest Clicker In The West"
    description = "Be the first to get a pibox"
    reward = 100


@listen_to("pibox_obtained")
class AchievementEmptyPibox(Achievement):
    name = "So Fast, But For What?"
    description = "Get a pibox with 0 piflouz"
    reward = 100

    async def check(self, user_id, qty, *args, **kwargs):
        if qty == 0:
            self.validate(user_id)


@listen_to("duel_created")
class AchievementCreateDuel(Achievement):
    name = "Let the Battles Begin! (1)"
    description = "Create a new duel"
    reward = 50


@listen_to("duel_accepted")
class AchievementAcceptDuel(Achievement):
    name = "Let the Battles Begin! (2)"
    description = "Accept a duel"
    reward = 50


@listen_to("duel_won")
class AchievementWinDuel(Achievement):
    name = "The Undefeatable"
    description = "Win a duel"
    reward = 100


@listen_to("combo_updated")
class AchievementCombo1(Achievement):
    name = "Discovering Combos"
    description = "Reach a combo of 1"
    reward = 10

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if profile["mining_combo"] >= 1:
            self.validate(user_id)


@listen_to("combo_updated")
class AchievementComboMax(Achievement):
    name = "The Addict (1)"
    description = "Reach the maximum rewardable combo"
    reward = 100

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if profile["mining_combo"] >= piflouz_handlers.get_max_rewardable_combo(user_id):
            self.validate(user_id)


@listen_to("combo_updated")
class AchievementCombo2max(Achievement):
    name = "The Addict (2)"
    description = "Reach a combo of twice the maximum rewardable combo"
    reward = 400

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if profile["mining_combo"] >= 2 * piflouz_handlers.get_max_rewardable_combo(user_id):
            self.validate(user_id)


@listen_to("combo_updated")
class AchievementCombo3max(Achievement):
    name = "The Addict (3)"
    description = "Reach a combo of three times the maximum rewardable combo"
    reward = 1000

    async def check(self, user_id, *args, **kwargs):
        profile = user_profile.get_profile(user_id)
        if profile["mining_combo"] >= 3 * piflouz_handlers.get_max_rewardable_combo(user_id):
            self.validate(user_id)


@listen_to("donation_successful")
class AchievementDonate1(Achievement):
    name = "Not So Generous"
    description = "Donate 1 piflouz to someone (which is taken by Pibot as a tax)"
    reward = 1

    async def check(self, user_id, amount, *args, **kwargs):
        if amount == 1:
            self.validate(user_id)


@listen_to("donation_successful")
class AchievementDonateToPibot(Achievement):
    name = "Give Me More Piflouz!"
    description = "Donate piflouz to Pibot"
    reward = 10

    async def check(self, user_id, amount, id_receiver, bot_id, *args, **kwargs):
        if id_receiver == bot_id:
            self.validate(user_id)


@listen_to("pibox_failed")
class AchievementFailPibox(Achievement):
    name = "So Fast But Not So Accurate"
    description = "React to an unclaimed pibox with the wrong emoji"
    reward = 100
