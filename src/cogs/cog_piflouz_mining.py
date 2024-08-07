from interactions import Extension, auto_defer, component_callback, slash_command

from constant import Constants
from piflouz_generated import PiflouzSource, add_to_stat
import piflouz_handlers
import user_profile
import utils


class CogPiflouzMining(Extension):
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

    @slash_command(name="get", description="Get some piflouz!", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def get_cmd(self, ctx):
        """
        Callback for the get command

        Parameters
        ----------
        ctx (interactions.InteractionContext)
        """
        await self.get_callback_tmp(ctx)

    @component_callback(BUTTON_NAME)
    @auto_defer(ephemeral=True)
    async def mining_button_callback(self, ctx):
        """
        Callback for the button under the mining message
        It does what /get would do

        Parameters
        ----------
        ctx (interactions.ComponentContext)
        """
        await self.get_callback_tmp(ctx)

    async def get_callback_tmp(self, ctx):
        """
        Callback for the /get command or button

        Parameters
        ----------
        ctx (interactions.SlashContext or interactions.ComponentContext)
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
            add_to_stat(qty, PiflouzSource.GET)
            await utils.update_piflouz_message(self.bot)

        await ctx.send(output_text, ephemeral=True)
