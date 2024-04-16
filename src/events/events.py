import asyncio
import datetime
from interactions import Embed, EmbedField, EmbedAttachment, Button, ButtonStyle, IntervalTrigger, Color, BrandColors
from interactions.client.utils.misc_utils import disable_components
from math import floor
import os
from pytz import timezone
import random

from constant import Constants
from custom_task_triggers import TaskCustom as Task
import embed_messages
from .matches_challenge import Matches_Interface
from .subsequence_challenge import Subseq_challenge
from my_database import db
import piflouz_handlers
import powerups
import utils
from wordle import Wordle


@Task.create(IntervalTrigger(minutes=5))
async def event_handlers(bot):
    tz = timezone("Europe/Paris")
    now = datetime.datetime.now()
    then = Constants.EVENT_TIME
    then = now.replace(hour=then.hour, minute=then.minute, second=then.second).astimezone(tz)
    dt = (then - now.astimezone(tz)).total_seconds() % (3600 * 24)
    
    current_event_passive = get_event_object(Event_type.PASSIVE)
    if current_event_passive is not None:
        await current_event_passive.actions_every_5min(bot)

    if dt > 330:  # More than 5 minutes before the next event (with a few more seconds to be extra safe)
        return

    await asyncio.sleep(dt)

    await update_events(bot)


async def update_events(bot):
    """
    Stops the current events and starts new ones
    --
    input:
        bot: interactions.Client
    """
    # End the current event
    await end_event(bot, Event_type.PASSIVE)
    await end_event(bot, Event_type.CHALLENGE)
    
    # Chose the new event of the day
    now = datetime.datetime.now()

    if now.month == 4 and now.day == 1:
        new_event_passive = Birthday_event()
    elif now.month == 4 and now.day == 2:
        # The current event is still the birthday event, so get_event_data will return the birthday data
        new_event_passive = Birthday_raffle_event(get_event_data(Event_type.PASSIVE)["baked_cakes"]["total"] * Birthday_event.REWARD_PER_CAKE)
    else:
        new_event_passive = random.choice(Constants.RANDOM_EVENTS_PASSIVE)
    
    new_event_challenge = random.choice(Constants.RANDOM_EVENTS_CHALLENGE)

    id1 = await new_event_passive.on_begin(bot)
    id2_msg, id2_thread = await new_event_challenge.on_begin(bot)

    db["events"]["passive"]["current_message_id"] = id1
    db["events"]["passive"]["current_event"] = new_event_passive.to_str()
    db["events"]["challenge"]["current_message_id"] = id2_msg
    db["events"]["challenge"]["current_thread_id"] = id2_thread
    db["events"]["challenge"]["current_event"] = new_event_challenge.to_str()


async def end_event(bot, event_type):
    """
    Ends an ongoing event
    --
    input:
        bot: interactions.Client
        event_type: int (Event_type)
    """
    current_event = get_event_object(event_type)
    
    if current_event is None: return  

    try:
        data = db["events"]["passive"] if event_type == Event_type.PASSIVE else db["events"]["challenge"]
        await current_event.on_end(bot, data["current_message_id"], data["current_thread_id"] if isinstance(current_event, Challenge_event) else None)
        
        match event_type:
            case Event_type.PASSIVE: db["events"]["passive"]["current_event"] = ""
            case Event_type.CHALLENGE: db["events"]["challenge"]["current_event"] = ""
    except Exception as e:
        print(f"Error ending event: {e}")


def get_default_db_data(event_type):
    """
    Returns the default dict for the event of the given type
    --
    input:
        event_type: int (Event_type)
    --
    output:
        data: dict
    """
    match event_type:
        case Event_type.PASSIVE:
            return {
                "current_event": "",
                "current_message_id": -1,
                "raffle": {"participation": dict()},
                "birthday": {"baked_cakes": {"total": 0}, "ingredients": dict(), "last_delivery": {"id": -1, "qty": dict()}},
                "birthday_raffle": {"participation": []}
            }
        case Event_type.CHALLENGE:
            return {
                "current_event": "",
                "current_message_id": -1,
                "current_thread_id": -1,
                "match": {"riddle": "", "main_solution": "", "all_solutions": [], "url_riddle": "", "url_solution": "", "completed": dict()},
                "subseq": {"subseq": "", "example_solution": "", "completed": dict(), "nb_solutions": []},
                "wordle": {"word": "", "guesses": dict()}
            }


def reset_event_database(event_type):
    """
    Resets the database for the event
    --
    input:
        event_type: int (Event_type)
    """
    match event_type:
        case Event_type.PASSIVE:
            db["events"]["passive"] = get_default_db_data(event_type)
        case Event_type.CHALLENGE:
            db["events"]["challenge"] = get_default_db_data(event_type)


def get_event_object(event):
    """
    Returns the event object of the given type
    --
    input:
        event: int (Event_type)
    --
    output:
        event: Event
    """
    try:
        match event:
            case Event_type.PASSIVE:
                return eval(db["events"]["passive"]["current_event"]) if db["events"]["passive"]["current_event"] != "" else None
            case Event_type.CHALLENGE:
                return eval(db["events"]["challenge"]["current_event"]) if db["events"]["challenge"]["current_event"] != "" else None
    except: pass
    
    return None


def get_event_data(e):
    """
    Returns the data dict of the event
    --
    input:
        e: int (Event_type) / Event
    --
    output:
        data: dict (Element_dict)
    """
    if isinstance(e, int): # Event type is given
        e = get_event_object(e)
    
    if e is None:
        return None
    
    assert isinstance(e, Event), "The input must be an Event object"

    match e:
        case Birthday_event(): return db["events"]["passive"]["birthday"]
        case Birthday_raffle_event(): return db["events"]["passive"]["birthday_raffle"]
        case Raffle_event(): return db["events"]["passive"]["raffle"]
        case Wordle_event(): return db["events"]["challenge"]["wordle"]
        case Move_match_event(): return db["events"]["challenge"]["match"]
        case Subseq_challenge_event(): return db["events"]["challenge"]["subseq"]
    

async def fetch_event_message(bot, event_type):
    """
    Returns the message announcing the event
    --
    input:
        bot: interactions.Client
        event_type: int (Event_type)
    --
    output:
        message: interactions.Message
    """
    channel = await bot.fetch_channel(db["out_channel"])
    match event_type:
        case Event_type.PASSIVE: return await channel.fetch_message(db["events"]["passive"]["current_message_id"])
        case Event_type.CHALLENGE: return await channel.fetch_message(db["events"]["challenge"]["current_message_id"])


async def fetch_event_thread(bot, event_type):
    """
    Returns the message announcing the event
    --
    input:
        bot: interactions.Client
        event_type: int (Event_type)
    --
    output:
        thread: interactions.Thread
    """
    match event_type:
        case Event_type.PASSIVE: return None
        case Event_type.CHALLENGE: return await bot.fetch_channel(db["events"]["challenge"]["current_thread_id"])


class Event_type:
    PASSIVE = 0
    CHALLENGE = 1

class Event:
    """
    Base class for the events, inherited by every event class
    """

    async def on_begin(self, bot):
        """
        Actions to be done when the event starts
        --
        input:
            bot: interactions.Client
        --
        output:
            int -> id of the message announcing the event
        """
        return None


    async def on_end(self, bot, msg_id, thread_id=None):
        """
        Actions to be done when the event ends
        --
        input:
            bot: interactions.Client
            msg_id: int -> id of the message announcing the event
            thread_id: int -> id of the thread created for the event
        """
        pass


    def get_powerups(self):
        """
        Returns the list of powerups active during the event
        --
        output:
            res: Powerup list
        """
        return []


    def to_str(self):
        """
        Returns a string used to store in the database, and get back the object with eval
        --
        output:
            res: str
        """
        return ""


    async def actions_every_5min(self, bot):
        """
        Actions to be done every 5 minutes
        --
        input:
            bot: interactions.Client
        """
        pass


class Passive_event(Event):
    async def get_embed(self, bot):
        """
        Returns an embed for the announcement message
        --
        input:
            bot: interactions.Client
        --
        output:
            embed: interactions.Embed
        """
        return None


    async def on_begin(self, bot):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new event
        embed = await self.get_embed(bot)
        message = await out_channel.send(embed=embed)
        await message.pin()
        return int(message.id)


    async def on_end(self, bot, msg_id, thread_id=None):
        if "out_channel" not in db.keys(): return

        out_channel = await bot.fetch_channel(db["out_channel"])
        old_message = await out_channel.fetch_message(msg_id)
        await old_message.unpin()


class Raffle_event(Passive_event):
    """
    Raffle event, people can buy tickets and the person with the winning ticket wins all the money (minus taxes)
    """
    def __init__(self, ticket_price, tax_ratio):
        self.ticket_price = ticket_price
        self.tax_ratio = tax_ratio


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

            piflouz_handlers.update_piflouz(id, prize, check_cooldown=False)
            embed = await embed_messages.get_embed_end_raffle(bot, id, prize)
            await out_channel.send(embed=embed)

            await utils.update_piflouz_message(bot)
            bot.dispatch("raffle_won", id)


    def to_str(self):
        return f"{type(self).__name__}({self.ticket_price}, {self.tax_ratio})"


    async def update_raffle_message(self, bot):
        """
        Updates the raffle message with amount of tickets bought by everyone
        --
        input:
            bot: interactions.Client
        """
        channel = await bot.fetch_channel(db["out_channel"])
        embed = await self.get_embed(bot)
        raffle_message = await fetch_event_message(bot, Event_type.PASSIVE)
        await raffle_message.edit(embed=embed)


    async def get_embed(self, bot):
        desc = f"Here is the new raffle! Use `/raffle n` to buy `n` 🎟️!\n\
    They cost {self.ticket_price} {Constants.PIFLOUZ_EMOJI} each\n\
    The user with the winning ticket will earn {100 - self.tax_ratio}% of the total money spent by everyone!"

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
        --
        output:
            prize: int
        """
        nb_tickets = sum(get_event_data(self)["participation"].values())
        prize = floor(nb_tickets * self.ticket_price * (100 - self.tax_ratio) / 100)
        return prize


class Event_from_powerups(Passive_event):
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
        return f"{Event_from_powerups.__name__}({powerups_str})"


class Increased_pibox_drop_rate_event(Event_from_powerups):
    def __init__(self, value):
        p = powerups.Pibox_drop_rate_multiplier(value)
        super().__init__(p)


class Increased_piflouz_event(Event_from_powerups):
    def __init__(self, value):
        p = powerups.Piflouz_multiplier(None, value, None)
        super().__init__(p)


class Cooldown_reduction_event(Event_from_powerups):
    def __init__(self, value):
        p = powerups.Cooldown_reduction(None, value, None)
        super().__init__(p)


class Combo_event(Event_from_powerups):
    def __init__(self, val_max_combo, val_multi_combo):
        p1 = powerups.Combo_max_increase(val_max_combo)
        p2 = powerups.Combo_reward_multiplier(val_multi_combo)
        super().__init__(p1, p2)


class Increased_piflouz_and_cooldown_event(Event_from_powerups):
    def __init__(self, val_piflouz, val_cooldown):
        p1 = powerups.Piflouz_multiplier(None, val_piflouz, None)
        p2 = powerups.Cooldown_reduction(None, val_cooldown, None)
        super().__init__(p1, p2)


class Pibox_drop_rate_and_reward_event(Event_from_powerups):
    def __init__(self, val_drop_rate, val_reward):
        p1 = powerups.Pibox_drop_rate_multiplier(val_drop_rate)
        p2 = powerups.Pibox_size_multiplier(val_reward)
        super().__init__(p1, p2)


class Challenge_event(Event):
    async def get_embed(self, bot):
        """
        Returns an embed for the announcement message
        --
        input:
            bot: interactions.Client
        --
        output:
            embed: interactions.Embed
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
        return int(message.id), int(thread.id)


    async def on_end(self, bot, msg_id, thread_id):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])
        old_message = await out_channel.fetch_message(msg_id)
        await old_message.unpin()


class Wordle_event(Challenge_event):
    def __init__(self, min_reward=100, max_reward=150, hard_mode_bonus=100):
        self.min_reward = min_reward
        self.max_reward = max_reward
        self.hard_mode_bonus = hard_mode_bonus


    async def get_embed(self, bot):
        """
        Returns an embed to announce the event
        --
        output:
            embed: interactions.Embed
        """
        desc = f"Use `/wordle guess [word]` to try to find the word of the day\nYou can also check your progress with `/wordle status`\nYou can earn between {self.min_reward} and {self.max_reward} {Constants.PIFLOUZ_EMOJI} depending on your score\n You can get an additional {self.hard_mode_bonus} {Constants.PIFLOUZ_EMOJI} if you find the word in hard mode (ie if every attempts respects all constraints from previous attempts)!"

        embed = Embed(title="Challenge event of the day: new Wordle!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[])
        return embed


    async def on_begin(self, bot):
        get_event_data(self)["word"] = Wordle().solution
        
        return await super().on_begin(bot)


    async def on_end(self, bot, msg_id, thread_id=None):
        data = get_event_data(self)
        data["guesses"] = dict()

        thread = await bot.fetch_channel(thread_id)
        await thread.send("The event is over! The word of the day was **" + data["word"] + "**")

        await super().on_end(bot, msg_id, thread_id)


    def to_str(self):
        return f"{Wordle_event.__name__}({self.min_reward}, {self.max_reward})"


class Birthday_event(Passive_event):
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
        --
        output:
            embed: interactions.Embed
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
        --
        input:
            emoji: str
            nb: int
            disabled: bool
        --
        output:
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
        --
        input:
            user_id: str (of an int)
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
        --
        input:
            bot: interactions.Client
        """
        embed = await self.get_embed(bot)
        message = await fetch_event_message(bot, Event_type.PASSIVE)
        await message.edit(embed=embed)


    def to_str(self):
        return f"{Birthday_event.__name__}()"


class Birthday_raffle_event(Passive_event):
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

            db["piflouz_generated"]["event"] += self.reward
            await utils.update_piflouz_message(bot)


    def to_str(self):
        return f"{type(self).__name__}({self.reward})"


    async def update_raffle_message(self, bot):
        """
        Updates the birthday raffle message with the participants
        --
        input:
            bot: interactions.Client
        """
        embed = await self.get_embed(bot)
        button = self.get_component()
        raffle_message = await fetch_event_message(bot, Event_type.PASSIVE)
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
        --
        output:
            res: interactions.Button
        """
        res = Button(style=ButtonStyle.SECONDARY, custom_id=self.BUTTON_ID, emoji=self.BUTTON_ID)
        return res


class Move_match_event(Challenge_event):
    """
    An event showing an equation with two matches to move to make it correct
    """

    def __init__(self, reward):
        self.reward = reward
    

    async def get_embed(self, img_url):
        """
        Returns an embed to announce the event
        --
        input:
            image_url: str -> Imgur url of the image to show
        --
        output:
            embed: interactions.Embed
        """
        desc = f"Use `/match guess [equation]` to try to find the correct solution of the day and earn {self.reward} {Constants.PIFLOUZ_EMOJI}!"
        embed = Embed(title="Challenge event of the day: move exactly two matches to make the equation correct!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[], images=EmbedAttachment(url=img_url))
        return embed


    async def on_begin(self, bot):
        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])

        event = await Matches_Interface.new()
        event.save_all("src/events/")
        url_riddle = utils.upload_image_to_imgur("src/events/riddle.png")
        url_sol = utils.upload_image_to_imgur("src/events/solution.png")

        data = get_event_data(self)
        data["riddle"] = event.riddle.str
        data["main_solution"] = event.main_sol.str
        data["all_solutions"] = event.all_sols
        data["url_riddle"] = url_riddle
        data["url_solution"] = url_sol

        # Starting new event
        embed = await self.get_embed(url_riddle)
        message = await out_channel.send(embed=embed)
        await message.pin()
        now = datetime.date.today()
        thread = await message.create_thread(name=f"[{now.day}/{now.month}] Challenge event of the day")
        return int(message.id), int(thread.id)


    async def on_end(self, bot, msg_id, thread_id=None):
        data = get_event_data(self)
        found_solutions = set(data["completed"].values())
        found_solutions_str = f"||{", ".join(found_solutions)}||"

        thread = await bot.fetch_channel(thread_id)
        embed = Embed(title="The event is over!", description=f"The event is over! {bot.user.mention} found {len(data["all_solutions"])} solutions. Below is one of them.\n You found the following solutions: {found_solutions_str}", color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), images=EmbedAttachment(url=data["url_solution"]))
        await thread.send(embed=embed)

        await super().on_end(bot, msg_id, thread_id)

        data["completed"] = dict()
        data["all_solutions"] = []

        try:
            os.remove("src/events/riddle.png")
            os.remove("src/events/solution.png")
        except:
            print("Could not remove match event files")


    def to_str(self):
        return f"{Move_match_event.__name__}({self.reward})"


class Subseq_challenge_event(Challenge_event):
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


    async def on_begin(self, bot):
        s, nb_sols, main_sol = await asyncio.to_thread(Subseq_challenge.new, random.randint(3, 6))
        data = get_event_data(self)

        data["subseq"] = s.subseq
        data["example_solution"] = main_sol
        data["nb_solutions"] = nb_sols

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
        found_solutions_str = f"||{", ".join(sorted(found_solutions))}||"
        
        for user_id, user_sol in data["completed"].items():
            guesses = user_sol["guesses"][:3]
            if any(found_solutions_nb[w] == 1 for w in guesses):
                piflouz_handlers.update_piflouz(user_id, self.reward_uniqueness, check_cooldown=False)

        data["completed"] = dict()

        thread = await bot.fetch_channel(thread_id)
        await thread.send(f"The event is over! Here is a level 4 solution: **{data["example_solution"]}**\n\
Here are all the solutions you found: {found_solutions_str}\n\n\
There were {data["nb_solutions"][0]} level 1 solutions, {data["nb_solutions"][1]} level 2 solutions, {data["nb_solutions"][2]} level 3 solutions and {data["nb_solutions"][3]} level 4 solutions in total.\n\n\
if one of your first three correct guesses was not in anyone else's first three guesses, you were rewarded with {self.reward_uniqueness} {Constants.PIFLOUZ_EMOJI}!")

        await super().on_end(bot, msg_id, thread_id)
    

    def to_str(self):
        return f"{Subseq_challenge_event.__name__}({self.reward_default}, {self.reward_bonus1}, {self.reward_bonus2}, {self.reward_bonus3}, {self.reward_uniqueness}, {self.max_rewardable_words}, {self.reward_per_word})"