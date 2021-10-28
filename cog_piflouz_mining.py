from discord.ext import commands
from discord_slash import cog_ext
from replit import db

from constant import Constants
import piflouz_handlers
import utils


class Cog_piflouz_mining(commands.Cog):
  """
  Cog containing all the interactions related to purchasing things
  ---
  fields:
    slash: discord_slash.SlashCommand 
    button_name: str
  """

  button_name = "piflouz_mining_button"

  def __init__(self, slash):
    self.slash = slash
  

  @cog_ext.cog_slash(name="get", description="for the lazy one", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def get_cmd(self, ctx):
    """
    Callback for the get command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    await ctx.defer(hidden=True)
    user = ctx.author

    current_time = int(ctx.created_at.timestamp())
    piflouz_handlers.update_combo(ctx.author_id, current_time)
    successful_update, qty = piflouz_handlers.update_piflouz(user.id, current_time=current_time)
    
    if not successful_update:
      timer = utils.get_timer(user.id, current_time)
      
      output_text = f"You still need to wait {utils.seconds_to_formatted_string(timer)} before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      output_text = f"You just earned {qty} {Constants.PIFLOUZ_EMOJI}! Come back later for some more\nYour current combo: {db['mining_combo'][str(user.id)]} / {Constants.MAX_MINING_COMBO}"
    
    await ctx.send(output_text, hidden=True)
    await utils.update_piflouz_message(ctx.bot)
    ctx.bot.dispatch("combo_updated", ctx.author_id)


  @cog_ext.cog_component(components=button_name, use_callback_name=False)
  async def mining_button_callback(self, ctx):
    """
    Callback for the button under the mining message
    It does what /get would do
    --
    input:
      discord_slash.context.ComponentContext
    """
    await self.slash.invoke_command(self.get_cmd, ctx, {})
    

  @cog_ext.cog_slash(name="cooldown", description="when your addiction is stronger than your sense of time", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def cooldown_cmd(self, ctx):
    """
    Callback for the cooldown command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    user = ctx.author
    current_time = int(ctx.created_at.timestamp())
    timer = utils.get_timer(user.id, current_time)
    if timer > 0 :
      output_text = f"You still need to wait {utils.seconds_to_formatted_string(timer)} before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      output_text = f"You can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
    await ctx.send(output_text, hidden=True)
