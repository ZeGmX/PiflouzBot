import random
import asyncio
from math import floor
from interactions import Embed, EmbedField, EmbedAttachment, Button, ButtonStyle, IntervalTrigger, Color, BrandColors
from interactions.client.utils.misc_utils import disable_components
import datetime

from constant import Constants
from custom_task_triggers import TaskCustom as Task
import embed_messages
from my_database import db
import piflouz_handlers
import powerups
import utils
import wordle


@Task.create(IntervalTrigger(minutes=5))
async def event_handlers(bot):
    now = datetime.datetime.now()
    then = Constants.EVENT_TIME
    then = datetime.datetime(now.year, now.month, now.day, then.hour,
                             then.minute, then.second)
    dt = (then - now).total_seconds() % (3600 * 24)
    
    if "current_event_passive" in db.keys():
        current_event_passive = eval(db["current_event_passive"][len(__name__) + 1:])
        await current_event_passive.actions_every_5min(bot)

    if dt > 330:  # More than 5 minutes before the next event (with a few more seconds to be extra safe)
        return

    await asyncio.sleep(dt)

    # End the current event
    await end_event(bot, "current_event_passive", "current_event_passive_message_id")
    await end_event(bot, "current_event_challenge", "current_event_challenge_message_id")

    # Chose the new event of the day
    now = datetime.datetime.now()

    if now.month == 4 and now.day == 1:
        new_event_passive = Birthday_event()
    elif now.month == 4 and now.day == 2:
        new_event_passive = Birthday_raffle_event(db["baked_cakes"]["total"] * Birthday_event.REWARD_PER_CAKE)
    else:
        new_event_passive = random.choice(Constants.RANDOM_EVENTS_PASSIVE)
    
    new_event_challenge = random.choice(Constants.RANDOM_EVENTS_CHALLENGE)

    id1 = await start_event(bot, new_event_passive)
    id2 = await start_event(bot, new_event_challenge)

    db["current_event_passive_message_id"] = id1
    db["current_event_passive"] = new_event_passive.to_str()
    db["current_event_challenge_message_id"] = id2
    db["current_event_challenge"] = new_event_challenge.to_str()


async def end_event(bot, event_key, event_msg_id_key):
    """
    Ends an ongoing event
    --
    input:
        bot: interactions.Client
        event_key: str -> key in the database of the event to end
        event_msg_id_key: str -> key in the database of the message announcing the event
    """
    if event_key in db.keys():
        current_event = eval(db[event_key][len(__name__) + 1:])
        await current_event.on_end(bot)

        channel = await bot.fetch_channel(db["out_channel"])
        old_message = await channel.fetch_message(db[event_msg_id_key])
        await old_message.unpin()


async def start_event(bot, event):
    """
    Starts a new event
    --
    input:
        bot: interactions.Client
        event: Event -> the event to start
    output:
        res: int -> id of the message announcing the event
    """
    message = await event.on_begin(bot)
    await message.pin()
    return int(message.id)


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
      msg: int -> id of the message announcing the event
    """
        return None

    async def on_end(self, bot):
        """
    Actions to be done when the event ends
    --
    input:
      bot: interactions.Client
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


class Raffle_event(Event):
    """
    Raffle event, people can buy tickets and the person with the winning ticket wins all the money (minus taxes)
    """
    def __init__(self, ticket_price, tax_ratio):
        self.ticket_price = ticket_price
        self.tax_ratio = tax_ratio


    async def on_begin(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new raffle
        embed = await self.get_embed_raffle(bot)
        message = await out_channel.send(embed=embed)
        return message


    async def on_end(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])
        participation = db["raffle_participation"]

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
            db["raffle_participation"] = dict()

            # Giving the tax to the bot
            tax_value = total_tickets * self.ticket_price - prize
            piflouz_handlers.update_piflouz(bot.user.id,
                                            qty=tax_value,
                                            check_cooldown=False)

            piflouz_handlers.update_piflouz(id, prize, check_cooldown=False)
            embed = await embed_messages.get_embed_end_raffle(bot, id, prize)
            await out_channel.send(embed=embed)

            await utils.update_piflouz_message(bot)
            bot.dispatch("raffle_won", id)


    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.ticket_price}, {self.tax_ratio})"


    async def update_raffle_message(self, bot):
        """
        Updates the raffle message with amount of tickets bought by everyone
        --
        input:
        bot: interactions.Client
        """
        if "current_event_passive_message_id" not in db.keys():
            return

        channel = await bot.fetch_channel(db["out_channel"])
        embed = await self.get_embed_raffle(bot)
        raffle_message = await channel.fetch_message(db["current_event_passive_message_id"])
        await raffle_message.edit(embed=embed)


    async def get_embed_raffle(self, bot):
        """
        Returns an embed message corresponding to the raffle message
        --
        input:
        bot: interactions.Client
        """
        desc = f"Here is the new raffle! Use `/raffle n` to buy `n` 🎟️!\n\
    They cost {self.ticket_price} {Constants.PIFLOUZ_EMOJI} each\n\
    The user with the winning ticket will earn {100 - self.tax_ratio}% of the total money spent by everyone!"

        fields = []

        if "raffle_participation" in db.keys() and len(db["raffle_participation"]) > 0:
            participation = db["raffle_participation"]

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
        nb_tickets = sum(db["raffle_participation"].values())
        prize = floor(nb_tickets * self.ticket_price * (100 - self.tax_ratio) / 100)
        return prize


class Event_from_powerups(Event):
    """
    Creates an event with just a list of powerups
    """
    def __init__(self, *powerup_list):
        self.powerups = list(powerup_list)


    async def on_begin(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new event
        embed = self.get_embed()
        message = await out_channel.send(embed=embed)
        await message.pin()
        return message


    def get_powerups(self):
        return self.powerups


    def get_embed(self):
        """
        Returns an embed to announce the event
        --
        output:
        embed: interactions.Embed
        """
        descriptions = [p.get_event_str() for p in self.powerups]
        content = "\n".join(descriptions)
        field = EmbedField(name="The following powerups are active:", value=content)

        embed = Embed(title="Passive event of the day", color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[field])
        return embed


    def to_str(self):
        powerups_str = ", ".join([p.to_str() for p in self.powerups])
        return f"{__name__}.{Event_from_powerups.__name__}({powerups_str})"


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


class Wordle_event(Event):
    def __init__(self, min_reward=200, max_reward=250):
        self.min_reward = min_reward
        self.max_reward = max_reward

    def get_embed(self):
        """
        Returns an embed to announce the event
        --
        output:
        embed: interactions.Embed
        """
        desc = f"Use `/wordle guess [word]` to try to find the word of the day and earn up to {self.max_reward}{Constants.PIFLOUZ_EMOJI}!\nYou can also check your progress with `/wordle status`"

        embed = Embed(title="Challenge event of the day: new Wordle!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL), fields=[])
        return embed


    async def on_begin(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])

        db["word_of_the_day"] = wordle.Wordle().solution

        # Starting new event
        embed = self.get_embed()
        message = await out_channel.send(embed=embed)
        await message.pin()
        return message


    async def on_end(self, bot):
        db["wordle_guesses"] = dict()

        if "out_channel" not in db.keys(): return
        out_channel = await bot.fetch_channel(db["out_channel"])
        await out_channel.send("The event is over, the word of the day was **" + db["word_of_the_day"] + "**")


    def to_str(self):
        return f"{__name__}.{Wordle_event.__name__}({self.min_reward}, {self.max_reward})"


class Birthday_event(Event):
    INGREDIENTS = ["🥛", "🥚", "🍫", "🧈"]
    INGREDIENTS_PER_CAKE = {"🥛": 1, "🥚": 2, "🍫": 3, "🧈": 1}
    REWARD_PER_CAKE = 100


    def __init__(self, spawn_rate=.25):
        self.spawn_rate = spawn_rate


    async def on_begin(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])

        db["baked_cakes"] = {"total": 0}
        db["birthday_event_ingredients"] = dict()

        # Starting new event
        embed = self.get_start_embed()
        message = await out_channel.send(embed=embed)
        await message.pin()
        return message


    async def on_end(self, bot):
        if "out_channel" not in db.keys():
            return
        out_channel = await bot.fetch_channel(db["out_channel"])

        # Disable previous deliveries
        delivery = db["last_birthday_delivery"]
        db["last_birthday_delivery"] = dict()

        if len(delivery) > 0:
            msg = await out_channel.fetch_message(delivery["id"])
            components = components = [self.get_component(emoji, nb, disabled=True) for emoji, nb in zip(self.INGREDIENTS, delivery["qty"].values())]
            await msg.edit(content="Unfortunately, the delivery person has left", components=components)

        embed = self.get_end_embed()
        await out_channel.send(embed=embed)


    def get_start_embed(self):
        """
        Returns the embed shown at the start of the event
        --
        output:
        embed: interactions.Embed
        """
        nb_backed_cakes = db["baked_cakes"]["total"]

        embed = Embed(title="Happy birthday Pibot!", thumbnail=EmbedAttachment(url=Constants.PIBOU4BIRTHDAY_URL),
            description=f"Today is Pibot's 2 years anniversary!\nYour goal is to bake as much birthday cake as possible! To do so, deliveries will appear randomly through the day, bringing cake resources. You can collect these resources, but be quick, or the delivery person will get impatient and leave. You can use the `/role get Birthday Notifications` command to get notified when the delivery arrives.\n Each cake requires {', '.join(f'{nb} {e}' for e, nb in self.INGREDIENTS_PER_CAKE.items())} to be baked. Pibot will earn {self.REWARD_PER_CAKE} {Constants.PIFLOUZ_EMOJI} per cake, and get very happy!\n You can check your progress and inventory using the `/birthday` command.\n\nCakes baked so far: {nb_backed_cakes}",
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
        nb_cakes = db["baked_cakes"]["total"]
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
        delivery = db["last_birthday_delivery"]
        db["last_birthday_delivery"] = dict()

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
        db["last_birthday_delivery"] = {"id": int(msg.id), "qty": {e: nb for e, nb in zip(self.INGREDIENTS, qty)}}


    def bake_cakes(self, user_id):
        """
        Uses a user's inventory to bake some cakes
        --
        input:
        user_id: str (of an int)
        """
        inv = dict(db["birthday_event_ingredients"][user_id])

        nb_cakes = min(inv[e] // self.INGREDIENTS_PER_CAKE[e] for e in self.INGREDIENTS)

        for ingredient in self.INGREDIENTS:
            inv[ingredient] -= nb_cakes * self.INGREDIENTS_PER_CAKE[ingredient]

        db["baked_cakes"]["total"] += nb_cakes
        db["baked_cakes"][user_id] += nb_cakes
        db["birthday_event_ingredients"][user_id] = inv


    async def update_birthday_message(self, bot):
        """
        Updates the birthday message with the amount of baked cakes
        --
        input:
        bot: interactions.Client
        """
        if "current_event_passive_message_id" not in db.keys():
            return

        channel = await bot.fetch_channel(db["out_channel"])
        embed = self.get_start_embed()
        message = await channel.fetch_message(db["current_event_passive_message_id"])
        await message.edit(embed=embed)


    def to_str(self):
        return f"{__name__}.{Birthday_event.__name__}()"


class Birthday_raffle_event(Event):
    """
    A special raffle event where you don't have to spend money
    """
    button_id = "🎟️"


    def __init__(self, reward):
        self.reward = reward


    async def on_begin(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])

        # Starting new raffle
        embed = await self.get_embed_raffle(bot)
        button = self.get_component()
        message = await out_channel.send(embed=embed, components=button)
        return message


    async def on_end(self, bot):
        if "out_channel" not in db.keys():
            return

        out_channel = await bot.fetch_channel(db["out_channel"])
        participation = list(db["birthday_raffle_participation"])

        # Computing the winner for the last raffle
        if len(participation) > 3:

            winner1 = random.choice(participation)
            participation.remove(winner1)
            winner2 = random.choice(participation)
            participation.remove(winner2)
            winner3 = random.choice(participation)

            db["birthday_raffle_participation"] = []

            prize1 = round(self.reward * .5)
            prize2 = round(self.reward * .3)
            prize3 = round(self.reward * .2)

            piflouz_handlers.update_piflouz(winner1, qty=prize1, check_cooldown=False)
            piflouz_handlers.update_piflouz(winner2, qty=prize2, check_cooldown=False)
            piflouz_handlers.update_piflouz(winner3, qty=prize3, check_cooldown=False)

            message = f"The birthday raffle is over! <@{winner1}> won {prize1} {Constants.PIFLOUZ_EMOJI}, <@{winner2}> won {prize2} {Constants.PIFLOUZ_EMOJI} and <@{winner3}> won {prize3} {Constants.PIFLOUZ_EMOJI}!"

            await out_channel.send(message)


    def to_str(self):
        return f"{__name__}.{type(self).__name__}({self.reward})"


    async def update_raffle_message(self, bot):
        """
        Updates the birthday raffle message with the participants
        --
        input:
        bot: interactions.Client
        """
        if "current_event_passive_message_id" not in db.keys():
            return

        channel = await bot.fetch_channel(db["out_channel"])
        embed = await self.get_embed_raffle(bot)
        button = self.get_component()
        raffle_message = await channel.fetch_message(db["current_event_passive_message_id"])
        await raffle_message.edit(embed=embed, components=button)


    async def get_embed_raffle(self, bot):
        """
        Returns an embed message corresponding to the raffle message
        --
        input:
        bot: interactions.Client
        """
        desc = f"Today's raffle is special! Click the button below to participate, and it's completely free! {self.reward} {Constants.PIFLOUZ_EMOJI} are at stake! The first winner will earn 50%, the second one will get 30% and the third winner will get 20%!"

        embed = Embed(title="Birthday Special Raffle!", description=desc, color=Color.random(), thumbnail=EmbedAttachment(url=Constants.PIBOU4BIRTHDAY_URL))

        if "birthday_raffle_participation" in db.keys() and len(db["birthday_raffle_participation"]) > 0:
            participation = list(db["birthday_raffle_participation"])
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
        res = Button(style=ButtonStyle.SECONDARY, custom_id=self.button_id, emoji=self.button_id)
        return res
