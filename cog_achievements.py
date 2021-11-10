from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import create_button, spread_to_rows
from discord_slash.model import ButtonStyle
from math import ceil
from replit import db

from achievement_handler import get_achievements_list
from constant import Constants
import utils


class Cog_achievements(commands.Cog):
  """
  Cog containing all the interactions related to purchasing things
  ---
  fields:
    slash: discord_slash.SlashCommand 
    achievements_per_page: int
    achievements: Achievement list
    nb_pages: int
  """
  achievements_per_page = 10

  def __init__(self, slash):
    self.slash = slash
    self.achievements = get_achievements_list()
    self.nb_pages = ceil(len(self.achievements) / self.achievements_per_page)

    for i in range(self.nb_pages):
      slash.add_component_callback(self.callback_from_page(i), components=f"page_achievements_list-{i}", use_callback_name=False)


  @cog_ext.cog_subcommand(base="achievements", name="list", description="Check all the statuses", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def achiev_list_cmd(self, ctx, page=0):
    """
    Callback for the achievements list command
    --
    input:
      ctx: discord_slash.context.SlashContext
    """
    user_id = str(ctx.author_id)

    if user_id not in db["achievements"].keys(): db["achievements"][user_id] = []

    user_achievements = list(db["achievements"][user_id])

    # Getting the string emoji
    res = [f"Page {page + 1} / {self.nb_pages}"]
    for a in self.achievements[page * self.achievements_per_page:(page + 1) * self.achievements_per_page]:
      emoji = "✅" if a.to_str() in user_achievements else "❌"
      res.append(f"{emoji} • **{a.name}** • {a.reward} {Constants.PIFLOUZ_EMOJI}\n{a.description}")
    s = "\n----\n".join(res)

    # Getting the buttons
    buttons = []
    if page != 0 : # not the first page
      buttons.append(create_button(style=ButtonStyle.gray, label="", custom_id=f"page_achievements_list-{page - 1}", emoji="⬅️"))
    if page < self.nb_pages - 1: # not the last page
      buttons.append(create_button(style=ButtonStyle.gray, label="", custom_id=f"page_achievements_list-{page + 1}", emoji="➡️"))
    components = spread_to_rows(*buttons)
    
    await ctx.send(s, components=components, hidden=True)
    

  def callback_from_page(self, page):
    """
    Returns the callback function for the page buttons in the achievement list
    --
    input:
      page: int
    --
    output:
      callback function
    """
    async def callback(ctx):
      await self.slash.invoke_command(self.achiev_list_cmd, ctx, {"page": page})
    return callback