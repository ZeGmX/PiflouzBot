from interactions import (
    Extension,
    OptionType,
    auto_defer,
    component_callback,
    slash_command,
    slash_option,
)

from constant import Constants
from embed_messages import get_embed_wordle
from events import (
    BirthdayEvent,
    BirthdayRaffleEvent,
    EventType,
    MatchesExpression,
    MoveMatchEvent,
    RaffleEvent,
    SubseqChallenge,
    SubseqChallengeEvent,
    WordleEvent,
    fetch_event_thread,
    get_event_data,
    get_event_object,
    update_events,
)
from piflouz_generated import PiflouzSource, add_to_stat
import piflouz_handlers
import utils
from wordle import Wordle


class CogEvent(Extension):
    """
    Cog containing all the interactions related to events
    --
    fields:
        bot: interactions.Client
    --
    Slash commands:
        /raffle
        /wordle guess
        /wordle status
        /birthday
        /match guess
        /subseq guess
    Components
        events.Birthday_raffle_event.BUTTON_ID
    """

    def __init__(self, bot):
        self.bot = bot

        # Register the button callbacks
        for emoji in BirthdayEvent.INGREDIENTS:
            self.bot.add_component_callback(self.callback_from_emoji(emoji))

    @slash_command(name="raffle", description="Buy raffle 🎟️ to test your luck ⚠️ Costs piflouz", scopes=Constants.GUILD_IDS)
    @slash_option(name="nb_tickets", description="How many tickets?", opt_type=OptionType.INTEGER, required=True, min_value=1)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def raffle_cmd(self, ctx, nb_tickets):
        """
        Callback for the /raffle command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        nb_tickets (int)
        """
        current_raffle, data = await self.check_event(EventType.PASSIVE, RaffleEvent, ctx)

        price = nb_tickets * current_raffle.ticket_price
        user_id = str(ctx.author.id)

        # user doesn't have enough money
        await utils.custom_assert(piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False), f"You don't have enough money to buy {nb_tickets} tickets", ctx)

        if user_id not in data["participation"].keys():
            data["participation"][user_id] = 0
        data["participation"][user_id] += nb_tickets

        await ctx.send(f"Successfully bought {nb_tickets} tickets", ephemeral=True)
        await current_raffle.update_raffle_message(self.bot)
        await utils.update_piflouz_message(self.bot)
        self.bot.dispatch("raffle_participation_successful", ctx.author.id, nb_tickets)

    @slash_command(name="wordle", description="TBD", sub_cmd_name="guess", sub_cmd_description="Take a guess on the word the day")
    @slash_option(name="word", description="5-letter english word", opt_type=OptionType.STRING, required=True, min_length=Wordle.WORD_SIZE, max_length=Wordle.WORD_SIZE)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def wordle_guess_cmd(self, ctx, word):
        """
        Callback for the /wordle guess command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        word (str)
        """
        current_wordle, data = await self.check_event(EventType.CHALLENGE, WordleEvent, ctx)
        wordle = Wordle(data["word"])

        user_id = str(int(ctx.author.id))
        if user_id not in data["guesses"].keys():
            data["guesses"][user_id] = []

        guesses = data["guesses"][user_id]
        word = word.lower()
        await utils.custom_assert(len(guesses) < wordle.NB_ATTEMPTS, "The maximum amount of attempts has been reached!", ctx)
        await utils.custom_assert(wordle.is_valid(word), "This is not a valid word!", ctx)
        await utils.custom_assert(len(guesses) == 0 or wordle.solution != guesses[-1], "You already won!", ctx)

        guesses.append(word)  # automatically updates the db

        header_str = "\n".join(wordle.guess(w) for w in guesses)

        if guesses[-1] == wordle.solution:  # When the wordle is succesfully completed.
            progress = 1 + (1 - len(guesses)) / (wordle.NB_ATTEMPTS - 1)
            reward = round(current_wordle.min_reward + progress * (current_wordle.max_reward - current_wordle.min_reward))

            results = "\n".join([wordle.guess(word) for word in guesses])
            is_hard_solution = wordle.is_hard_solution(guesses)
            if is_hard_solution:
                reward += current_wordle.hard_mode_bonus
                header_str += (
                    f"\n\nCongratulations, you found the word of the day with {len(guesses)}/{wordle.NB_ATTEMPTS} attempts!\n"
                    + "This was a hard mode solution, well done!\n"
                    + f"You earned {reward}{Constants.PIFLOUZ_EMOJI}"
                )
                announcement_msg = f"{ctx.author.mention} solved today's Wordle in hard mode ({len(guesses)}/{wordle.NB_ATTEMPTS})!\n{results}"
            else:
                header_str += (
                    f"\n\nCongratulations, you found the word of the day with {len(guesses)}/{wordle.NB_ATTEMPTS} attempts!\n"
                    + f"You earned {reward}{Constants.PIFLOUZ_EMOJI}"
                )
                announcement_msg = f"{ctx.author.mention} solved today's Wordle ({len(guesses)}/{wordle.NB_ATTEMPTS})!\n{results}"
            piflouz_handlers.update_piflouz(user_id, reward, check_cooldown=False)

            thread = await fetch_event_thread(self.bot, EventType.CHALLENGE)
            await thread.send(announcement_msg)

            add_to_stat(reward, PiflouzSource.EVENT)
            await utils.update_piflouz_message(self.bot)

        elif len(guesses) == wordle.NB_ATTEMPTS:
            header_str += f"\n\nOuch, you failed :(\nThe answer was: **{wordle.solution}**"

        await self.send_wordle_embed(ctx, wordle, guesses, header_str)

    @slash_command(name="wordle", description="TBD", sub_cmd_name="status", sub_cmd_description="Check how your wordle is going")
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def wordle_status_cmd(self, ctx):
        """
        Callback for the /wordle status command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        """
        _, data = await self.check_event(EventType.CHALLENGE, WordleEvent, ctx)
        wordle = Wordle(data["word"])

        user_id = str(int(ctx.author.id))
        await utils.custom_assert(user_id in data["guesses"].keys(), "You haven't participated to today's wordle yet!", ctx)

        guesses = data["guesses"][user_id]

        await utils.custom_assert(len(guesses) > 0, "You haven't participated to today's wordle yet!", ctx)

        header_str = "\n".join(wordle.guess(w) for w in guesses)
        header_str += f"\n{len(guesses)}/{wordle.NB_ATTEMPTS}"

        if guesses[-1] == wordle.solution:
            header_str += "\nYou won!"
        elif len(guesses) == wordle.NB_ATTEMPTS:
            header_str += f"\nYou lost :( The correct word was {wordle.solution}"

        await self.send_wordle_embed(ctx, wordle, guesses, header_str)

    async def send_wordle_embed(self, ctx, wordle, guesses, header_str):
        """
        Generates the wordle image, host it on imgur and send it as an interaction response

        Parameters
        ----------
        ctx (interactions.SlashContext)
        wordle (wordle.Wordle)
        guesses (List[str])
        header_str (str)
        """
        user_id = ctx.author.id
        embed = await get_embed_wordle(wordle.solution, guesses, header_str, user_id)
        await ctx.send(embed=embed, ephemeral=True)

    async def birthday_ingredient_button_callback(self, ctx, emoji):
        """
        callback for the birthday event buttons with the given emoji

        Parameters
        ----------
        ctx (interactions.SlashContext)
        emoji (str)
        """
        user_id = str(ctx.author.id)

        event = get_event_object(EventType.PASSIVE)
        data = get_event_data(event)

        if user_id not in data["ingredients"].keys():
            data["ingredients"][user_id] = {e: 0 for e in BirthdayEvent.INGREDIENTS}
            data["ingredients"][user_id]["last_react_time"] = -1
        if user_id not in data["baked_cakes"].keys():
            data["baked_cakes"][user_id] = 0

        date = int(ctx.message.timestamp.timestamp())
        await utils.custom_assert(data["ingredients"][user_id]["last_react_time"] != date, "You already took one ingredient from this delivery!", ctx)

        qty = data["last_delivery"]["qty"][emoji]
        data["ingredients"][user_id]["last_react_time"] = date
        data["ingredients"][user_id][emoji] += qty

        event.bake_cakes(user_id)

        res = self.get_birthday_str(user_id)
        await ctx.send(res, ephemeral=True)
        await event.update_birthday_message(self.bot)

    def callback_from_emoji(self, emoji):
        """
        Returns the callback function for the birthday event buttons with the given emoji

        Parameters
        ----------
        emoji (str)

        Returns
        -------
        interactions.ComponentCommand
        """
        @component_callback(emoji)
        @auto_defer(ephemeral=True)
        async def callback(ctx):
            await self.birthday_ingredient_button_callback(ctx, emoji)
        return callback

    @slash_command(name="birthday", description="Check how your baking skills are going", scopes=Constants.GUILD_IDS, options=[])
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def birthday_cmd(self, ctx):
        """
        Callback for the /birthday command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        """
        _, data = await self.check_event(EventType.PASSIVE, BirthdayEvent, ctx)
        user_id = str(ctx.author.id)

        if user_id not in data["ingredients"].keys():
            data["ingredients"][user_id] = {e: 0 for e in BirthdayEvent.INGREDIENTS}
            data["ingredients"][user_id]["last_react_time"] = -1
        if user_id not in data["baked_cakes"].keys():
            data["baked_cakes"][user_id] = 0

        res = self.get_birthday_str(user_id)
        await ctx.send(res, ephemeral=True)

    def get_birthday_str(self, user_id):
        """
        Returns a string detailing the inventory of a user

        Parameters
        ----------
        user_id (str (of an int))

        Returns
        -------
        res (str)
        """
        res = "Your ingredients: \n"
        data = get_event_data(EventType.PASSIVE)
        for e in BirthdayEvent.INGREDIENTS:
            res += f"• {e}: {data["ingredients"][user_id][e]}\n"
        res += f"\nYou baked {data["baked_cakes"][user_id]} cakes!"
        return res

    @component_callback(BirthdayRaffleEvent.BUTTON_ID)
    @auto_defer(ephemeral=True)
    async def birthday_raffle_register(self, ctx):
        """
        Callback for the button to register to the birthday raffle

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        """
        current_bday_raffle, data = await self.check_event(EventType.PASSIVE, BirthdayRaffleEvent, ctx)
        user_id = str(ctx.author.id)
        await utils.custom_assert(user_id not in data["participation"], "You are already registered!", ctx)
        data["participation"].append(user_id)

        await current_bday_raffle.update_raffle_message(self.bot)

        await ctx.send("You are now registered!", ephemeral=True)

    @slash_command(name="match", description="TBD", sub_cmd_name="guess", sub_cmd_description="Take a guess on the match event of the day", scopes=Constants.GUILD_IDS)
    @slash_option(name="guess", description="Your guessed equation", opt_type=OptionType.STRING, required=True)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def match_guess_cmd(self, ctx, guess):
        """
        Callback for the /match guess command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        guess (str)
        """
        current_match, data = await self.check_event(EventType.CHALLENGE, MoveMatchEvent, ctx)
        user_id = str(ctx.author.id)

        await utils.custom_assert(user_id not in data["completed"].keys(), "You already won the event!", ctx)

        expression = MatchesExpression(s=guess)
        await utils.custom_assert(expression.is_valid(), "This is not a valid equation!", ctx)
        await utils.custom_assert(expression.is_correct(), "This equation is incorrect!", ctx)
        await utils.custom_assert(expression.str in data["all_solutions"], "This equation is not one of my solution, try again!", ctx)

        data["completed"][user_id] = expression.str

        piflouz_handlers.update_piflouz(user_id, current_match.reward, check_cooldown=False)
        await ctx.send(f"Congratulations, this is correct! You earned {current_match.reward} {Constants.PIFLOUZ_EMOJI}", ephemeral=True)

        thread = await fetch_event_thread(self.bot, EventType.CHALLENGE)
        await thread.send(f"{ctx.author.mention} solved today's match event!")

        add_to_stat(current_match.reward, PiflouzSource.EVENT)
        await utils.update_piflouz_message(self.bot)

    @slash_command(name="subseq", description="TBD", sub_cmd_name="guess", sub_cmd_description="Take a guess on the subsequence event of the day", scopes=Constants.GUILD_IDS)
    @slash_option(name="guess", description="Your guessed word", opt_type=OptionType.STRING, required=True)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def subseq_guess_cmd(self, ctx, guess):
        """
        Callback for the `/subseq guess` command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        guess (str)
        """
        current_subseq, data = await self.check_event(EventType.CHALLENGE, SubseqChallengeEvent, ctx)
        user_id = str(ctx.author.id)

        if user_id not in data["completed"].keys():
            data["completed"][user_id] = {"default": False, "projection": False, "intermediate": False, "both": False, "guesses": []}

        comp = data["completed"][user_id]
        proposed_words = set(comp["guesses"])
        await utils.custom_assert(len(proposed_words) < current_subseq.max_rewardable_words or any(not comp[key] for key in ["default", "projection", "intermediate", "both"]), "You already completed the event!", ctx)

        s = SubseqChallenge(subseq=data["subseq"])
        guess_clean = SubseqChallenge._clean_word(guess)
        await utils.custom_assert(guess_clean not in comp["guesses"], "You already proposed this word!", ctx)
        await utils.custom_assert(s.check_default(guess_clean), "Incorrect!", ctx)

        # Checks which levels are now completed
        comp["guesses"].append(guess_clean)
        earned = 0

        success_projection = s.check_projection(guess_clean)
        success_intermediate = s.check_with_intermediate(guess_clean)

        if not comp["default"]:
            comp["default"] = True
            earned += current_subseq.reward_default

        if success_projection and not comp["projection"]:
            comp["projection"] = True
            earned += current_subseq.reward_bonus1

        if success_intermediate and not comp["intermediate"]:
            comp["intermediate"] = True
            earned += current_subseq.reward_bonus2

        if success_projection and success_intermediate and not comp["both"]:
            comp["both"] = True
            earned += current_subseq.reward_bonus3

        if len(proposed_words) < current_subseq.max_rewardable_words:
            earned += current_subseq.reward_per_word

        piflouz_handlers.update_piflouz(user_id, earned, check_cooldown=False)

        message = f"Congratulations, this is correct! You earned {earned} {Constants.PIFLOUZ_EMOJI}.\n\nHere is your progress:\n\
• [Level 1]: {"✅" if comp["default"] else "❌"}\n\
• [Level 2]: {"✅" if comp["projection"] else "❌"}\n\
• [Level 3]: {"✅" if comp["intermediate"] else "❌"}\n\
• [Level 4]: {"✅" if comp["both"] else "❌"}\n\
• Rewarded attempts: {min(len(proposed_words) + 1, current_subseq.max_rewardable_words)} / {current_subseq.max_rewardable_words}"

        await ctx.send(message, ephemeral=True)

        thread = await fetch_event_thread(self.bot, EventType.CHALLENGE)
        output_message = f"{ctx.author.mention} solved today's subsequence event at level "

        solved = [comp["default"], comp["projection"], comp["intermediate"], comp["both"]]
        solved = [str(i + 1) for i, s in enumerate(solved) if s]
        output_message += ", ".join(solved) + "!"

        if len(proposed_words) == 0:
            msg = await thread.send(output_message)
            data["msg_id"][user_id] = int(msg.id)
        else:
            msg = await thread.fetch_message(data["msg_id"][user_id])
            await msg.edit(content=output_message)

        add_to_stat(earned, PiflouzSource.EVENT)
        await utils.update_piflouz_message(self.bot)

    @slash_command(name="restart-events", description="Restart the events", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def restart_event(self, ctx):
        """
        Callback for the `/restart-events` command

        Parameters
        ----------
        ctf (interactions.SlashContext)
        """
        await update_events(self.bot)
        await ctx.send("Done!", ephemeral=True)

    @staticmethod
    async def check_event(event_type, event_cls, ctx):
        """
        Verifies that the current event is of the given type

        Parameters
        ----------
        event_type (int (Event_type))
        event_cls (class (Event subclass))
        ctx (interactions.SlashContext)

        Returns
        -------
        current_event (Event)
        data (dict (Element_dict))
        """
        current_event = get_event_object(event_type)

        type_str = "challenge" if event_type == EventType.CHALLENGE else "passive"
        await utils.custom_assert(current_event is not None, f"No current {type_str} event registered", ctx)
        await utils.custom_assert(isinstance(current_event, event_cls), "The current event is not of this type", ctx)

        data = get_event_data(current_event)

        return current_event, data
