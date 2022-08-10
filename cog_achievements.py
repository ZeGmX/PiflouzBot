from interactions import extension_command, Extension, Emoji, Button, ButtonStyle, autodefer
from math import ceil
from replit import db

from achievement_handler import get_achievements_list
from constant import Constants
import utils


class Cog_achievements(Extension):
  """
  Cog containing all the interactions related to purchasing things
  ---
  fields:
    bot: interactions.Client
    achievements_per_page: int
    achievements: Achievement list
    nb_pages: int
  --
  Slash commands:
    /achievements list
  Components:
    page_achievements_list-{i}, i = 0...self.pages - 1
  """
  achievements_per_page = 10

  def __init__(self, bot):
    self.bot = bot
    self.achievements = get_achievements_list()
    self.nb_pages = ceil(len(self.achievements) / self.achievements_per_page)

    # Register the callbacks for the page arrow components
    for i in range(self.nb_pages):
      self.bot.component(f"page_achievements_list-{i}")(self.callback_from_page(i))


  @extension_command(name="achievements", description="TBD", scope=Constants.GUILD_IDS)
  async def achievements_cmd(self, ctx):
    print("in cmd")
    pass

  
  @achievements_cmd.subcommand(name="list", description="Check your achievements")
  @autodefer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def achiev_list_cmd(self, ctx, page=0):
    """
    Callback for the achievements list command
    --
    input:
      ctx: interactions.CommandContext
      page: int
    """
    await self.send_achievements_page(ctx, 0)
    

  async def send_achievements_page(self, ctx, page):
    """
    Common callback for the achievements list command and buttons
    --
    input:
      ctx: interactions.CommandContext
      page: int
    """
    user_id = str(ctx.author.id)

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
      buttons.append(Button(style=ButtonStyle.SECONDARY, emoji=Emoji(name="⬅️"), custom_id=f"page_achievements_list-{page - 1}"))
      
    if page < self.nb_pages - 1: # not the last page
      buttons.append(Button(style=ButtonStyle.SECONDARY, emoji=Emoji(name="➡️"), custom_id=f"page_achievements_list-{page + 1}"))
    
    await ctx.send(s, components=buttons, ephemeral=True)
    

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
    @autodefer(ephemeral=True)
    async def callback(ctx):
      await self.send_achievements_page(ctx, page=page)
    return callback


def setup(bot):
  Cog_achievements(bot)