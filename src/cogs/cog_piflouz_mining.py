from interactions import slash_command, component_callback, Extension, auto_defer
from my_database import db

from constant import Constants
import piflouz_handlers
import user_profile
import utils


class Cog_piflouz_mining(Extension):
    """
    Cog containing all the interactions related to purchasing things
    ---
    fields:
        bot: interactions.client
        button_name: str
    --
    Slash commands:
        /get
        /cooldown
    Components:
        self.BUTTON_NAME
    """

    BUTTON_NAME = "piflouz_mining_button"

    def __init__(self, bot):
        self.bot = bot
    

    @slash_command(name="get", description="For the lazy ones", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def get_cmd(self, ctx):
        """
        Callback for the get command
        --
        input:
            ctx: interactions.InteractionContext
        """
        await self.get_callback_tmp(ctx)


    @component_callback(BUTTON_NAME)
    @auto_defer(ephemeral=True)
    async def mining_button_callback(self, ctx):
        """
        Callback for the button under the mining message
        It does what /get would do
        --
        input:
            ctx: interactions.ComponentContext
        """
        await self.get_callback_tmp(ctx)

    
    async def get_callback_tmp(self, ctx):
        """
        Callback for the /get command or button
        --
        input:
            ctx: interactions.SlashContext or interactions.ComponentContext
        """
        current_time = int(ctx.id.created_at.timestamp())
        piflouz_handlers.update_combo(ctx.author.id, current_time)
        successful_update, qty = piflouz_handlers.update_piflouz(ctx.author.id, current_time=current_time)

        if not successful_update:
            timer = user_profile.get_timer(ctx.author.id, current_time)
            output_text = f"You still need to wait {utils.seconds_to_formatted_string(timer)} before earning more {Constants.PIFLOUZ_EMOJI}!"
        else:
            profile = user_profile.get_profile(str(ctx.author.id))
            output_text = f"You just earned {qty} {Constants.PIFLOUZ_EMOJI}! Come back later for some more\nYour current combo: {profile["mining_combo"]} / {piflouz_handlers.get_max_rewardable_combo(ctx.author.id)}\nDaily bonus obtained: {profile["daily_bonus"]} / {Constants.DAILY_BONUS_MAX_STREAK}"
            
            self.bot.dispatch("combo_updated", ctx.author.id)
            db["piflouz_generated"]["get"] += qty
            await utils.update_piflouz_message(self.bot)

        await ctx.send(output_text, ephemeral=True)


    @slash_command(name="cooldown", description="When your addiction is stronger than your sense of time", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def cooldown_cmd(self, ctx):
        """
        Callback for the cooldown command
        --
        input:
            ctx: interactions.CommandContext
        """
        user = ctx.author
        current_time = int(ctx.id.created_at.timestamp())
        timer = user_profile.get_timer(user.id, current_time)
        if timer > 0 :
            output_text = f"You still need to wait {utils.seconds_to_formatted_string(timer)} before earning more {Constants.PIFLOUZ_EMOJI}!"
        else:
            output_text = f"You can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
        await ctx.send(output_text, ephemeral=True)


def setup(bot):
    Cog_piflouz_mining(bot)