from interactions import extension_command, extension_component, Extension
from replit import db

from constant import Constants
import piflouz_handlers
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
    self.button_name
  """

  button_name = "piflouz_mining_button"

  def __init__(self, bot):
    self.bot = bot
  

  @extension_command(name="get", description="For the lazy ones", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def get_cmd(self, ctx):
    """
    Callback for the get command
    --
    input:
      ctx: interactions.CommandContext
    """
    await ctx.defer(ephemeral=True)

    current_time = int(ctx.id.epoch)
    piflouz_handlers.update_combo(ctx.author.id, current_time)
    successful_update, qty = piflouz_handlers.update_piflouz(ctx.author.id, current_time=current_time)
    
    if not successful_update:
      timer = utils.get_timer(ctx.author.id, current_time)
      
      output_text = f"You still need to wait {utils.seconds_to_formatted_string(timer)} before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      output_text = f"You just earned {qty} {Constants.PIFLOUZ_EMOJI}! Come back later for some more\nYour current combo: {db['mining_combo'][str(ctx.author.id)]} / {piflouz_handlers.get_max_rewardable_combo(ctx.author.id)}"
    
    await ctx.send(output_text, ephemeral=True)
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("combo_updated", ctx.author.id)


  @extension_component(component=button_name)
  async def mining_button_callback(self, ctx):
    """
    Callback for the button under the mining message
    It does what /get would do
    --
    input:
      ctx: interactions.ComponentContext
    """
    await self.get_cmd(ctx)
    

  @extension_command(name="cooldown", description="When your addiction is stronger than your sense of time", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def cooldown_cmd(self, ctx):
    """
    Callback for the cooldown command
    --
    input:
      ctx: interactions.CommandContext
    """
    user = ctx.author
    current_time = int(ctx.id.epoch)
    timer = utils.get_timer(user.id, current_time)
    if timer > 0 :
      output_text = f"You still need to wait {utils.seconds_to_formatted_string(timer)} before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      output_text = f"You can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
    await ctx.send(output_text, ephemeral=True)


def setup(bot):
  Cog_piflouz_mining(bot)