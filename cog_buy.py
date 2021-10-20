from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import create_button, spread_to_rows
from discord_slash.model import ButtonStyle
from replit import db
import time

from constant import Constants
import embed_messages
import piflouz_handlers
import utils


class Cog_buy(commands.Cog):
  """
  Cog containing all the interactions related to purchasing things
  ---
  fields:
    bot: discord.ext.commands.Bot
    slash: discord_slash.SlashCommand 
    store_button_name: str
  """
  store_button_name = "store_button"

  def __init__(self, bot, slash):
    self.bot = bot
    self.slash = slash

    for emoji in Constants.POWERUPS_STORE:
      slash.add_component_callback(self.callback_from_emoji(emoji), components=emoji, use_callback_name=False)

  
  @cog_ext.cog_slash(name="piflex", description=f"when you have too many piflouz /!\ Costs {Constants.PIFLEX_COST} piflouz", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def piflex_cmd(self, ctx):
    """
    Callback for the piflex command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    user_id = str(ctx.author.id)
    
    # User has enough money
    if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(user_id, qty=-Constants.PIFLEX_COST, check_cooldown=False):
      role = ctx.guild.get_role(Constants.MEGA_PIFLEXER_ROLE_ID)
      member = ctx.author
      await member.add_roles(role)
      t = time.time()
      db["mega_piflexers"][user_id] = int(t)

      embed, index = embed_messages.get_embed_piflex(ctx.author)
      await ctx.send(embed=embed)

      if str(ctx.author_id) not in db["discovered_piflex"].keys():
        db["discovered_piflex"][str(ctx.author_id)] = []
      
      already_discovered = set(db["discovered_piflex"][str(ctx.author_id)])
      already_discovered.add(index)
      db["discovered_piflex"][str(ctx.author_id)] = list(already_discovered)

      await utils.update_piflouz_message(self.bot)

    # User doesn't have enough money
    else:
      balance = 0 if user_id not in db["piflouz_bank"].keys() else db["piflouz_bank"][user_id]
      await ctx.send(f"You need {Constants.PIFLEX_COST - balance} more {Constants.PIFLOUZ_EMOJI} to piflex!", hidden=True)


  @cog_ext.cog_slash(name="buyRankPiflex", description=f"flex with a custom rank /!\ Costs {Constants.PIFLEXER_COST} piflouz, lasts for {Constants.PIFLEXROLE_DURATION} seconds", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def buy_rank_piflex_cmd(self, ctx):
    """
    Callback for the buyRankPiflex command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    user_id = str(ctx.author.id)
    member = ctx.author
    role = ctx.guild.get_role(Constants.PIFLEXER_ROLE_ID)

    if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(user_id, qty=-Constants.PIFLEXER_COST, check_cooldown=False) and role not in member.roles:
      await member.add_roles(role)
      await ctx.send(f"{member.mention} just bought the piflexer rank!")
      await utils.update_piflouz_message(self.bot)
      db["piflexers"][user_id] = int(time.time())
    else:
      # User does not have enough money
      if role not in member.roles:
        await ctx.send(f"You need {Constants.PIFLEXER_COST - db['piflouz_bank'][user_id]} {Constants.PIFLOUZ_EMOJI} to buy the rank!", hidden=True)

      # User already have the rank
      else:
        await ctx.send("You already have the rank!", hidden=True)


  @cog_ext.cog_slash(name="store", description="buy fun upgrades", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def store_cmd(self, ctx):
    """
    Callback for the raffle command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    embed = embed_messages.get_embed_store_ui()
    
    buttons = [create_button(style=ButtonStyle.gray, label="", custom_id=emoji, emoji=emoji) for emoji in Constants.POWERUPS_STORE.keys()]
    components = spread_to_rows(*buttons)

    await ctx.send(embed=embed, components=components, hidden=True)
  

  async def store_button_callback(self, ctx, emoji):
    """
    callback for the store button with the given emoji
    --
    input:
      ctx: discord_slash.context.ComponentContext
    """
    await ctx.defer(hidden=True)
    user_id = str(ctx.author.id)

    if user_id not in db["powerups"].keys():
      db["powerups"][user_id] = []
    
    powerup = Constants.POWERUPS_STORE[emoji]
    if powerup.on_buy(user_id):
      await utils.update_piflouz_message(self.bot)
      await ctx.send("Successfully bought the powerup", hidden=True)
    else:
      await ctx.send("Purchase failed", hidden=True)


  def callback_from_emoji(self, emoji):
    """
    Returns the callback function for the store button with the given emoji
    --
    input:
      emoji: str
    --
    output:
      callback function
    """
    async def callback(ctx):
      await self.store_button_callback(ctx, emoji)
    return callback