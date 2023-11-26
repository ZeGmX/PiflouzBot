from interactions import Extension, Button, ButtonStyle, auto_defer, slash_command, component_callback
import copy

from constant import Constants
import embed_messages
from my_database import db
import piflouz_handlers
import utils


class Cog_buy(Extension):
  """
  Cog containing all the interactions related to purchasing things
  ---
  fields:
    bot: interactions.Client
    store_button_name: str
  --
  Slash commands:
    /piflex
    /buy-rank-piflex
    /store
  Components:
    emoji, emoji in Constants.POWERUPS_STORE.keys()
  """
  store_button_name = "store_button"

  def __init__(self, bot):
    self.bot = bot

    for emoji in Constants.POWERUPS_STORE.keys():
      self.bot.add_component_callback(self.callback_from_emoji(emoji))

  
  @slash_command(name="piflex", description=f"When you have too many piflouz ⚠️ Costs {Constants.PIFLEX_COST} piflouz", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def piflex_cmd(self, ctx):
    """
    Callback for the piflex command
    --
    input:
      ctx: interactions.SlashContext
    """
    user_id = str(ctx.author.id)
    
    # User has enough money
    if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(user_id, qty=-Constants.PIFLEX_COST, check_cooldown=False):
      await ctx.author.add_role(role=Constants.MEGA_PIFLEXER_ROLE_ID)
      t = int(ctx.id.created_at.timestamp())
      db["mega_piflexers"][user_id] = t

      embed, index = embed_messages.get_embed_piflex(ctx.author)
      
      if str(ctx.author.id) not in db["discovered_piflex"].keys():
        db["discovered_piflex"][str(ctx.author.id)] = []
      
      already_discovered = set(db["discovered_piflex"][str(ctx.author.id)])
      new = index not in already_discovered
      already_discovered.add(index)
      db["discovered_piflex"][str(ctx.author.id)] = list(already_discovered)

      content = None if not new else "Congratulations, this is a new image!"
      channel = ctx.channel
      await channel.send(content, embed=embed)
      await ctx.send("Done!", ephemeral=True)

      await utils.update_piflouz_message(self.bot)
      self.bot.dispatch("piflex_bought", ctx.author.id)

    # User doesn't have enough money
    else:
      balance = 0 if user_id not in db["piflouz_bank"].keys() else db["piflouz_bank"][user_id]
      await ctx.send(f"You need {Constants.PIFLEX_COST - balance} more {Constants.PIFLOUZ_EMOJI} to piflex!", ephemeral=True)


  @slash_command(name="buy-rank-piflex", description=f"Flex with a custom rank ⚠️ Costs {Constants.PIFLEXER_COST} piflouz, lasts for {utils.seconds_to_formatted_string(Constants.PIFLEX_ROLE_DURATION)}", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def buy_rank_piflex_cmd(self, ctx):
    """
    Callback for the buyRankPiflex command
    --
    input:
      ctx: interactions.SlashContext
    """
    user_id = str(ctx.author.id)
    member = ctx.author
    role_id = Constants.PIFLEXER_ROLE_ID
    
    if user_id in db["piflouz_bank"] and piflouz_handlers.update_piflouz(user_id, qty=-Constants.PIFLEXER_COST, check_cooldown=False) and role_id not in member.roles:
      await member.add_role(role=role_id)
      channel = ctx.channel
      await channel.send(f"{member.mention} just bought the piflexer rank!")
      await ctx.send("Done!", ephemeral=True)
      await utils.update_piflouz_message(self.bot)
      db["piflexers"][user_id] = int(ctx.id.created_at.timestamp())
      self.bot.dispatch("piflexer_rank_bought", ctx.author.id)
    else:
      # User does not have enough money
      if role_id not in member.roles:
        await ctx.send(f"You need {Constants.PIFLEXER_COST - db['piflouz_bank'][user_id]} {Constants.PIFLOUZ_EMOJI} to buy the rank!", ephemeral=True)

      # User already have the rank
      else:
        await ctx.send("You already have the rank!", ephemeral=True)


  @slash_command(name="store", description="Buy fun upgrades", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def store_cmd(self, ctx):
    """
    Callback for the raffle command
    --
    input:
      ctx: interactions.SlashContext
    """
    embed = embed_messages.get_embed_store_ui()

    buttons = [Button(style=ButtonStyle.SECONDARY, label="", custom_id=emoji, emoji=emoji) for emoji in Constants.POWERUPS_STORE.keys()]

    await ctx.send(embed=embed, components=buttons, ephemeral=True)
  

  async def store_button_callback(self, ctx, emoji):
    """
    callback for the store button with the given emoji
    --
    input:
      ctx: interactions.ComponentContext
      emoji: str
    """
    user_id = str(ctx.author.id)
    current_time = int(ctx.id.created_at.timestamp())

    if user_id not in db["powerups"].keys():
      db["powerups"][user_id] = []
    
    # We take a copy of the powerup in order not to modify the fields when buying
    powerup = copy.copy(Constants.POWERUPS_STORE[emoji])
    if powerup.on_buy(user_id, current_time):
      await utils.update_piflouz_message(self.bot)
      await ctx.send("Successfully bought the powerup", ephemeral=True)
      self.bot.dispatch("store_purchase_successful", ctx.author.id)
    else:
      await ctx.send("Purchase failed", ephemeral=True)


  def callback_from_emoji(self, emoji):
    """
    Returns the callback function for the store button with the given emoji
    --
    input:
      emoji: str
    --
    output:
      interactions.ComponentCommand
    """
    @component_callback(emoji)
    @auto_defer(ephemeral=True)
    async def callback(ctx):
      await self.store_button_callback(ctx, emoji)
    return callback


def setup(bot):
  Cog_buy(bot)