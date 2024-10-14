import functools
from interactions import Button, ButtonStyle, IntervalTrigger, auto_defer, component_callback, listen
from random import random, randrange, shuffle
import requests
from unidecode import unidecode

from constant import Constants
from custom_task_triggers import TaskCustom as Task
from database import db
import events
from piflouz_generated import PiflouzSource, add_to_stat
import piflouz_handlers
from random_pool import RandomPoolTable
import user_profile
import utils


@Task.create(IntervalTrigger(seconds=30))
async def pibox_task(bot):
    """
    Generates pibox randomly

    Parameters
    ----------
    bot (interactions.Client)
    """
    event = events.get_event_object(events.EventType.PASSIVE)
    drop_rate_multiplier = 1

    if event is not None:
        powerups_list = event.get_powerups()
        drop_rate_multiplier = functools.reduce(lambda accu, powerup: accu * powerup.get_pibox_rate_multiplier_value(), powerups_list, drop_rate_multiplier)

    table = RandomPoolTable.compute_pibox_table()

    for pool, drop_rate in table.pools:
        drop_rate = min(1, drop_rate * drop_rate_multiplier)

        if random() < drop_rate:
            cls = eval(pool.get_random())
            pibox = await cls.new(bot)
            if pibox is not None:
                add_box_to_db(pibox)


def get_all_pibox():
    """
    Returns a dict containing all currently active pibox

    Returns
    -------
    res (dict (Element_dict))
    """
    return db["pibox"]


async def load_all_pibox(bot):
    """
    Loads all the piboxes from the database

    Parameters
    ----------
    bot(interactions.Client)
    """
    for _, data in get_all_pibox().items():
        await Pibox.from_str(data, bot)  # This will register the listeners


def add_box_to_db(pibox):
    """
    Adds a pibox to the database

    Parameters
    ----------
    pibox(Pibox)
    """
    if pibox is not None:
        get_all_pibox()[str(pibox.message_id)] = pibox.to_str()


class Pibox:
    """
    Abstract base class for piboxes
    """

    @staticmethod
    def get_new_id():
        """
        Gets a new unique id for a pibox

        Returns
        -------
        int
        """
        id = db["last_pibox_id"]
        db["last_pibox_id"] += 1
        return id

    @staticmethod
    async def new(bot):
        """
        Creates a new pibox, spawns it and returns it

        Parameters
        ----------
        bot (interactions.Client)

        Returns
        -------
        Pibox:
            The new pibox, None if the pibox could not be created
        """
        return None

    async def _register_listeners(self, bot):
        """
        Registers the listeners used to know when to update the pibox

        Parameters
        ----------
        bot (interactions.Client)
        """
        pass

    async def _remove_listeners(self, bot):
        """
        Removes all the listeners used by the pibox

        Parameters
        ----------
        bot (interactions.Client)
        """
        pass

    async def _on_fail(self, bot, user_id):
        """
        Called when someone tries to get a pibox but fails

        Parameters
        ----------
        bot (interactions.Client)
        user_id (int/str)
        """
        pass

    async def _on_success(self, bot, user_id):
        """
        Called when someone gets a pibox successfully

        Parameters
        ----------
        bot (interactions.Client)
        user_id (int/str)
        """
        pass

    def to_str(self):
        """
        Transforms the pibox into a string that can recrete the object using `eval()`

        Returns
        -------
        str
        """
        return dict()

    @staticmethod
    async def from_str(data, bot):
        """
        Creates a Pibox object from a string

        Parameters
        ----------
        data (str)
        bot (interactions.Client)

        Returns
        -------
        Pibox
            Corresponding Pibox object
        """
        res = eval(data)
        await res._register_listeners(bot)
        return res


class QuickReactPibox(Pibox):
    """
    The original pibox, where the user has to react to a message to get the pibox
    """

    POSSIBLE_EMOJI_ID_SOLUTIONS = Constants.EMOJI_IDS_FOR_PIBOX
    POSSIBLE_EMOJI_NAME_SOLUTIONS = Constants.EMOJI_NAMES_FOR_PIBOX

    def __init__(self, amount, custom_message=None, is_piflouz_generated=False, is_giveaway=False, steal_reward=False,
                 is_opposite=False, nb_reward=1, already_claimed=None, message_id=None, emoji_id_solution=None, id=None):
        self.amount = amount
        self.custom_message = custom_message                # Custom message to display at the end of the pibox message
        self.is_piflouz_generated = is_piflouz_generated    # Whether the piflouz were generated from scratch (contrary to giveaway for instance)
        self.is_giveaway = is_giveaway                      # Whether the pibox comes from a /giveaway command
        self.steal_reward = steal_reward                    # Whether the bot steals the reward from the user
        self.is_opposite = is_opposite                      # Whether the user has to react with the wrong emoji to get the pibox
        self.nb_reward = nb_reward                          # How many users can claim the pibox
        self.already_claimed = already_claimed or []        # List of users who already claimed the pibox
        self.message_id = message_id
        self.emoji_id_solution = emoji_id_solution
        self.id = id if id is not None else Pibox.get_new_id()

    @staticmethod
    async def new(bot, custom_message=None, is_piflouz_generated=True, is_giveaway=False, steal_reward=False, is_opposite=False, nb_reward=1, sender_id=None, piflouz_quantity=None):
        # Choose a random emoji
        index = randrange(len(QuickReactPibox.POSSIBLE_EMOJI_ID_SOLUTIONS))
        emoji_id = QuickReactPibox.POSSIBLE_EMOJI_ID_SOLUTIONS[index]
        emoji_name = QuickReactPibox.POSSIBLE_EMOJI_NAME_SOLUTIONS[index]
        emoji = f"<:{emoji_name}:{emoji_id}>"

        if piflouz_quantity is None:
            # Compute the maximum amount of piflouz that can be given
            max_size = Constants.MAX_PIBOX_AMOUNT
            event = events.get_event_object(events.EventType.PASSIVE)

            if event is not None:
                powerups_list = event.get_powerups()
                max_size = round(functools.reduce(lambda accu, powerup: accu * powerup.get_pibox_reward_multiplier_value(), powerups_list, max_size))

            piflouz_quantity = randrange(max_size)

        if is_giveaway:
            if not piflouz_handlers.update_piflouz(sender_id, qty=-piflouz_quantity * nb_reward, check_cooldown=False):
                return None  # Not enough piflouz to give

            if str(sender_id) != str(bot.user.id):
                profile = user_profile.get_profile(sender_id)
                profile["donation_balance"] += piflouz_quantity

            await utils.update_piflouz_message(bot)
            bot.dispatch("giveaway_successful", sender_id)

        role = await bot.guilds[0].fetch_role(Constants.PIBOX_NOTIF_ROLE_ID)

        text_output = f"{role.mention} Be Fast! First to react with {emoji} will get {piflouz_quantity} {Constants.PIFLOUZ_EMOJI}!"
        if custom_message is not None:
            text_output += " " + custom_message

        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.send(text_output)

        res = QuickReactPibox(piflouz_quantity, custom_message, is_piflouz_generated=is_piflouz_generated, is_giveaway=is_giveaway, steal_reward=steal_reward, is_opposite=is_opposite, nb_reward=nb_reward, message_id=message.id, emoji_id_solution=emoji_id)
        if res is not None: await res._register_listeners(bot)

        return res

    async def _on_message_reaction_add(self, reac_event, bot):
        """
        Listener function executed when a reaction is added to a message

        Parameters
        ----------
        reac_event (interactions.MessageReactionAdd)
        bot (interactions.Client)
        """
        message_id = reac_event.message.id
        if str(message_id) != str(self.message_id): return  # Reaction on another message

        emoji = reac_event.reaction.emoji
        user = reac_event.author

        if str(user.id) in self.already_claimed: return  # User already claimed the pibox

        if (emoji.id is not None and int(emoji.id) == self.emoji_id_solution) == (not self.is_opposite):
            await self._on_success(bot, user.id)
        else:
            await self._on_fail(bot, user.id)

    async def _register_listeners(self, bot):
        @listen()
        async def on_message_reaction_add(reac_event):
            await self._on_message_reaction_add(reac_event, bot)

        bot.add_listener(on_message_reaction_add)
        self.listener = on_message_reaction_add

    async def _remove_listeners(self, bot):
        bot.listeners["message_reaction_add"].remove(self.listener)

    async def _on_fail(self, bot, user_id):
        bot.dispatch("pibox_failed", user_id, self.amount)

    def _get_final_message(self, id_winner, bot):
        """
        Generates the string to be displayed when the pibox is won

        Parameters
        ----------
        id_winner : str/int
            user id of the winner
        bot : interactions.Client
        """
        res = ""

        users = [f"<@{id}>" for id in self.already_claimed]
        if len(users) > 1: users[-1] = f"and {users[-1]}"
        users = ", ".join(users)

        # All rewards have been claimed
        if len(self.already_claimed) == self.nb_reward:
            res = f"{users} all won {self.amount} {Constants.PIFLOUZ_EMOJI} from a pibox!"
            if self.custom_message is not None: res += " " + self.custom_message

        else:
            emoji_id_index = QuickReactPibox.POSSIBLE_EMOJI_ID_SOLUTIONS.index(self.emoji_id_solution)
            emoji_name = QuickReactPibox.POSSIBLE_EMOJI_NAME_SOLUTIONS[emoji_id_index]
            emoji = f"<:{emoji_name}:{self.emoji_id_solution}>"

            res = f"<@&{Constants.PIBOX_NOTIF_ROLE_ID}> Be Fast! First to react with {emoji} will get {self.amount} {Constants.PIFLOUZ_EMOJI}!"
            if self.custom_message is not None: res += " " + self.custom_message

            nb_claim_left = self.nb_reward - len(self.already_claimed)
            res += f"\n{users} already claimed the pibox, but it can be claimed {nb_claim_left} more time{"s" if nb_claim_left > 1 else ""}!"

        return res

    async def _on_success(self, bot, user_id):
        self.already_claimed.append(str(user_id))

        # Remove the pibox from the database, or update it if there are still rewards to claim
        if len(self.already_claimed) >= self.nb_reward:
            del get_all_pibox()[str(self.message_id)]
            await self._remove_listeners(bot)
        else:
            get_all_pibox()[str(self.message_id)] = self.to_str()  # Update the pibox in the database

        # Update the piflouz balance
        if self.steal_reward:
            piflouz_handlers.update_piflouz(bot.user.id, self.amount, False)

            # `update_piflouz` can't go below 0, so we have to remove at most the amount of piflouz the user has
            profile = user_profile.get_profile(user_id)
            taken = min(profile["piflouz_balance"], self.amount)
            piflouz_handlers.update_piflouz(user_id, -taken, False)
        else:
            piflouz_handlers.update_piflouz(user_id, self.amount, False)

        # Edit the message to show the winner
        new_text_message = self._get_final_message(user_id, bot)
        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.fetch_message(self.message_id)
        await message.edit(content=new_text_message)

        # Add to stats
        if self.is_piflouz_generated and not self.steal_reward:
            add_to_stat(self.amount, PiflouzSource.PIBOX)

        # Check if it was a giveaway
        elif self.is_giveaway and str(user_id) != str(bot.user.id) and not self.steal_reward:
            id = str(user_id)
            profile = user_profile.get_profile(id)
            profile["donation_balance"] -= self.amount

        await utils.update_piflouz_message(bot)
        if not self.steal_reward: bot.dispatch("pibox_obtained", user_id, self.amount)

    def to_str(self):
        return f"QuickReactPibox({self.amount}, custom_message={f"'{self.custom_message}'" if self.custom_message is not None else None}, is_piflouz_generated={self.is_piflouz_generated}, is_giveaway={self.is_giveaway}, steal_reward={self.steal_reward}, nb_reward={self.nb_reward}, already_claimed={self.already_claimed}, message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"


class QuickReactGiveawayPibox(QuickReactPibox):
    """
    Pibox generated using the `/giveaway` command
    """

    def __init__(self, amount, custom_message, message_id=None, emoji_id_solution=None, id=None):
        super().__init__(amount, custom_message=custom_message, is_piflouz_generated=False, is_giveaway=True, message_id=message_id, emoji_id_solution=emoji_id_solution, id=id)

    @staticmethod
    async def new(bot, sender_id, qty):
        custom_message = f"This is a gift from the great <@{sender_id}>, be sure to thank them!"
        return await QuickReactPibox.new(bot, custom_message, is_piflouz_generated=False, is_giveaway=True, sender_id=sender_id, piflouz_quantity=qty)

    def to_str(self):
        return f"QuickReactGiveawayPibox({self.amount}, custom_message={f"'{self.custom_message}'" if self.custom_message is not None else None}, message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"


class QuickReactPiboxMasterPibox(QuickReactPibox):
    """
    Pibox generated using the `/spawn-pibox` command
    """

    def __init__(self, amount, custom_message, message_id=None, emoji_id_solution=None, id=None):
        super().__init__(amount, custom_message=custom_message, is_piflouz_generated=True, is_giveaway=False, message_id=message_id, emoji_id_solution=emoji_id_solution, id=id)

    @staticmethod
    async def new(bot):
        custom_message = "It was spawned by the pibox master"
        qty = randrange(Constants.MAX_PIBOX_AMOUNT)
        return await QuickReactPibox.new(bot, custom_message, is_piflouz_generated=True, piflouz_quantity=qty)

    def to_str(self):
        return f"QuickReactPiboxMasterPibox({self.amount}, custom_message='{f"'{self.custom_message}'" if self.custom_message is not None else None}', message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"


class QuickReactByPibotPibox(QuickReactPibox):
    """
    Pibox generated uusing the bot's money
    """

    def __init__(self, amount, custom_message, message_id=None, emoji_id_solution=None, id=None):
        super().__init__(amount, custom_message, is_piflouz_generated=False, is_giveaway=True, message_id=message_id, emoji_id_solution=emoji_id_solution, id=id)

    @staticmethod
    async def new(bot):
        custom_message = f"{bot.user.mention} spawned it with its own {Constants.PIFLOUZ_EMOJI}!"
        return await QuickReactPibox.new(bot, custom_message, is_piflouz_generated=False, is_giveaway=True, sender_id=bot.user.id)

    def to_str(self):
        f"QuickReactByPibotPibox({self.amount}, custom_message='{f"'{self.custom_message}'" if self.custom_message is not None else None}', message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"


class TriviaPibox(Pibox):
    """
    Pibox where the user has to answer a trivia question to get the pibox
    """

    def __init__(self, question, answers, correct_answer, amount, message_id, failed_indices=None, failed_users=None, id=None):
        self.question = question
        self.answers = answers
        self.correct_answer = correct_answer
        self.amount = amount
        self.message_id = message_id
        self.id = id if id is not None else Pibox.get_new_id()
        self.failed_indices = failed_indices if failed_indices is not None else set()
        self.failed_users = failed_users if failed_users is not None else []

    @staticmethod
    def fetch_question():
        """
        Gets a new trivia question/answers

        Returns
        -------
        str:
            The question
        List[str]:
            The answers
        str:
            The correct answer
        """
        done = False
        while not done:
            r = requests.get(url="https://the-trivia-api.com/v2/questions", params={"regions": ["FR"], "limit": 1}).json()[0]
            question = r["question"]["text"]
            answer = r["correctAnswer"]
            all_answers = r["incorrectAnswers"] + [answer]
            shuffle(all_answers)
            done = not any([len(a) > 80 for a in all_answers])  # Button labels can't be too long

        return question, all_answers, answer

    @staticmethod
    async def new(bot):
        question, all_answers, answer = TriviaPibox.fetch_question()
        pibox_id = Pibox.get_new_id()

        # Computing the maximum amount of piflouz that can be given
        max_size = Constants.MAX_PIBOX_AMOUNT
        event = events.get_event_object(events.EventType.PASSIVE)
        if event is not None:
            powerups_list = event.get_powerups()
            max_size = round(functools.reduce(lambda accu, powerup: accu * powerup.get_pibox_reward_multiplier_value(), powerups_list, max_size))

        piflouz_quantity = randrange(max_size)

        components = []
        emojis = [":one:", ":two:", ":three:", ":four:"]
        for i, txt in enumerate(all_answers):
            components.append(Button(style=ButtonStyle.GRAY, label=txt, emoji=emojis[i], custom_id=f"pibox_{pibox_id}_{i}"))

        role = await bot.guilds[0].fetch_role(Constants.PIBOX_NOTIF_ROLE_ID)
        msg = f"{role.mention} Find the correct answer to earn {piflouz_quantity} {Constants.PIFLOUZ_EMOJI}!\n\n{question}"

        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.send(msg, components=components)

        pibox = TriviaPibox(question, all_answers, answer, piflouz_quantity, message.id, id=pibox_id)
        await pibox._register_listeners(bot)
        return pibox

    async def _on_button_click(self, ctx, index, bot):
        """
        Callback function executed when a button is clicked on the pibox message

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        index (int)
            Which button was clicked
        bot (interactions.Client)
        """
        if str(ctx.author.id) in self.failed_users:
            await ctx.send("You already failed this pibox", ephemeral=True)
            return

        if self.answers[index] == self.correct_answer:
            await self._on_success(bot, ctx, ctx.author.id, index)
        else:
            await self._on_fail(bot, ctx, ctx.author.id, index)

    async def _register_listeners(self, bot):
        for i in range(4):
            await self._register_one_listener(bot, i)  # For some reason, if we declare the function inside the loop, they all use i = 3

    async def _register_one_listener(self, bot, i):
        @component_callback(f"pibox_{self.id}_{i}")
        @auto_defer(ephemeral=True)
        async def callback(ctx):
            await self._on_button_click(ctx, i, bot)

        bot.add_component_callback(callback)

    async def _remove_listeners(self, bot):
        for i in range(4):
            del bot._component_callbacks[f"pibox_{self.id}_{i}"]

    async def _on_fail(self, bot, ctx, user_id, index):
        self.failed_indices.add(index)
        self.failed_users.append(str(user_id))
        bot.dispatch("pibox_failed", user_id, self.amount)

        # update in the database
        get_all_pibox()[str(self.message_id)] = self.to_str()

        await self._update_message(bot)
        await ctx.send("Wrong answer!\nThanks to you, this answer has been eliminated, but the reward was reduced by 25%", ephemeral=True)

    async def _on_success(self, bot, ctx, user_id, index):
        reward = round(self.amount * (1 - len(self.failed_indices) / 4))
        piflouz_handlers.update_piflouz(user_id, reward, False)
        bot.dispatch("pibox_obtained", user_id, reward)

        del get_all_pibox()[str(self.message_id)]
        add_to_stat(reward, PiflouzSource.PIBOX)

        await ctx.send(f"Correct answer! You won {reward} {Constants.PIFLOUZ_EMOJI}!", ephemeral=True)

        components = ctx.message.components[0].components
        for i, component in enumerate(components):
            if i == index:
                component.style = ButtonStyle.GREEN
            else:
                component.style = ButtonStyle.RED
            component.disabled = True

        content = f"<@{user_id}> won {reward} {Constants.PIFLOUZ_EMOJI} ({len(self.failed_indices)} failed attempts) solving the following question:\n\n{self.question}"

        await ctx.message.edit(content=content, components=components)
        await utils.update_piflouz_message(bot)
        await self._remove_listeners(bot)

    async def _get_message(self, bot):
        """
        Returns the string to be sent in the message (when it's being updated)

        Parameters
        ----------
        bot (interactions.Client)

        Returns
        -------
        str
        """
        role = await bot.guilds[0].fetch_role(Constants.PIBOX_NOTIF_ROLE_ID)
        amount = round(self.amount * (1 - len(self.failed_indices) / 4))

        return f"{role.mention} Find the correct answer to earn {amount} {Constants.PIFLOUZ_EMOJI}, but you only have one chance!\nEach failed atempt will eliminate the answer and reduce the reward by 25% of the initial value\n\n{self.question}"

    async def _update_message(self, bot):
        """
        Updates the message with the new reward and the failed answers

        Parameters
        ----------
        bot : interactions.Client
        """
        content = await self._get_message(bot)

        components = []
        emojis = [":one:", ":two:", ":three:", ":four:"]
        for i, txt in enumerate(self.answers):
            color = ButtonStyle.GRAY if i not in self.failed_indices else ButtonStyle.RED
            disabled = i in self.failed_indices
            components.append(Button(style=color, label=txt, emoji=emojis[i], custom_id=f"pibox_{self.id}_{i}", disabled=disabled))

        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.fetch_message(self.message_id)
        await message.edit(content=content, components=components)

    def sanityze_str(self, s):
        res = unidecode(s).replace("'", r"\'").replace('"', r'\"')
        while r"\\" in res:
            res = res.replace(r"\\", "\\")
        return res

    def to_str(self):
        new_question = self.sanityze_str(self.question)
        new_answers = "[" + ",".join([f"'{self.sanityze_str(a)}'" for a in self.answers]) + "]"
        new_correct_answer = self.sanityze_str(self.correct_answer)
        return rf"TriviaPibox(question='{new_question}', answers={new_answers}, correct_answer='{new_correct_answer}', amount={self.amount}, message_id={self.message_id}, failed_indices={self.failed_indices}, failed_users={self.failed_users}, id={self.id})"


class HauntedPibox(QuickReactPibox):
    """
    A normal pibox, except that it has a chance to take piflouz from the user
    """

    STEAL_PROBA = Constants.HAUNTED_PIBOX_STEAL_PROBA

    def __init__(self, amount, steal_reward, message_id=None, emoji_id=None, id=None):
        super().__init__(amount, is_piflouz_generated=True, is_giveaway=False, steal_reward=steal_reward, message_id=message_id, emoji_id_solution=emoji_id, id=id)

    @staticmethod
    async def new(bot):
        # Choose a random emoji
        index = randrange(len(QuickReactPibox.POSSIBLE_EMOJI_ID_SOLUTIONS))
        emoji_id = QuickReactPibox.POSSIBLE_EMOJI_ID_SOLUTIONS[index]
        emoji_name = QuickReactPibox.POSSIBLE_EMOJI_NAME_SOLUTIONS[index]
        emoji = f"<:{emoji_name}:{emoji_id}>"

        # Compute the maximum amount of piflouz that can be given
        max_size = Constants.MAX_PIBOX_AMOUNT
        event = events.get_event_object(events.EventType.PASSIVE)
        if event is not None:
            powerups_list = event.get_powerups()
            max_size = round(functools.reduce(lambda accu, powerup: accu * powerup.get_pibox_reward_multiplier_value(), powerups_list, max_size))
        piflouz_quantity = randrange(max_size)

        role = await bot.guilds[0].fetch_role(Constants.PIBOX_NOTIF_ROLE_ID)
        text_output = f"{role.mention} Be Fast! First to react with {emoji} may get {piflouz_quantity} {Constants.PIFLOUZ_EMOJI}!"
        text_output += "\nTrick or treat! 🎃 This pibox may or may not be haunted 👻 Will you risk it for the biscuit? 🪦🧟"

        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.send(text_output)

        steal_reward = random() < HauntedPibox.STEAL_PROBA

        res = HauntedPibox(piflouz_quantity, steal_reward=steal_reward, message_id=message.id, emoji_id=emoji_id)
        if res is not None: await res._register_listeners(bot)

        return res

    def _get_final_message(self, id_winner, bot):
        if self.steal_reward:
            res = f"Trick! 🧛🕸️🔮{bot.user.mention} stole {self.amount} {Constants.PIFLOUZ_EMOJI} from <@{id_winner}>!"
        else:
            res = f"Treat! 🍬🍭🎃<@{id_winner}> won {self.amount} {Constants.PIFLOUZ_EMOJI} from a pibox!"
        return res

    def to_str(self):
        return f"HauntedPibox({self.amount}, steal_reward={self.steal_reward}, message_id={self.message_id}, emoji_id={self.emoji_id_solution}, id={self.id})"


class RafflePibox(QuickReactPibox):
    """
    A pibox that drops raffle tickets
    """

    MAX_AMOUNT = Constants.MAX_RAFFLE_PIBOX_AMOUNT

    def __init__(self, amount, message_id=None, emoji_id_solution=None, id=None):
        super().__init__(amount, message_id=message_id, emoji_id_solution=emoji_id_solution, id=id)

    @staticmethod
    async def new(bot):
        # Choose a random emoji
        index = randrange(len(RafflePibox.POSSIBLE_EMOJI_ID_SOLUTIONS))
        emoji_id = RafflePibox.POSSIBLE_EMOJI_ID_SOLUTIONS[index]
        emoji_name = RafflePibox.POSSIBLE_EMOJI_NAME_SOLUTIONS[index]
        emoji = f"<:{emoji_name}:{emoji_id}>"

        # Compute the maximum amount of piflouz that can be given
        amount = randrange(1, RafflePibox.MAX_AMOUNT + 1)

        role = await bot.guilds[0].fetch_role(Constants.PIBOX_NOTIF_ROLE_ID)
        text_output = f"{role.mention} Be Fast! First to react with {emoji} will get {amount} 🎟️!"

        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.send(text_output)

        res = RafflePibox(amount, message_id=message.id, emoji_id_solution=emoji_id)
        if res is not None: await res._register_listeners(bot)

        return res

    async def _deactivate(self, bot):
        """
        If no raffle is running, the pibox is deactivated

        Parameters
        ----------
        bot : interactions.Client
        """
        channel = await bot.fetch_channel(db["out_channel"])
        message = await channel.fetch_message(self.message_id)
        await message.edit(content="This pibox was for a previous raffle event, it is now closed")
        await self._remove_listeners(bot)

        # Remove the pibox from the database
        del get_all_pibox()[str(self.message_id)]

    async def _on_success(self, bot, user_id):
        current_event = events.get_event_object(events.EventType.PASSIVE)

        # Check if there is a raffle event running
        if not isinstance(current_event, events.RaffleEvent):
            await self._deactivate(bot)
            return

        # Update the raffle balance
        event_data = events.get_event_data(events.EventType.PASSIVE)
        event_data["tickets_from_pibox"] += self.amount
        user_id = str(user_id)
        if user_id not in event_data["participation"].keys():
            event_data["participation"][user_id] = 0
        event_data["participation"][user_id] += self.amount

        # Remove the pibox from the database
        del get_all_pibox()[str(self.message_id)]

        # Edit the message to show the winner
        new_text_message = f"<@{user_id}> won {self.amount} 🎟️ from a pibox!"
        out_channel = await bot.fetch_channel(db["out_channel"])
        message = await out_channel.fetch_message(self.message_id)
        await message.edit(content=new_text_message)

        await current_event.update_raffle_message(bot)
        bot.dispatch("pibox_obtained", user_id, self.amount)

        await self._remove_listeners(bot)

    async def _on_fail(self, bot, user_id):
        current_event = events.get_event_object(events.EventType.PASSIVE)

        # Check if there is a raffle event running
        if not isinstance(current_event, events.RaffleEvent):
            await self._deactivate(bot)
            return

        await super()._on_fail(bot, user_id)

    def to_str(self):
        return f"RafflePibox({self.amount}, message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"


class OppositeQuickReactPibox(QuickReactPibox):
    """
    A pibox where the user has to react with the wrong emoji to get the pibox
    """

    def __init__(self, amount, message_id=None, emoji_id=None, id=None):
        super().__init__(amount, is_piflouz_generated=True, is_giveaway=False, steal_reward=False, is_opposite=True, message_id=message_id, emoji_id_solution=emoji_id, id=id)

    @staticmethod
    async def new(bot):
        return await QuickReactPibox.new(bot, is_piflouz_generated=True, is_opposite=True)

    def to_str(self):
        return f"OppositeQuickReactPibox({self.amount}, message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"


class MultiClaimQuickReactPibox(QuickReactPibox):
    """
    A pibox where multiple users can claim the pibox
    """

    NB_REWARD = Constants.MULTI_CLAIM_PIBOX_NB_REWARD

    def __init__(self, amount, nb_reward, message_id=None, emoji_id=None, id=None):
        super().__init__(amount, is_piflouz_generated=True, nb_reward=nb_reward, message_id=message_id, emoji_id_solution=emoji_id, id=id)

    @staticmethod
    async def new(bot):
        return await QuickReactPibox.new(bot, is_piflouz_generated=True, nb_reward=MultiClaimQuickReactPibox.NB_REWARD)

    def to_str(self):
        return f"MultiClaimQuickReactPibox({self.amount}, nb_reward={self.nb_reward}, message_id={self.message_id}, emoji_id_solution={self.emoji_id_solution}, id={self.id})"
