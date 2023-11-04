from interactions import Extension, extension_command, TextInput, TextStyleType, Modal, extension_modal, extension_message_command, autodefer
from my_database import db

from constant import Constants
import utils


class Cog_would_you_rather(Extension):
  """
  Commands for the "Would you rather?"
  --
  fields:
    bot: interactions.Client
  --
  Slash commands:
    /wouldyourather
  Message commands:
    WYR - edit
  Modals:
    wyr
  """

  modal_name = "wyr"

  def __init__(self, bot):
    self.bot = bot


  @extension_command(name="wouldyourather", description="Create a custom wouldyourather", scope=Constants.GUILD_IDS)
  @autodefer(ephemeral=True)
  async def wouldyourather_cmd(self, ctx):
    """
    Custom wouldyourather commend for easier formating
    --
    input:
      ctx: interactions.CommandContext
    """
    modal = self.get_wyr_modal()

    if str(ctx.author.id) in db["wyr_edit"].keys():
      del db["wyr_edit"][str(ctx.author.id)]  
    
    await ctx.popup(modal)

  # @extension_modal("wyr")
  # @autodefer(ephemeral=True)
  # async def wouldyourather_response(self, ctx, *options):
  #   """
  #   Response to the "Would you rather?" modal
  #   --
  #   input:
  #     ctx: interactions.ComponentContext
  #     options: string list
  #   """
  #   msg = await ctx.send(self.get_wyr_txt(options))

  #   emojis = "🇦🇧🇨🇩🇪"
  #   for i in range(len(options)):
  #     await msg.create_reaction(emojis[i])


  @extension_message_command(name="WYR - edit", scope=Constants.GUILD_IDS)
  @autodefer(ephemeral=True)
  async def edit_would_you_rather_app(self, ctx):
    """
    Message context application for editing a "Would you rather?" message by Pibot
    --
    input:
      ctx: ctx: interactions.CommandContext
    """
    start = "> **Would you rather...**\n"
    await utils.custom_assert(self.check_if_wyr_message(ctx.target), "This is not a Pibot-generated 'Would you rather?'", ctx)

    separator = "\n> **or**\n"
    content = ctx.target.content[len(start):].split(separator)
    values = [line[4:] for line in content]

    modal = self.get_wyr_modal(values=values)
    await ctx.popup(modal)

    db["wyr_edit"][str(ctx.author.id)] = int(ctx.target.id)

 
  @extension_modal(modal_name)
  @autodefer(ephemeral=True)
  async def wouldyourather_edit_response(self, ctx, *options):
    """
    Response to the "Would you rather?" modal
    --
    input:
      ctx: interactions.ComponentContext
      options: string list
    """
    # We remove the blank options
    options = list(filter(lambda elmt: len(elmt) > 0, options))

    channel = await self.bot.get_channel(ctx.channel_id)
    txt = self.get_wyr_txt(options)
    msg = None
    
    # We are editing a WYR
    if str(ctx.author.id) in db["wyr_edit"].keys():
      # We recover the id of the original message we are editing
      id = db["wyr_edit"][str(ctx.author.id)]
      msg = await channel.get_message(id)
      await msg.edit(txt)
      del db["wyr_edit"][str(ctx.author.id)]
    # We are creating a WYR
    else:
      msg = await channel.send(txt)

    await ctx.send("Done!", ephemeral=True)

    # We update the reaction emojis
    emojis = "🇦🇧🇨🇩🇪"

    bot_reac = []
    if msg.reactions is not None:
      bot_reac = [reac.emoji.name for reac in msg.reactions if reac.me and reac.emoji.name in emojis]
    for i in range(len(options)):
      if emojis[i] not in bot_reac:
        await msg.create_reaction(emojis[i])
    for i in range(len(options), len(emojis)):
      if emojis[i] in bot_reac:
        await msg.remove_all_reactions_of(emojis[i])

  
  def get_wyr_modal(self, values=None):
    """
    Generates the modal object for a "Would you rather?"
    --
    input:
      values: string list -> the default value for each wyr option
    """
    nb_options = 5
    
    if values is None: values = []
    if len(values) < 5: values += [""] * (5 - len(values))

    option_indexes = "ABCDE"

    # The first two are mandatory, the other ones are not
    components = [TextInput(style=TextStyleType.SHORT, label=f"Option {option_indexes[i]}", custom_id=f"wyr_option_{i}", value=values[i], placeholder="Type your option here", required=i < 2) for i in range(nb_options)]
    return Modal(title="Would you rather...", custom_id=self.modal_name, components=components)


  def get_wyr_txt(self, options):
    """
    Returns the formatted text for a "Would you rather?"
    --
    input:
      options: str list
    --
    output:
      res: str
    """
    emojis = "🇦🇧🇨🇩🇪"  
    
    text_start = "> **Would you rather...**\n"
    text_separator = "\n> **or**\n"
    text_end = text_separator.join([f"> {emojis[i]} {options[i]}" for i in range(len(options)) if len(options[i]) > 0])

    return text_start + text_end
    

  def check_if_wyr_message(self, msg):
    """
    Checks if the message is a "Would you rather?" message by Pibot
    --
    input:
      msg: interactions.Message
    --
    output:
      res: bool
    """
    start = "> **Would you rather...**\n"
    return msg.content.startswith(start) and msg.author.id == int(self.bot.me.id)


def setup(bot):
  Cog_would_you_rather(bot)