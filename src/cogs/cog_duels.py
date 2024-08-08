from interactions import (
    Button,
    ButtonStyle,
    Extension,
    OptionType,
    SlashCommandChoice,
    auto_defer,
    component_callback,
    slash_command,
    slash_option,
)
from interactions.client.utils.misc_utils import disable_components
from interactions.ext.paginators import Paginator
from math import ceil

from constant import Constants
from duels import generate_duel, get_all_duels, recover_duel
import piflouz_handlers
import utils
from wordle import Wordle


class CogDuels(Extension):
    """
    Cog containing all the interactions related to duels
    --
    fields:
        bot: interactions.Client
    --
    Slash commands:
        /duel challenge
        /duel play Shifumi
        /duel status
    Components:
        duel_accept_button_name
        duel_deny_button_name
        duel_cancel_button_name
    """

    DUEL_ACCEPT_BUTTON_NAME = "duel_accept"
    DUEL_DENY_BUTTON_NAME = "duel_deny"
    DUEL_CANCEL_BUTTON_NAME = "duel_cancel"

    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="duel", description="TBD", sub_cmd_name="challenge", sub_cmd_description="Duel someone to earn piflouz!", scopes=Constants.GUILD_IDS)
    @slash_option(name="amount", description="How much do you want to bet?", required=True, opt_type=OptionType.INTEGER, min_value=1)
    @slash_option(name="duel_type", description="What game do you want to play?", required=True, opt_type=OptionType.STRING, choices=[
        SlashCommandChoice(name="Shifumi", value="Shifumi"),
        SlashCommandChoice(name="Wordle", value="Wordle")
    ])
    @slash_option(name="user", description="Who do you want to duel? Leave empty to duel anyone", required=False, opt_type=OptionType.USER)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def duel_challenge_cmd(self, ctx, amount, duel_type, user=None):
        """
        Callback for the duel challenge subcommand

        Parameters
        ----------
        ctx (interactions.SlashContext)
        amount (int):
            how many piflouz involved by both users
        duel_type (string):
            what kind of duel
        user (interactions.User):
            the person challenged
        """
        await utils.custom_assert(user is None or int(ctx.author.id) != int(user.id), "You can't challenge yourself!", ctx)

        await utils.custom_assert(piflouz_handlers.update_piflouz(ctx.author.id, qty=-amount, check_cooldown=False), "You don't have enough piflouz to do that", ctx)

        id_challenged = -1 if user is None else int(user.id)

        new_duel = generate_duel(int(ctx.author.id), id_challenged, amount, duel_type)

        mention = "anyone" if user is None else user.mention

        buttons = [
            Button(style=ButtonStyle.SUCCESS, label="", custom_id=CogDuels.DUEL_ACCEPT_BUTTON_NAME, emoji="✅"),
            Button(style=ButtonStyle.DANGER, label="", custom_id=CogDuels.DUEL_DENY_BUTTON_NAME, emoji="❎"),
            Button(style=ButtonStyle.SECONDARY, label="", custom_id=CogDuels.DUEL_CANCEL_BUTTON_NAME, emoji="🚫")
        ]

        channel = ctx.channel
        msg = await channel.send(f"{ctx.author.mention} challenged {mention} at {duel_type} betting {amount} {Constants.PIFLOUZ_EMOJI}! Click the green button below to accept or click the red one to deny. Click the gray one to cancel the challenge", components=buttons)

        opponent_name = "anyone" if user is None else user.username

        thread = await msg.create_thread(f"{duel_type} duel - {ctx.author.username} vs {opponent_name}")
        await thread.add_member(ctx.author.id)
        if user is not None: await thread.add_member(user.id)

        new_duel.edit("message_id", msg.id)
        new_duel.edit("thread_id", thread.id)
        get_all_duels().append(new_duel.get_dict())

        await ctx.send("Done!", ephemeral=True)

        await utils.update_piflouz_message(self.bot)
        self.bot.dispatch("duel_created", ctx.author.id, id_challenged, amount, duel_type)

    @component_callback(DUEL_ACCEPT_BUTTON_NAME)
    @auto_defer(ephemeral=True)
    async def duel_accept_button_callback(self, ctx):
        """
        Callback for the button that accepts a duel

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        """
        msg_id = int(ctx.message.id)

        # Finding the right duel
        duel_index = None
        all_duels = get_all_duels()
        for i, duel_dict in enumerate(all_duels):
            if duel_dict["message_id"] == msg_id:
                duel_index = i
                break

        await utils.custom_assert(duel_index is not None, "Could not find the duel", ctx)

        # Check that the duel is still available
        await utils.custom_assert(not duel_dict["accepted"], "This challenge has already been accepted", ctx)

        # Check that you are a target of the duel
        await utils.custom_assert(duel_dict["user_id2"] == int(ctx.author.id) or duel_dict["user_id2"] == -1, "You are not targeted by this duel", ctx)

        # Check that you are not the one who made the challenge
        await utils.custom_assert(duel_dict["user_id1"] != int(ctx.author.id), "You can't challenge yourself!", ctx)

        # Check the user has enough money
        await utils.custom_assert(piflouz_handlers.update_piflouz(ctx.author.id, qty=-duel_dict["amount"], check_cooldown=False), "You don't have enough piflouz to do that", ctx)

        all_duels[duel_index]["accepted"] = True
        all_duels[duel_index]["user_id2"] = int(ctx.author.id)

        duel_id = duel_dict["duel_id"]
        thread_id = duel_dict["thread_id"]

        thread = await self.bot.fetch_channel(thread_id)
        await thread.add_member(ctx.author.id)

        duel = recover_duel(all_duels[duel_index])

        await duel.on_accept(thread)
        await thread.edit(name=f"[Accepted] {thread.name}")

        components = disable_components(*ctx.message.components)
        await ctx.message.edit(components=components)
        await ctx.send("Done!", ephemeral=True)

        await utils.update_piflouz_message(self.bot)
        self.bot.dispatch("duel_accepted", int(ctx.author.id), duel_id)

    @component_callback(DUEL_DENY_BUTTON_NAME)
    @auto_defer(ephemeral=True)
    async def duel_deny_button_callback(self, ctx):
        """
        Callback for the button that denies a duel

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        """
        msg_id = int(ctx.message.id)

        # Finding the right duel
        duel_index = None
        all_duels = get_all_duels()
        for i, duel_dict in enumerate(all_duels):
            if duel_dict["message_id"] == msg_id:
                duel_index = i
                break

        await utils.custom_assert(duel_index is not None, "This duel does not exist", ctx)
        await utils.custom_assert(not duel_dict["accepted"], "You already accepted this challenge", ctx)
        await utils.custom_assert(duel_dict["user_id2"] != -1, "You can't deny a challenge at anyone", ctx)
        await utils.custom_assert(duel_dict["user_id2"] == int(ctx.author.id), "You are not targeted by this duel", ctx)

        # Give back the money to the challenger
        piflouz_handlers.update_piflouz(duel_dict["user_id1"], qty=duel_dict["amount"], check_cooldown=False)

        del all_duels[duel_index]

        thread_id = duel_dict["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        await thread.send(f"{ctx.author.mention} denied <@{duel_dict["user_id1"]}>'s challenge!")
        await thread.edit(name=f"[Denied] {thread.name}")
        await thread.archive()

        components = disable_components(*ctx.message.components)
        await ctx.message.edit(components=components)

        await ctx.send("Done", ephemeral=True)
        await utils.update_piflouz_message(self.bot)

    @component_callback(DUEL_CANCEL_BUTTON_NAME)
    @auto_defer(ephemeral=True)
    async def duel_cancel_button_callback(self, ctx):
        """
        Callback for the button that denies a duel

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        """
        msg_id = int(ctx.message.id)

        # Finding the right duel
        duel_index = None
        all_duels = get_all_duels()
        for i, duel_dict in enumerate(all_duels):
            if duel_dict["message_id"] == msg_id:
                duel_index = i
                break

        await utils.custom_assert(duel_index is not None, "This duel does not exist", ctx)
        await utils.custom_assert(not duel_dict["accepted"], "The duel was already accepted", ctx)
        await utils.custom_assert(duel_dict["user_id1"] == int(ctx.author.id), "You did not create this challenge", ctx)

        # Give back the money to the challenger
        piflouz_handlers.update_piflouz(ctx.author.id, qty=duel_dict["amount"], check_cooldown=False)

        del all_duels[duel_index]

        mention = "anyone" if duel_dict["user_id2"] == -1 else f"<@{duel_dict["user_id2"]}>"

        thread_id = duel_dict["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        await thread.send(f"{ctx.author.mention} cancelled their challenge to {mention}, what a loser")
        await thread.edit(name=f"[Cancelled] {thread.name}")
        await thread.archive()

        components = disable_components(*ctx.message.components)
        await ctx.message.edit(components=components)

        await ctx.send("Done!", ephemeral=True)
        await utils.update_piflouz_message(self.bot)

    @slash_command(name="duel", description="TBD", sub_cmd_name="status", sub_cmd_description="Check your ongoing duels", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    async def duel_status_cmd(self, ctx):
        """
        Callback for the duel subcommand command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        """
        my_duels = filter(lambda duel: int(ctx.author.id) in [duel["user_id1"], duel["user_id2"]] or duel["user_id2"] == -1, get_all_duels())

        msgs = []
        for duel_dict in my_duels:
            duel = recover_duel(duel_dict)
            mention = "anyone" if duel_dict["user_id2"] == -1 else f"<@{duel_dict["user_id2"]}>"
            s = f"• Id: {duel_dict["duel_id"]} - <@{duel_dict["user_id1"]}> vs {mention} - {duel_dict["duel_type"]} - {duel_dict["amount"]} {Constants.PIFLOUZ_EMOJI}\n{duel.status(int(ctx.author.id))}"

            # Link to the duel thread
            s += f"https://discord.com/channels/{ctx.guild.id}/{duel_dict["thread_id"]}\n"

            msgs.append(s)

        if len(msgs) == 0:
            await ctx.send("You have no ongoing duels", ephemeral=True)

        else:
            p = Paginator.create_from_list(client=self.bot, content=msgs, prefix="Here are your ongoing duels:\n")
            await p.send(ctx, ephemeral=True)

    async def checks_before_play(self, ctx, duel_type):
        """
        Checks if the duel can be played

        Parameters
        ----------
        ctx (interactions.SlashContext)
        duel_type (string):
            the type of duel

        Returns
        -------
        duel (duels.Duel)
        duel_index (int):
            the index of the duel in the db
        """
        thread = ctx.channel
        duel_index = None
        all_duels = get_all_duels()
        for i, duel_dict in enumerate(all_duels):
            if duel_dict["thread_id"] == int(thread.id):
                duel_index = i
                break

        await utils.custom_assert(duel_index is not None, "You are not inside an ongoing duel thread", ctx)
        await utils.custom_assert(duel_dict["accepted"], "This duel is not accepted yet", ctx)
        await utils.custom_assert(int(ctx.author.id) in [duel_dict["user_id1"], duel_dict["user_id2"]], "You are not part of this challenge", ctx)
        await utils.custom_assert(duel_dict["duel_type"] == duel_type, f"This duel is not a {duel_type} duel", ctx)

        if duel_dict["user_id1"] == ctx.author.id:
            await utils.custom_assert(duel_dict["result1"] is None, "You already finished playing!", ctx)
        else:
            await utils.custom_assert(duel_dict["result2"] is None, "You already finished playing!", ctx)

        return recover_duel(all_duels[duel_index]), duel_index

    @slash_command(name="duel", description="TBD", group_name="play", group_description="TBD", sub_cmd_name="shifumi", sub_cmd_description="Play shifumi!", scopes=Constants.GUILD_IDS)
    @slash_option(name="value", description="What do you want to play?", required=True, opt_type=OptionType.STRING, choices=[
        SlashCommandChoice(name="Rock", value="Rock"),
        SlashCommandChoice(name="Paper", value="Paper"),
        SlashCommandChoice(name="Scissors", value="Scissors")
    ])
    @auto_defer(ephemeral=True)
    async def duel_play_shifumi_cmd(self, ctx, value):
        """
        Callback for the `duel play shifumi` subcommand

        Parameters
        ----------
        ctx (interactions.SlashContext)
        value (string):
            the move played by the player
        """
        await self.global_duel_play(ctx, value, "Shifumi")

    @slash_command(name="duel", description="TBD", group_name="play", group_description="TBD", sub_cmd_name="wordle", sub_cmd_description="Play wordle!", scopes=Constants.GUILD_IDS)
    @slash_option(name="guess", description="What is your guessed word?", required=True, opt_type=OptionType.STRING, min_length=Wordle.WORD_SIZE, max_length=Wordle.WORD_SIZE)
    @auto_defer(ephemeral=True)
    async def duel_play_wordle_cmd(self, ctx, guess):
        """
        Callback for the `duel play wordle` subcommand

        Parameters
        ----------
        ctx (interactions.SlashContext)
        value (string):
            the move played by the player
        """
        await self.global_duel_play(ctx, guess, "Wordle")

    async def global_duel_play(self, ctx, value, duel_type):
        """
        Callback for `/duel play` for any type of duel

        Parameters
        ----------
        ctx (interactions.SlashContext)
        value (string):
            the action played by the player
        duel_type (string):
            the type of duel
        """
        # Processing the move
        duel, duel_index = await self.checks_before_play(ctx, duel_type)
        check, error_msg = duel.check_entry(value)
        await utils.custom_assert(check, error_msg, ctx)

        res = await duel.play(ctx.author.id, value)

        if res is None:
            await ctx.send("Done! Just wait for the other player to finish playing", ephemeral=True)
        else:
            await ctx.send(**res, ephemeral=True)

        # Processing the potential outcome of the duel
        if not duel.is_over(): return

        winner_loser = duel.get_winner_loser()
        thread = await self.bot.fetch_channel(duel.dict["thread_id"])

        qty = duel.dict["amount"]
        duel_type = duel.dict["duel_type"]

        del get_all_duels()[duel_index]

        # Tie, everyone gets all of their money back
        if not winner_loser:
            id1, id2 = duel.dict["user_id1"], duel.dict["user_id2"]
            piflouz_handlers.update_piflouz(id1, qty=qty, check_cooldown=False)
            piflouz_handlers.update_piflouz(id2, qty=qty, check_cooldown=False)

            await thread.send(f"<@{id1}> and <@{id2}> tied at {duel_type.lower()}! {duel.tie_str()} They both got their money back")
            await thread.edit(name=f"[Tie] {thread.name[11:]}")  # We remove the [Accepted]
            self.bot.dispatch("duel_tie", id1, id2, qty, duel_type)

            return

        # Someone won
        total_money = 2 * qty
        money_tax = ceil(total_money * Constants.DUEL_TAX_RATIO / 100)
        money_if_win = total_money - money_tax

        id_winner = winner_loser[0]
        id_loser = winner_loser[1]

        piflouz_handlers.update_piflouz(id_winner, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.user.id, qty=money_tax, check_cooldown=False)

        await thread.send(f"<@{id_winner}> won at {duel_type} against <@{id_loser}>, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! {duel.win_str(id_winner, id_loser)}")

        username = (await ctx.guild.fetch_member(id_winner)).username
        await thread.edit(name=f"[{username} won] {thread.name[11:]}")  # We remove the [Accepted]
        self.bot.dispatch("duel_won", id_winner, id_loser, qty, duel_type)
        await thread.archive()

        await utils.update_piflouz_message(self.bot)
