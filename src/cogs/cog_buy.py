import copy
import functools
from interactions import Button, ButtonStyle, Extension, auto_defer, component_callback, slash_command, spread_to_rows
from math import ceil

from constant import Constants
import embed_messages
from events import EventType, get_event_object
from my_database import db
import piflouz_handlers
import user_profile
import utils


class CogBuy(Extension):
    """
    Cog containing all the interactions related to purchasing things
    ---
    fields:
        bot: interactions.Client
        store_button_name: str
    --
    Slash commands:
        /store
    Components:
        emoji, emoji in Constants.POWERUPS_STORE.keys()
        piflex
        buy_rank_piflex
    """

    store_button_name = "store_button"

    def __init__(self, bot):
        self.bot = bot

        for emoji in Constants.POWERUPS_STORE.keys():
            self.bot.add_component_callback(self.callback_from_emoji(emoji))

    @component_callback("piflex")
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def piflex_component(self, ctx):
        """
        Callback for the piflex component

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)

        price_multiplier = self.get_store_discount_multiplier()
        price = ceil(Constants.PIFLEX_COST * price_multiplier)

        # User has enough money
        if piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False):
            await ctx.author.add_role(role=Constants.MEGA_PIFLEXER_ROLE_ID)
            t = int(ctx.id.created_at.timestamp())
            db["mega_piflexers"][user_id] = t

            embed, index = embed_messages.get_embed_piflex(ctx.author)

            already_discovered = profile["discovered_piflex"]
            new = index not in already_discovered

            if new:
                already_discovered.append(index)

            content = None if not new else "Congratulations, this is a new image!"
            channel = ctx.channel
            await channel.send(content, embed=embed)
            await ctx.send("Done!", ephemeral=True)

            await utils.update_piflouz_message(self.bot)
            self.bot.dispatch("piflex_bought", ctx.author.id)
            await self.update_store_msg(ctx, profile["piflouz_balance"])

        # User doesn't have enough money
        else:
            balance = profile["piflouz_balance"]
            await ctx.send(f"You need {price - balance} more {Constants.PIFLOUZ_EMOJI} to piflex!", ephemeral=True)

    @component_callback("buy_rank_piflex")
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def buy_rank_piflex_component(self, ctx):
        """
        Callback for the buyRankPiflex component

        Parameters
        ----------
        ctx (interactions.SlashContext)
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)
        member = ctx.author
        role_id = Constants.PIFLEXER_ROLE_ID

        price_multiplier = self.get_store_discount_multiplier()
        price = ceil(Constants.PIFLEXER_COST * price_multiplier)

        if piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False) and role_id not in member.roles:
            await member.add_role(role=role_id)
            channel = ctx.channel
            await channel.send(f"{member.mention} just bought the piflexer rank!")
            await ctx.send("Done!", ephemeral=True)
            await utils.update_piflouz_message(self.bot)
            db["piflexers"][user_id] = int(ctx.id.created_at.timestamp())
            self.bot.dispatch("piflexer_rank_bought", ctx.author.id)
            await self.update_store_msg(ctx, profile["piflouz_balance"])
        else:
            # User does not have enough money
            if role_id not in member.roles:
                await ctx.send(f"You need {price - profile["piflouz_balance"]} {Constants.PIFLOUZ_EMOJI} to buy the rank!", ephemeral=True)

            # User already have the rank
            else:
                await ctx.send("You already have the rank!", ephemeral=True)

    @slash_command(name="store", description="Buy fun upgrades", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def store_cmd(self, ctx):
        """
        Callback for the raffle command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        """
        balance = user_profile.get_profile(str(ctx.author.id))["piflouz_balance"]

        price_multiplier = self.get_store_discount_multiplier()
        embed = embed_messages.get_embed_store_ui(balance, price_multiplier)

        buttons = self.get_all_store_components()

        await ctx.send(embed=embed, components=spread_to_rows(*buttons), ephemeral=True)

    async def store_button_callback(self, ctx, emoji):
        """
        callback for the store button with the given emoji

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        emoji (str)
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)
        current_time = int(ctx.id.created_at.timestamp())

        # We take a copy of the powerup in order not to modify the fields when buying
        powerup = copy.copy(Constants.POWERUPS_STORE[emoji])

        # Apply potential event-related discounts
        powerup.price = ceil(self.get_store_discount_multiplier() * powerup.price)

        if powerup.on_buy(user_id, current_time):
            await utils.update_piflouz_message(self.bot)
            await ctx.send("Successfully bought the powerup", ephemeral=True)
            self.bot.dispatch("store_purchase_successful", ctx.author.id)

            await self.update_store_msg(ctx, profile["piflouz_balance"])
        else:
            await ctx.send("Purchase failed", ephemeral=True)

    def callback_from_emoji(self, emoji):
        """
        Returns the callback function for the store button with the given emoji

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
            await self.store_button_callback(ctx, emoji)
        return callback

    async def update_store_msg(self, ctx, balance):
        """
        Updates the store message with the given balance

        Parameters
        ----------
        ctx (interactions.SlashContext)
        balance (int)
        """
        price_multiplier = self.get_store_discount_multiplier()
        embed = embed_messages.get_embed_store_ui(balance, price_multiplier)
        await ctx.edit(ctx.message, embed=embed, components=spread_to_rows(*self.get_all_store_components()))

    def get_all_store_components(self):
        """
        Returns all the components of the store
        """
        buttons = [Button(style=ButtonStyle.GRAY, label="", custom_id=emoji, emoji=emoji) for emoji in Constants.POWERUPS_STORE.keys()]\
                + [Button(style=ButtonStyle.GRAY, label="", custom_id="buy_rank_piflex", emoji=Constants.PIFLOUZ_EMOJI),
                   Button(style=ButtonStyle.GRAY, label="", custom_id="piflex", emoji=Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI)]
        return buttons

    def get_store_discount_multiplier(self):
        """
        Returns the store discount multiplier

        Returns
        -------
        res (float)
        """
        current_event = get_event_object(EventType.PASSIVE)
        if current_event is not None:
            return functools.reduce(lambda accu, powerup: accu * powerup.get_store_price_multiplier(), current_event.get_powerups(), 1)
        return 1
