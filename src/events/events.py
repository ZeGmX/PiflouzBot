import asyncio
import datetime
from interactions import BrandColors, Button, ButtonStyle, Color, Embed, EmbedAttachment, EmbedField, FlatUIColors, IntervalTrigger, listen
from interactions.client.utils.misc_utils import disable_components
import logging
from math import floor
import os
import random

from constant import Constants
from custom_task_triggers import TaskCustom as Task
from database import db
import embed_messages
import pibox
from piflouz_generated import PiflouzSource, add_to_stat
import piflouz_handlers
import powerups
from random_pool import RandomPool, RandomPoolTable
from seasons import get_season_end_date
import utils
from wordle import Wordle

from .matches_challenge import MatchesInterface
from .subsequence_challenge import SubseqChallenge


logger = logging.getLogger("custom_log")

waiting_for_reset = asyncio.Lock()  # Lock to prevent multiple instances of the event reset task
prepare_free = asyncio.Event()  # False by default, True means we can run the prepare_events task with no concurrency issues
prepare_free.set()


@Task.create(IntervalTrigger(minutes=5))
async def event_handlers(bot):
    """
    Task that handles the starting/ending of the events
    Also handles the event actions every 5 minutes

    Parameters
    ----------
    bot (interactions.Client)
    """
    # This global variable keeps track of whether this task is already running in another instance, and is handling the event reset part
    # If it is, we don't want to run it again
    # Otherwise, if the task is called at e.g. t = 320 s before the reset, then it would be called again at t = 20 s before, and both instances would try to reset the event
    global waiting_for_reset

    now = datetime.datetime.now(tz=Constants.TIMEZONE)
    then = Constants.EVENT_TIME
    then = now.replace(hour=then.hour, minute=then.minute, second=then.second)
    dt = (then - now).total_seconds() % (3600 * 24)

    current_event_passive = get_event_object(EventType.PASSIVE)
    if current_event_passive is not None:
        await current_event_passive.actions_every_5min(bot)

    if dt > 330 or waiting_for_reset.locked():  # More than 5 minutes before the next event (with a few more seconds to be extra safe)
        return

    await waiting_for_reset.acquire()
    await asyncio.sleep(dt)

    await update_events(bot)
    waiting_for_reset.release()


async def update_events(bot):
    """
    Stops the current events and starts new ones

    Parameters
    ----------
    bot (interactions.Client)
    """
    logger.info("Updating the events")

    # End the current event
    await end_event(bot, EventType.PASSIVE)
    await end_event(bot, EventType.CHALLENGE)
    bot.dispatch("event_ended")

    # Chose the new event of the day
    now = datetime.datetime.now(Constants.TIMEZONE)

    # Overrides the buffered event
    if now.date() == get_season_end_date():
        channel = await bot.fetch_channel(db["out_channel"])
        await channel.send("The season will end today, so the next event will be tomorrow!")
        return

    # Ensure there is an event ready to start
    await wait_for_buffer_ready(bot)

    # Overrides the buffered event
    if now.month == 4 and now.day == 1:
        new_event_passive = BirthdayEvent()
    elif now.month == 4 and now.day == 2:
        # The current event is still the birthday event, so get_event_data will return the birthday data
        new_event_passive = BirthdayRaffleEvent(get_event_data(EventType.PASSIVE)["baked_cakes"]["total"] * BirthdayEvent.REWARD_PER_CAKE)
    elif now.month == 10 and now.day == 31:
        new_event_passive = HalloweenEvent()
    else:
        new_event_passive = eval(db["events"]["passive"]["buffered_event"])

    new_event_challenge = eval(db["events"]["challenge"]["buffered_event"])

    id1 = await new_event_passive.on_begin(bot)
    id2_msg, id2_thread = await new_event_challenge.on_begin(bot)

    db["events"]["passive"]["current_message_id"] = id1
    db["events"]["passive"]["current_event"] = new_event_passive.to_str()
    db["events"]["challenge"]["current_message_id"] = id2_msg
    db["events"]["challenge"]["current_thread_id"] = id2_thread
    db["events"]["challenge"]["current_event"] = new_event_challenge.to_str()

    logger.info("Successfully started the events")

    reset_buffered_events()
    await prepare_events(bot)


async def wait_for_buffer_ready(bot):
    """
    Checks if all buffered events are ready, otherwise computes a new set of events
    Note 1: if we are already computing the events from another source, this function will asynchronously wait until the other source is finished
    Note 2: if two or more sources are waiting, all of them will be released all at once (so it's best to avoid that    )

    Parameters
    ----------
    bot (interactions.Client)
    """
    global prepare_free

    if not prepare_free.is_set():  # Buffered events are being computed from another source
        print("Currently waiting for buffered events to be prepared somewhere else")
        await prepare_free.wait()
        print("Done waiting")
        return

    prepare_free.clear()
    if db["events"]["passive"]["buffered_event"] == "" or db["events"]["challenge"]["buffered_event"] == "":
        reset_buffered_events()
        await prepare_events(bot)
    prepare_free.set()


async def prepare_events(bot):
    """
    Buffers the event for the next day in the database
    Date-related events are not buffered, but override the buffered event in `update_events`

    Parameters
    ----------
    bot (interactions.Client)
    """
    global prepare_free

    logger.info("Event preparation started")

    prepare_free.clear()
    new_event_passive = Constants.RANDOM_EVENTS_PASSIVE.get_random()
    new_event_challenge = Constants.RANDOM_EVENTS_CHALLENGE.get_random()

    await new_event_passive.prepare(bot)
    db["events"]["passive"]["buffered_event"] = new_event_passive.to_str()

    await new_event_challenge.prepare(bot)
    db["events"]["challenge"]["buffered_event"] = new_event_challenge.to_str()

    print("Done preparing events")
    logger.info("Event preparation completed")
    prepare_free.set()


def reset_buffered_events():
    """
    Resets the buffered events in the database
    """
    db["events"]["passive"]["buffered_event"] = ""
    db["events"]["challenge"]["buffered_event"] = ""
    db["events"]["passive"]["buffered_data"] = dict()
    db["events"]["challenge"]["buffered_data"] = dict()


async def end_event(bot, event_type):
    """
    Ends an ongoing event

    Parameters
    ----------
    bot (interactions.Client)
    event_type (int)
    """
    current_event = get_event_object(event_type)

    if current_event is None: return

    try:
        data = db["events"]["passive"] if event_type == EventType.PASSIVE else db["events"]["challenge"]
        await current_event.on_end(bot, data["current_message_id"], data["current_thread_id"] if isinstance(current_event, ChallengeEvent) else None)

        match event_type:
            case EventType.PASSIVE: db["events"]["passive"]["current_event"] = ""
            case EventType.CHALLENGE: db["events"]["challenge"]["current_event"] = ""
    except Exception as e:
        print(f"Error ending event: {e}")


def get_default_db_data(event_type):
    """
    Returns the default dict for the event of the given type

    Parameters
    ----------
    event_type (int)

    Returns
    -------
    data (dict)
    """
    match event_type:
        case EventType.PASSIVE:
            return {
                "current_event": "",
                "buffered_event": "",
                "current_message_id": -1,
                "buffered_data": dict(),
                "raffle": {"participation": dict()},
                "birthday": {"baked_cakes": {"total": 0}, "ingredients": dict(), "last_delivery": {"id": -1, "qty": dict()}},
                "birthday_raffle": {"participation": []}
            }
        case EventType.CHALLENGE:
            return {
                "current_event": "",
                "buffered_event": "",
                "current_message_id": -1,
                "current_thread_id": -1,
                "buffered_data": dict(),
                "match": {"riddle": "", "main_solution": "", "all_solutions": [], "url_riddle": "", "url_solution": "", "completed": dict()},
                "subseq": {"subseq": "", "example_solution": "", "completed": dict(), "nb_solutions": [], "msg_id": dict()},
                "wordle": {"word": "", "guesses": dict()}
            }


def reset_event_database(event_type):
    """
    Resets the database for the event

    Parameters
    ----------
    event_type (int)
    """
    match event_type:
        case EventType.PASSIVE:
            db["events"]["passive"] = get_default_db_data(event_type)
        case EventType.CHALLENGE:
            db["events"]["challenge"] = get_default_db_data(event_type)


def get_event_object(event):
    """
    Returns the event object of the given type

    Parameters
    ----------
    event (int)

    Returns
    -------
    event (Event)
    """
    try:
        match event:
            case EventType.PASSIVE:
                return eval(db["events"]["passive"]["current_event"]) if db["events"]["passive"]["current_event"] != "" else None
            case EventType.CHALLENGE:
                return eval(db["events"]["challenge"]["current_event"]) if db["events"]["challenge"]["current_event"] != "" else None
    except Exception: pass

    return None


def get_event_data(e):
    """
    Returns the data dict of the event

    Parameters
    ----------
    e (int)

    Returns
    -------
    data (dict (Element_dict))
    """
    if isinstance(e, int):  # Event type is given
        e = get_event_object(e)

    if e is None:
        return None

    assert isinstance(e, Event), "The input must be an Event object"

    match e:
        case BirthdayEvent(): return db["events"]["passive"]["birthday"]
        case BirthdayRaffleEvent(): return db["events"]["passive"]["birthday_raffle"]
        case RaffleEvent(): return db["events"]["passive"]["raffle"]
        case WordleEvent(): return db["events"]["challenge"]["wordle"]
        case MoveMatchEvent(): return db["events"]["challenge"]["match"]
        case SubseqChallengeEvent(): return db["events"]["challenge"]["subseq"]


def get_buffer_event_data(e):
    """
    Returns the buffered data dict of the event

    Parameters
    ----------
    e (int)
    """
    if e is None: return None

    if isinstance(e, Event): e = EventType.PASSIVE if isinstance(e, PassiveEvent) else EventType.CHALLENGE

    match e:
        case EventType.PASSIVE: return db["events"]["passive"]["buffered_data"]
        case EventType.CHALLENGE: return db["events"]["challenge"]["buffered_data"]


async def fetch_event_message(bot, event_type):
    """
    Returns the message announcing the event

    Parameters
    ----------
    bot (interactions.Client)
    event_type (int)

    Returns
    -------
    message (interactions.Message)
    """
    channel = await bot.fetch_channel(db["out_channel"])
    match event_type:
        case EventType.PASSIVE: return await channel.fetch_message(db["events"]["passive"]["current_message_id"])
        case EventType.CHALLENGE: return await channel.fetch_message(db["events"]["challenge"]["current_message_id"])


async def fetch_event_thread(bot, event_type):
    """
    Returns the message announcing the event

    Parameters
    ----------
    bot (interactions.Client)
    event_type (int)

    Returns
    -------
    thread (interactions.Thread)
    """
    match event_type:
        case EventType.PASSIVE: return None
        case EventType.CHALLENGE: return await bot.fetch_channel(db["events"]["challenge"]["current_thread_id"])


async def register_listeners(bot):
    """
    Registers the required listeners for the events

    Parameters
    ----------
    bot : interactions.Client
    """
    for event in [EventType.PASSIVE, EventType.CHALLENGE]:
        current_event = get_event_object(event)
        if current_event is not None:
            await current_event.register_listeners(bot)


class EventType:
    PASSIVE = 0
    CHALLENGE = 1


class Event:
    """
    Base class for the events, inherited by every event class
    """

    async def prepare(self, bot):
        """
        Prepares the event for the next day

        Parameters
        ----------
        bot (interactions.Client)
        """
        pass

    async def on_begin(self, bot):
        """
        Actions to be done when the event starts

        Parameters
        ----------
        bot (interactions.Client)

        Returns
        -------
        int:
            id of the message announcing the event
        """
        return None

    async def on_end(self, bot, msg_id, thread_id=None):
        """
        Actions to be done when the event ends

        Parameters
        ----------
        bot (interactions.Client)
        msg_id (int):
            id of the message announcing the event
        thread_id (int):
            id of the thread created for the event
        """
        pass

    def get_powerups(self):
        """
        Returns the list of powerups active during the event

        Returns
        -------
        res (Powerup list)
        """
        return []

    def get_pibox_pool_table(self):
        """
        Returns the pibox pool for the event
        This table can be used to update the global pibox pool table
        """
        return RandomPoolTable()

    def to_str(self):
        """
        Returns a string used to store in the database, and get back the object with eval

        Returns
        -------
        res (str)
        """
        return ""

    async def actions_every_5min(self, bot):
        """
        Actions to be done every 5 minutes

        Parameters
        ----------
        bot (interactions.Client)
        """
        pass

    async def register_listeners(self, bot):
        """
        Registers the required listeners for the event

        Parameters
        ----------
        bot : interactions.Client
        """
        pass


class PassiveEvent(Event):
    async def get_embed(self, bot):
        """
        Returns an embed for the announcement message

        Parameters
        ----------
        bot (interactions.Client)

        Returns
        -------
        embed (interactions.Embed)
        """
        return None

    async def on_begin(self, bot):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new event
        embed = await self.get_embed(bot)
        message = await out_channel.send(embed=embed)
        await message.pin()
        await self.register_listeners(bot)
        return int(message.id)

    async def on_end(self, bot, msg_id, thread_id=None):
        if "out_channel" not in db.keys(): return

        out_channel = await bot.fetch_channel(db["out_channel"])
        old_message = await out_channel.fetch_message(msg_id)
        await old_message.unpin()


class RaffleEvent(PassiveEvent):
    """
    Raffle event, people can buy tickets and the person with the winning ticket wins all the money (minus taxes)
    """

    def __init__(self, ticket_price, tax_ratio, max_base_prize=300):
        self.ticket_price = ticket_price
        self.tax_ratio = tax_ratio
        self.max_base_prize = max_base_prize

    async def prepare(self, bot):
        get_buffer_event_data(self)["base_prize"] = random.randint(self.max_base_prize // 2, self.max_base_prize)

    async def on_begin(self, bot):
        data = get_event_data(self)
        data["base_prize"] = get_buffer_event_data(self)["base_prize"]
        data["tickets_from_pibox"] = 0
        return await super().on_begin(bot)

    async def on_end(self, bot, msg_id, thread_id=None):
        await super().on_end(bot, msg_id, thread_id)

        out_channel = await bot.fetch_channel(db["out_channel"])
        data = get_event_data(self)
        participation = data["participation"]

        # Computing the winner for the last raffle
        if len(participation) > 0:

            total_tickets = sum(participation.values())
            winning_index = random.randrange(0, total_tickets)

            partial_sum = 0
            for id, value in participation.items():
                if partial_sum <= winning_index < partial_sum + value:
                    break
                partial_sum += value

            prize = self.get_raffle_total_prize()
            data["participation"] = dict()

            # Giving the tax to the bot
            tax_value = total_tickets * self.ticket_price - prize
            piflouz_handlers.update_piflouz(bot.user.id, qty=tax_value, check_cooldown=False)
            add_to_stat(data["base_prize"] + data["tickets_from_pibox"] * self.ticket_price, PiflouzSource.EVENT)

            piflouz_handlers.update_piflouz(id, prize, check_cooldown=False)
            embed = await embed_messages.get_embed_end_raffle(bot, id, prize)
            await out_channel.send(embed=embed)

            await utils.update_piflouz_message(bot)
            bot.dispatch("raffle_won", id)

    def to_str(self):
        return f"{type(self).__name__}({self.ticket_price}, {self.tax_ratio}, {self.max_base_prize})"

    async def update_raffle_message(self, bot):
        """
        Updates the raffle message with amount of tickets bought by everyone

        Parameters
        ----------
        bot (interactions.Client)
        """
        embed = await self.get_embed(bot)
        raffle_message = await fetch_event_message(bot, EventType.PASSIVE)
        await raffle_message.edit(embed=embed)

    async def get_embed(self, bot):
        data = get_event_data(self)
        desc = f"Here is the new raffle! Use `/raffle n` to buy `n` 🎟️!\n\
    They cost {self.ticket_price} {Constants.PIFLOUZ_EMOJI} each\n\
    The user with the winning ticket will earn {100 - self.tax_ratio}% of the total money spent by everyone, plus a {data["base_prize"]} {Constants.PIFLOUZ_EMOJI} base prize!"

        fields = []

        participation = get_event_data(self)["participation"]
        if len(participation) > 0:
            async def get_str(key_val):
                user_id, nb_tickets = key_val
                return f"<@{user_id}> - {nb_tickets}\n"

            tasks = [get_str(key_val) for key_val in participation.items()]
            res = await asyncio.gather(*tasks)
            val = "".join(res)

            total_prize = self.get_raffle_total_prize()

            fields.append(EmbedField(name="Current 🎟️ bought", value=val, inline=False))
            fields.append(EmbedField(name="Total prize", value=f"The winner will earn {total_prize} {Constants.PIFLOUZ_EMOJI}!", inline=False))

        embed = Embed(title="Passive event of the day: new Raffle!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=fields)

        return embed

    def get_raffle_total_prize(self):
        """
        Returns the total prize in the current raffle
        Returns 0 if there is no current raffle

        Returns
        -------
        prize (int)
        """
        data = get_event_data(self)
        nb_tickets = sum(data["participation"].values())
        prize = floor(nb_tickets * self.ticket_price * (100 - self.tax_ratio) / 100) + data["base_prize"]
        return prize

    def get_pibox_pool_table(self):
        pool = RandomPool("pibox_raffle", [("RafflePibox", 1)])
        return RandomPoolTable([(pool, Constants.PIBOX_POOL_TABLE.pools[0][1])])


class EventFromPowerups(PassiveEvent):
    """
    Creates an event with just a list of powerups
    """

    def __init__(self, *powerup_list):
        self.powerups = list(powerup_list)

    def get_powerups(self):
        return self.powerups

    async def get_embed(self, bot):
        descriptions = [p.get_event_str() for p in self.powerups]
        content = "\n".join(descriptions)
        field = EmbedField(name="The following powerups are active:", value=content)

        embed = Embed(title="Passive event of the day", color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[field])
        return embed

    def to_str(self):
        powerups_str = ", ".join([p.to_str() for p in self.powerups])
        return f"{EventFromPowerups.__name__}({powerups_str})"


class IncreasedPiboxDropRateEvent(EventFromPowerups):
    def __init__(self, value):
        p = powerups.PiboxDropRateMultiplier(value)
        super().__init__(p)


class IncreasedPiflouzEvent(EventFromPowerups):
    def __init__(self, value):
        p = powerups.PiflouzMultiplier(None, value, None)
        super().__init__(p)


class CooldownReductionEvent(EventFromPowerups):
    def __init__(self, value):
        p = powerups.CooldownReduction(None, value, None)
        super().__init__(p)


class ComboEvent(EventFromPowerups):
    def __init__(self, val_max_combo, val_multi_combo):
        p1 = powerups.ComboMaxIncrease(val_max_combo)
        p2 = powerups.ComboRewardMultiplier(val_multi_combo)
        super().__init__(p1, p2)


class IncreasedPiflouzAndCooldownEvent(EventFromPowerups):
    def __init__(self, val_piflouz, val_cooldown):
        p1 = powerups.PiflouzMultiplier(None, val_piflouz, None)
        p2 = powerups.CooldownReduction(None, val_cooldown, None)
        super().__init__(p1, p2)


class PiboxDropRateAndRewardEvent(EventFromPowerups):
    def __init__(self, val_drop_rate, val_reward):
        p1 = powerups.PiboxDropRateMultiplier(val_drop_rate)
        p2 = powerups.PiboxSizeMultiplier(val_reward)
        super().__init__(p1, p2)


class StoreDiscountEvent(EventFromPowerups):
    def __init__(self, value):
        p1 = powerups.StorePriceMultiplier(value)
        super().__init__(p1)


class PiboxRewardIncreasedEvent(EventFromPowerups):
    def __init__(self, value):
        p1 = powerups.PiboxSizeMultiplier(value)
        super().__init__(p1)


class ChallengeEvent(Event):
    async def get_embed(self, bot):
        """
        Returns an embed for the announcement message

        Parameters
        ----------
        bot (interactions.Client)

        Returns
        -------
        embed (interactions.Embed)
        """
        return None

    async def on_begin(self, bot):
        """
        output:
            int -> id of the message announcing the event
            int -> id of the thread created for the event
        """
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new event
        embed = await self.get_embed(bot)
        message = await out_channel.send(embed=embed)
        await message.pin()
        now = datetime.date.today()
        thread = await message.create_thread(name=f"[{now.day}/{now.month}] Challenge event of the day")
        await self.register_listeners(bot)
        return int(message.id), int(thread.id)

    async def on_end(self, bot, msg_id, thread_id):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])
        old_message = await out_channel.fetch_message(msg_id)
        await old_message.unpin()


class WordleEvent(ChallengeEvent):
    def __init__(self, min_reward=100, max_reward=150, hard_mode_bonus=100):
        self.min_reward = min_reward
        self.max_reward = max_reward
        self.hard_mode_bonus = hard_mode_bonus

    async def get_embed(self, bot):
        """
        Returns an embed to announce the event

        Returns
        -------
        embed (interactions.Embed)
        """
        desc = f"Use `/wordle guess [word]` to try to find the word of the day\nYou can also check your progress with `/wordle status`\nYou can earn between {self.min_reward} and {self.max_reward} {Constants.PIFLOUZ_EMOJI} depending on your score\n You can get an additional {self.hard_mode_bonus} {Constants.PIFLOUZ_EMOJI} if you find the word in hard mode (ie if every attempts respects all constraints from previous attempts)!"

        embed = Embed(title="Challenge event of the day: new Wordle!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[])
        return embed

    async def prepare(self, bot):
        data = get_buffer_event_data(self)
        data["word"] = Wordle().solution

    async def on_begin(self, bot):
        get_event_data(self)["word"] = get_buffer_event_data(self)["word"]

        return await super().on_begin(bot)

    async def on_end(self, bot, msg_id, thread_id=None):
        data = get_event_data(self)
        data["guesses"] = dict()

        thread = await bot.fetch_channel(thread_id)
        await thread.send("The event is over! The word of the day was **" + data["word"] + "**")

        await super().on_end(bot, msg_id, thread_id)

    def to_str(self):
        return f"{WordleEvent.__name__}({self.min_reward}, {self.max_reward})"


class BirthdayEvent(PassiveEvent):
    INGREDIENTS = ["🥛", "🥚", "🍫", "🧈"]
    INGREDIENTS_PER_CAKE = {"🥛": 1, "🥚": 2, "🍫": 3, "🧈": 1}
    REWARD_PER_CAKE = 100

    def __init__(self, spawn_rate=.25):
        self.spawn_rate = spawn_rate

    async def on_begin(self, bot):
        data = get_event_data(self)
        data["baked_cakes"] = {"total": 0}
        data["ingredients"] = dict()

        return await super().on_begin(bot)

    async def on_end(self, bot, msg_id, thread_id=None):
        await super().on_end(bot, msg_id, thread_id)

        # Disable previous deliveries
        data = get_event_data(self)
        delivery = data["last_delivery"]
        data["last_delivery"] = dict()

        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])

        if len(delivery) > 0:
            msg = await out_channel.fetch_message(delivery["id"])
            components = components = [self.get_component(emoji, nb, disabled=True) for emoji, nb in zip(self.INGREDIENTS, delivery["qty"].values())]
            await msg.edit(content="Unfortunately, the delivery person has left", components=components)

        embed = self.get_end_embed()
        await out_channel.send(embed=embed)

    async def get_embed(self, bot):
        nb_backed_cakes = get_event_data(self)["baked_cakes"]["total"]

        current_year = datetime.datetime.now().year
        age = current_year - 2021

        embed = Embed(title="Happy birthday Pibot!", thumbnail=EmbedAttachment(url=Constants.PIBOU4BIRTHDAY_URL),
            description=f"Today is Pibot's {age} years anniversary!\nYour goal is to bake as much birthday cake as possible! To do so, deliveries will appear randomly through the day, bringing cake resources. You can collect these resources, but be quick, or the delivery person will get impatient and leave. You can use the `/role get Birthday Notifications` command to get notified when the delivery arrives.\n Each cake requires {", ".join(f"{nb} {e}" for e, nb in self.INGREDIENTS_PER_CAKE.items())} to be baked. Pibot will earn {self.REWARD_PER_CAKE} {Constants.PIFLOUZ_EMOJI} per cake, and get very happy!\n You can check your progress and inventory using the `/birthday` command.\n\nCakes baked so far: {nb_backed_cakes}",
            color=BrandColors.WHITE
        )
        return embed

    def get_end_embed(self):
        """
        Returns the embed shown at the end of the event

        Returns
        -------
        embed (interactions.Embed)
        """
        nb_cakes = get_event_data(self)["baked_cakes"]["total"]
        embed = Embed(title="The baking is over!", thumbnail=EmbedAttachment(url=Constants.PIBOU4BIRTHDAY_URL),
            description=f"Congratulations, you managed to bake {nb_cakes} cakes. Pibot will invest the earned {nb_cakes * self.REWARD_PER_CAKE} {Constants.PIFLOUZ_EMOJI} in the next event! 👀",
            color=BrandColors.WHITE
        )
        return embed

    def get_component(self, emoji, nb, disabled=False):
        """
        Returns a button for a given ingredient

        Parameters
        ----------
        emoji (str)
        nb (int)
        disabled (bool)

        Returns
        -------
        interactions.Button
        """
        return Button(style=ButtonStyle.SECONDARY, label=str(nb), emoji=emoji, custom_id=emoji, disabled=disabled)

    async def actions_every_5min(self, bot):
        if "out_channel" not in db.keys():
            return
        out_channel = await bot.fetch_channel(db["out_channel"])

        # Amount of each ingredient
        qty = [random.randint(1, 5) for _ in self.INGREDIENTS]

        # Disable previous deliveries
        data = get_event_data(self)
        delivery = data["last_delivery"]
        data["last_delivery"] = dict()

        if len(delivery) > 0:
            msg = await out_channel.fetch_message(delivery["id"])
            components = disable_components(*msg.components)
            await msg.edit(content="Unfortunately, the delivery person has left", components=components)

        # Check if a delivery happens
        if random.random() > self.spawn_rate:
            return

        # Create a new delivery
        components = [self.get_component(emoji, nb) for emoji, nb in zip(self.INGREDIENTS, qty)]
        role_notif = await bot.guilds[0].fetch_role(Constants.BIRTHDAY_NOTIF_ROLE_ID)
        msg = await out_channel.send(f"{role_notif.mention} A new cake ingredient delivery has appeared! But you can only take one type so chose carefully", components=components)
        data["last_delivery"] = {"id": int(msg.id), "qty": {e: nb for e, nb in zip(self.INGREDIENTS, qty)}}

    def bake_cakes(self, user_id):
        """
        Uses a user's inventory to bake some cakes

        Parameters
        ----------
        user_id (str)
        """
        data = get_event_data(self)
        inv = dict(data["ingredients"][user_id])

        nb_cakes = min(inv[e] // self.INGREDIENTS_PER_CAKE[e] for e in self.INGREDIENTS)

        for ingredient in self.INGREDIENTS:
            inv[ingredient] -= nb_cakes * self.INGREDIENTS_PER_CAKE[ingredient]

        data["baked_cakes"]["total"] += nb_cakes
        data["baked_cakes"][user_id] += nb_cakes
        data["ingredients"][user_id] = inv

    async def update_birthday_message(self, bot):
        """
        Updates the birthday message with the amount of baked cakes

        Parameters
        ----------
        bot (interactions.Client)
        """
        embed = await self.get_embed(bot)
        message = await fetch_event_message(bot, EventType.PASSIVE)
        await message.edit(embed=embed)

    def to_str(self):
        return f"{BirthdayEvent.__name__}()"


class BirthdayRaffleEvent(PassiveEvent):
    """
    A special raffle event where you don't have to spend money
    """

    BUTTON_ID = "🎟️"

    def __init__(self, reward):
        self.reward = reward

    async def on_begin(self, bot):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new raffle
        embed = await self.get_embed(bot)
        button = self.get_component()
        message = await out_channel.send(embed=embed, components=button)
        await message.pin()
        return int(message.id)

    async def on_end(self, bot, msg_id, thread_id=None):
        await super().on_end(bot, msg_id, thread_id)

        data = get_event_data(self)
        participation = list(data["participation"])

        # Computing the winner for the last raffle
        if len(participation) >= 3:

            winner1 = random.choice(participation)
            participation.remove(winner1)
            winner2 = random.choice(participation)
            participation.remove(winner2)
            winner3 = random.choice(participation)

            data["participation"] = []

            prize1 = round(self.reward * .5)
            prize2 = round(self.reward * .3)
            prize3 = round(self.reward * .2)

            piflouz_handlers.update_piflouz(winner1, qty=prize1, check_cooldown=False)
            piflouz_handlers.update_piflouz(winner2, qty=prize2, check_cooldown=False)
            piflouz_handlers.update_piflouz(winner3, qty=prize3, check_cooldown=False)

            if "out_channel" not in db.keys(): return

            message = f"The birthday raffle is over! <@{winner1}> won {prize1} {Constants.PIFLOUZ_EMOJI}, <@{winner2}> won {prize2} {Constants.PIFLOUZ_EMOJI} and <@{winner3}> won {prize3} {Constants.PIFLOUZ_EMOJI}!"
            out_channel = await bot.fetch_channel(db["out_channel"])
            await out_channel.send(message)

            add_to_stat(self.reward, PiflouzSource.EVENT)
            await utils.update_piflouz_message(bot)

    def to_str(self):
        return f"{type(self).__name__}({self.reward})"

    async def update_raffle_message(self, bot):
        """
        Updates the birthday raffle message with the participants

        Parameters
        ----------
        bot (interactions.Client)
        """
        embed = await self.get_embed(bot)
        button = self.get_component()
        raffle_message = await fetch_event_message(bot, EventType.PASSIVE)
        await raffle_message.edit(embed=embed, components=button)

    async def get_embed(self, bot):
        desc = f"Today's raffle is special! Click the button below to participate, and it's completely free! {self.reward} {Constants.PIFLOUZ_EMOJI} are at stake! The first winner will earn 50%, the second one will get 30% and the third winner will get 20%!"

        embed = Embed(title="Birthday Special Raffle!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4BIRTHDAY_URL))

        participation = get_event_data(self)["participation"]
        if len(participation) > 0:
            val = "\n".join(f"• <@{user_id}>" for user_id in participation)

            embed.add_field(name="Current participants", value=val, inline=False)
            embed.add_field(name="Total prize", value=f"The three winners will earn 50%, 30% and 20% of the total jackpot of {self.reward} {Constants.PIFLOUZ_EMOJI}!", inline=False)

        return embed

    def get_component(self):
        """
        Returns the button to register to the Raffle

        Returns
        -------
        res (interactions.Button)
        """
        res = Button(style=ButtonStyle.SECONDARY, custom_id=self.BUTTON_ID, emoji=self.BUTTON_ID)
        return res


class MoveMatchEvent(ChallengeEvent):
    """
    An event showing an equation with two matches to move to make it correct
    """

    def __init__(self, reward):
        self.reward = reward

    async def get_embed(self, img_url):
        """
        Returns an embed to announce the event

        Parameters
        ----------
        image_url (str):
            Imgur url of the image to show

        Returns
        -------
        embed (interactions.Embed)
        """
        desc = f"Use `/match guess [equation]` to try to find the correct solution of the day and earn {self.reward} {Constants.PIFLOUZ_EMOJI}!"
        embed = Embed(title="Challenge event of the day: move exactly two matches to make the equation correct!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[], images=EmbedAttachment(url=img_url))
        return embed

    async def prepare(self, bot):
        event = await MatchesInterface.new()
        event.save_all("src/events/")
        url_riddle = utils.upload_image_to_imgur("src/events/riddle.png")
        url_sol = utils.upload_image_to_imgur("src/events/solution.png")

        data = get_buffer_event_data(self)
        data["riddle"] = event.riddle.str
        data["main_solution"] = event.main_sol.str
        data["all_solutions"] = event.all_sols
        data["url_riddle"] = url_riddle
        data["url_solution"] = url_sol

    async def on_begin(self, bot):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])

        data = get_event_data(self)
        buffer = get_buffer_event_data(self)

        for key, val in buffer.items():
            data[key] = val

        # Starting new event
        embed = await self.get_embed(data["url_riddle"])
        message = await out_channel.send(embed=embed)
        await message.pin()
        now = datetime.date.today()
        thread = await message.create_thread(name=f"[{now.day}/{now.month}] Challenge event of the day")
        return int(message.id), int(thread.id)

    async def on_end(self, bot, msg_id, thread_id=None):
        data = get_event_data(self)
        found_solutions = set(data["completed"].values())

        desc_str = f"The event is over! {bot.user.mention} found {len(data["all_solutions"])} solutions. Below is one of them.\n\n"

        if len(found_solutions) > 0:
            found_solutions_str = f"||{", ".join(found_solutions)}||"
            desc_str += f"You found the following solutions: {found_solutions_str}"
        else:
            desc_str += "Unfortunately, no one found any solution this time :("

        thread = await bot.fetch_channel(thread_id)
        embed = Embed(title="The event is over!", description=desc_str, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), images=EmbedAttachment(url=data["url_solution"]))
        await thread.send(embed=embed)

        await super().on_end(bot, msg_id, thread_id)

        data["completed"] = dict()
        data["all_solutions"] = []

        try:
            os.remove("src/events/riddle.png")
            os.remove("src/events/solution.png")
        except Exception:
            print("Could not remove match event files")

    def to_str(self):
        return f"{MoveMatchEvent.__name__}({self.reward})"


class SubseqChallengeEvent(ChallengeEvent):
    """
    An event where the user has to find a word with a given subsequence
    """

    def __init__(self, reward_default, reward_bonus1, reward_bonus2, reward_bonus3, reward_uniqueness, max_rewardable_words, reward_per_word):
        self.reward_default = reward_default
        self.reward_bonus1 = reward_bonus1
        self.reward_bonus2 = reward_bonus2
        self.reward_bonus3 = reward_bonus3
        self.reward_uniqueness = reward_uniqueness
        self.max_rewardable_words = max_rewardable_words
        self.reward_per_word = reward_per_word

    async def get_embed(self, bot):
        desc = f"Use `/subseq guess [word]` to try to find the answer.\n\n\
You can earn {Constants.PIFLOUZ_EMOJI} in the following ways:\n\
• [Level 1] Find any solution to earn {self.reward_default} {Constants.PIFLOUZ_EMOJI}!\n\
• [Level 2] Find a solution that contains exactly the same amount of occurences of each subsequence letter to earn an additional {self.reward_bonus1} {Constants.PIFLOUZ_EMOJI}!\n\
• [Level 3] Find a solution that contains at least one letter between each subsequence letter to earn an additional {self.reward_bonus2} {Constants.PIFLOUZ_EMOJI}!\n\
• [Level 4] Find a solution that meets the previous two conditions to earn an additional {self.reward_bonus3} {Constants.PIFLOUZ_EMOJI}!\n\
• Up to {self.max_rewardable_words} correct solutions are rewarded with an additional {self.reward_per_word} {Constants.PIFLOUZ_EMOJI} each!\n\
• If one of your first {self.max_rewardable_words} correct guesses was not in anyone else's first {self.max_rewardable_words} guesses, you will earn an additional {self.reward_uniqueness} {Constants.PIFLOUZ_EMOJI} at the end of the event!"

        embed = Embed(title=f"Challenge event of the day: find a french word that has \"{get_event_data(self)["subseq"]}\" as a subsequence", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[])
        return embed

    async def prepare(self, bot):
        data = get_buffer_event_data(self)

        s, nb_sols, main_sol = await asyncio.to_thread(SubseqChallenge.new, random.randint(3, 6))
        data = get_buffer_event_data(self)

        data["subseq"] = s.subseq
        data["example_solution"] = main_sol
        data["nb_solutions"] = nb_sols

    async def on_begin(self, bot):
        data = get_event_data(self)
        buffer = get_buffer_event_data(self)

        for key, val in buffer.items():
            data[key] = val

        return await super().on_begin(bot)

    async def on_end(self, bot, msg_id, thread_id=None):
        data = get_event_data(self)

        found_solutions = set()  # All the submitted words, used in the announcement message
        found_solutions_nb = dict()  # How many times each word was submitted, used to compute the rewards
        for user_sol in data["completed"].values():
            found_solutions.update(user_sol["guesses"])
            for w in user_sol["guesses"][:self.max_rewardable_words]:
                if w not in found_solutions_nb:
                    found_solutions_nb[w] = 0
                found_solutions_nb[w] += 1

            # We still need to set this up to avoid errors accessing the dict afterwards
            # Note: extra words will be displayed but not counted towards the unicity rewards
            for w in user_sol["guesses"][self.max_rewardable_words:]:
                if w not in found_solutions_nb:
                    found_solutions_nb[w] = 0
        found_solutions_unclean = SubseqChallenge.get_unclean_equivalent(*found_solutions)

        # Bold unique solutions
        for i, w in enumerate(found_solutions):
            if found_solutions_nb[w] == 1:
                found_solutions_unclean[i] = f"**{found_solutions_unclean[i]}**"
            elif found_solutions_nb[w] == 0:
                found_solutions_unclean[i] = f"[{found_solutions_unclean[i]}]"

        # Separate solutions by level
        found_solutions_levels = [[], [], [], []]
        s = SubseqChallenge(subseq=data["subseq"])
        for w in found_solutions_unclean:
            lvl2 = s.check_projection(w)
            lvl3 = s.check_with_intermediate(w)
            if lvl2 and lvl3: found_solutions_levels[3].append(w)
            elif lvl3: found_solutions_levels[2].append(w)
            elif lvl2: found_solutions_levels[1].append(w)
            else: found_solutions_levels[0].append(w)

        # Generate the string to display
        str_lines = ["||" + ", ".join(sorted(lvl)) + "||" if len(lvl) > 0 else "None" for lvl in found_solutions_levels]
        str_lines_prefix = ["1️⃣: ", "2️⃣: ", "3️⃣: ", "4️⃣: "]
        found_solutions_str = "\n".join(f"{prefix}{line}" for prefix, line in zip(str_lines_prefix, str_lines))

        # Find users who found a unique solution
        user_unique_sol = []
        for user_id, user_sol in data["completed"].items():
            guesses = user_sol["guesses"][:3]
            if any(found_solutions_nb[w] == 1 for w in guesses):
                piflouz_handlers.update_piflouz(user_id, self.reward_uniqueness, check_cooldown=False)
                user_unique_sol.append(f"<@{user_id}>")

        data["completed"] = dict()
        data["msg_id"] = dict()

        res_str = f"The event is over! Here is a level 4 solution: **{data["example_solution"]}**\n"

        # All solutions found
        if len(found_solutions_unclean) > 0:
            res_str += f"Here are all the solutions you found (unique words are bolded, and extra words are between brackets):\n{found_solutions_str}\n\n"
        else:
            res_str += "Unfortunately, no one found any solution this time :(\n\n"

        # All existing solutions
        res_str += f"There were {data["nb_solutions"][0]} level 1 solutions, {data["nb_solutions"][1]} level 2 solutions, {data["nb_solutions"][2]} level 3 solutions and {data["nb_solutions"][3]} level 4 solutions in total.\n\n"

        # Users who found unique solutions
        if len(user_unique_sol) > 0:
            res_str += f"The following people earned an additional {self.reward_uniqueness} {Constants.PIFLOUZ_EMOJI} for finding a unique solution:{", ".join(user_unique_sol)}"
        else:
            res_str += "Unfortunately, no one found a unique solution this time :("

        thread = await bot.fetch_channel(thread_id)
        await thread.send(res_str)

        await super().on_end(bot, msg_id, thread_id)

    def to_str(self):
        return f"{SubseqChallengeEvent.__name__}({self.reward_default}, {self.reward_bonus1}, {self.reward_bonus2}, {self.reward_bonus3}, {self.reward_uniqueness}, {self.max_rewardable_words}, {self.reward_per_word})"


class HalloweenEvent(PassiveEvent):
    """
    An event where pibox drop rate is increased, but pibox are haunter
    """

    def __init__(self, drop_rate_value=200):
        self.drop_rate_value = drop_rate_value
        self.powerups = [powerups.PiboxDropRateMultiplier(self.drop_rate_value)]

    def get_powerups(self):
        return self.powerups

    async def get_embed(self, bot):
        embed = Embed(title="Passive event of the day: it's spooky time! 🦇 🎃 👻", thumbnail=EmbedAttachment(url=Constants.HALLOWEEN_PIFLOUZ_URL),
            description=f"Today's pibox are haunted! Will you be brave enough to get them?\nTo compensate, the following powerup is active:\n{self.powerups[0].get_event_str()}",
            color=FlatUIColors.PUMPKIN
        )
        return embed

    def get_pibox_pool_table(self):
        pool = RandomPool("pibox", [("QuickReactPibox", 0), ("TriviaPibox", 0), ("HauntedPibox", 1)])
        return RandomPoolTable([(pool, Constants.PIBOX_POOL_TABLE.pools[0][1])])

    def to_str(self):
        return f"{HalloweenEvent.__name__}({self.drop_rate_value})"


class PiboxFromGetEvent(PassiveEvent):
    """
    Event where there is a chance to drop a pibox after using the /get command
    """

    def __init__(self, proba_spawn=.1):
        self.proba_spawn = proba_spawn

    async def get_embed(self, bot):
        embed = Embed(title="Pibox event of the day", thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL),
            description=f"Today, there is a {int(self.proba_spawn * 100)}% chance to drop a pibox when using the `/get` command!\nGood luck!",
            color=Color.random()
        )
        return embed

    def to_str(self):
        return f"{PiboxFromGetEvent.__name__}({self.proba_spawn})"

    async def _on_get(self, bot, user_id):
        if random.random() < self.proba_spawn:
            box = await pibox.QuickReactPibox.new(bot, custom_message=f"<@{user_id}> found this pibox while using the `/get` command! 🎁")
            if box is not None:
                pibox.add_box_to_db(box)

    async def _remove_listeners(self, bot):
        bot.listeners["combo_updated"].remove(self._listener_get)
        bot.listeners["event_ended"].remove(self._listener_end)

    async def register_listeners(self, bot):
        @listen("combo_updated")
        async def custom_get_listener(event, user_id):
            await self._on_get(bot, user_id)
        bot.add_listener(custom_get_listener)
        self._listener_get = custom_get_listener

        @listen("event_ended")
        async def custom_event_end_listener(event):
            await self._remove_listeners(bot)
        bot.add_listener(custom_event_end_listener)
        self._listener_end = custom_event_end_listener
