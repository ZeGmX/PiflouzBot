from discord.ext import commands
from discord_slash import cog_ext
from replit import db
import functools

from constant import Constants
import piflouz_handlers
import powerups  # Used for eval
import utils


class Cog_piflouz_mining(commands.Cog):
  """
  Cog containing all the interactions related to purchasing things
  ---
  fields:
    bot: discord.ext.commands.Bot
    slash: discord_slash.SlashCommand 
    button_name: str
  """

  button_name = "piflouz_mining_button"

  def __init__(self, bot, slash):
    self.bot = bot
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
    successful_update = piflouz_handlers.update_piflouz(user.id)
    
    if not successful_update:
      timer = utils.get_timer(user.id)
      
      output_text = f"{user.mention}, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      if str(user.id) not in db["powerups"].keys():
        db["powerups"][str(user.id)] = []
        
      qty = functools.reduce(lambda accu, powerup_str: accu * eval(powerup_str).get_piflouz_multiplier_value(), db["powerups"][str(user.id)], Constants.NB_PIFLOUZ_PER_REACT)
      qty = int(qty)

      output_text = f"You just earned {qty} {Constants.PIFLOUZ_EMOJI}! Come back later for some more"
    
    await ctx.send(output_text, hidden=True)
    await utils.update_piflouz_message(self.bot)


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
    timer = utils.get_timer(user.id)
    if timer > 0 :
      output_text = f"{user.mention}, you still need to wait {timer} seconds before earning more {Constants.PIFLOUZ_EMOJI}!"
    else:
      output_text = f"{user.mention}, you can earn more {Constants.PIFLOUZ_EMOJI}. DO IT RIGHT NOW!"
    await ctx.send(output_text, hidden=True)
