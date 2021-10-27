from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from discord_slash.model import SlashCommandOptionType as option_type
from discord.utils import escape_markdown
from replit import db

from constant import Constants
import powerups # Used for eval
import socials
import utils


class Cog_status_check(commands.Cog):
  """
  Cog containing all the interactions related to checking information about the user
  """

  @cog_ext.cog_slash(name="isLive", description="check if a certain streamer is live", guild_ids=Constants.GUILD_IDS, options=[
  create_option(name="streamer_name", description="The name of the streamer you want to check", option_type=option_type.STRING, required=True)
  ])
  @utils.check_message_to_be_processed
  async def is_live_cmd(self, ctx, streamer_name):
    """
    Callback for the isLive command
    --
    input:
      ctx: discord_slash.context.SlashContext
      streamer_name: str
    """
    stream = socials.get_live_status(streamer_name)
    if stream is not None:
      # The streamer is live
      msg = escape_markdown(f"{streamer_name} is currently live on \"{stream.title}\", go check out on https://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}")
      await ctx.send(msg)
    else:
      # The streamer is not live
      msg = escape_markdown(f"{streamer_name} is not live yet. Follow https://www.twitch.tv/{streamer_name} to stay tuned ! {Constants.FUEGO_EMOJI}")
      await ctx.send(msg)
  

  @cog_ext.cog_slash(name="balance", description=f"check how many piflouz you have. Kind of a low-cost Piflex", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="user", description="the person you want to check. Leave empty to check your own balance", option_type=option_type.USER, required=False)
  ])
  @utils.check_message_to_be_processed
  async def balance_cmd(self, ctx, user=None):
    """
    Callback for the balance command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    if user is None: user = ctx.author

    user_id = str(user.id)
    if user_id not in db["piflouz_bank"].keys(): db["piflouz_bank"][user_id] = 0
    if user_id not in db["turbo_piflouz_bank"].keys(): db["turbo_piflouz_bank"][user_id] = 0
    
    balance = db["piflouz_bank"][str(user.id)]
    content = f"Balance of {user.mention}:\n{balance} {Constants.PIFLOUZ_EMOJI}"

    if str(user.id) in db["turbo_piflouz_bank"].keys():
      content += f"\n{db['turbo_piflouz_bank'][str(user.id)]} {Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI}"

    await ctx.send(content, hidden=True)


  @cog_ext.cog_slash(name="pilord", description="see how much you need to farm to flex with your rank", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def pilord_cmd(self, ctx):
    """
    Callback for the pilord command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    user_id = str(ctx.author.id)
    if user_id not in db["piflouz_bank"].keys():
      db["piflouz_bank"][user_id] = 0

    if user_id in db["current_pilords"]:
      await ctx.send("You are currently a pilord. Kinda flexing right now!", hidden=True)
    else:
      amount = db["piflouz_bank"][user_id]
      max_amount = db["piflouz_bank"][db["current_pilords"][0]]
      await ctx.send(f"You need {max_amount - amount} {Constants.PIFLOUZ_EMOJI} to become pilord!", hidden=True)  
  

  @cog_ext.cog_slash(name="powerups", description="see how powerful you are", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def powerups_cmd(self, ctx):
    """
    Callback for the powerups command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    await ctx.defer(hidden=True)
    user_id = str(ctx.author_id)
    content = "Here is the list of powerups you have at the moment:\n"
    has_any_powerup = False

    if user_id in db["powerups"].keys():
      for powerup_str in db["powerups"][user_id]:
        powerup = eval(powerup_str)
        info = powerup.get_info_str()
        if info != "": 
          content +=  info + '\n'
          has_any_powerup = True

    if not has_any_powerup:
      content = "You don't have any power up at the moment. Go buy one, using `/store`!"   
    await ctx.send(content, hidden=True)

  
  @cog_ext.cog_slash(name="ranking", description="See how worthy you are", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def ranking_cmd(self, ctx):
    """
    Callback for the ranking command
    --
    input:
    ctx: discord.ext.commands.Context
    """
    await ctx.defer(hidden=True)
    d_piflouz = dict(db["piflouz_bank"])
    d_piflex = dict(db["discovered_piflex"])
    d_donations = dict(db["donation_balance"])
    
    res = ""
    user_id = str(ctx.author_id)

    if user_id in d_piflouz.keys():
      amount_user = d_piflouz[user_id]
      rank = len([val for val in d_piflouz.values() if val > amount_user]) + 1
      res += f"Piflouz ranking: {rank} with {amount_user} {Constants.PIFLOUZ_EMOJI}\n"

    if user_id in d_piflex.keys():
      amount_user = len(d_piflex[user_id])
      rank = len([val for val in d_piflex.values() if len(val) > amount_user]) + 1
      res += f"Piflex discovery ranking: {rank} with {amount_user} discovered piflex images\n"

    if user_id in db["donation_balance"].keys():
      amount_user = d_donations[user_id]
      rank = len([val for val in d_donations.values() if val > amount_user]) + 1
      res += f"Piflouz donation ranking: {rank} with {amount_user} {Constants.PIFLOUZ_EMOJI}\n"
    
    if res == "":
      await ctx.send("You are not part of any ranking", hidden=True)
    else:
      await ctx.send(res, hidden=True)
    

  @cog_ext.cog_slash(name="seasonresult", description="see how much you earned in the last season", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def seasonresult_cmd(self, ctx):
    """
    Callback for the seasonresult command
    --
    input:
    ctx: discord.ext.commands.Context
    """
    await ctx.defer(hidden=True)

    user_id = str(ctx.author_id)
    assert user_id in db["season_results"].keys(), "You did not participate to the previous season"

    lines = ["Last season you earned the following:"]
    total = 0
    for key, val in db["season_results"][user_id].items():
      if key.endswith("ranking"):
        score, rank = val
        lines.append(f"{key} - {score} {Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI} - rank {rank + 1}")
        total += score
      else:
        lines.append(f"{key} - {val} {Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI}")
        total += val
    lines.append(f"Total - {total}")
  
    msg = "\n".join(lines)
    await ctx.send(msg, hidden=True)
      
