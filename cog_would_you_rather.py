from interactions import Extension, OptionType, extension_command, TextInput, TextStyleType, Modal, extension_modal, extension_message_command, autodefer, option
from replit import db

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
    WYR - add option
    WYR - edit
    WYR - remove option
  Modals:
    wyr
    wyr_edit
  """

  def __init__(self, bot):
    self.bot = bot


  @extension_command(name="wouldyourather", description="Create a custom wouldyourather", scope=Constants.GUILD_IDS)
  @option(name="nb_options", description="How many options, up to 5", type=OptionType.INTEGER, min_value=2, max_value=5,  required=True)
  @autodefer(ephemeral=True)
  async def wouldyourather_cmd(self, ctx, nb_options):
    """
    Custom wouldyourather commend for easier formating
    --
    input:
      ctx: interactions.CommandContext
      nb_options: int between 2 and 5
    """
    modal = self.get_wyr_modal(nb_options)
    await ctx.popup(modal)


  @extension_modal("wyr")
  @autodefer(ephemeral=True)
  async def wouldyourather_response(self, ctx, *options):
    """
    Response to the "Would you rather?" modal
    --
    input:
      ctx: interactions.ComponentContext
      options: string list
    """
    msg = await ctx.send(self.get_wyr_txt(options))

    emojis = "🇦🇧🇨🇩🇪"
    for i in range(len(options)):
      await msg.create_reaction(emojis[i])


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
    nb_options = len(content)
    values = [line[4:] for line in content]

    modal = self.get_wyr_modal(nb_options, values=values, custom_id="wyr_edit")
    await ctx.popup(modal)

    db["wyr_edit"][str(ctx.author.id)] = int(ctx.target.id)


  @extension_message_command(name="WYR - add option", scope=Constants.GUILD_IDS)
  @autodefer(ephemeral=True)
  async def wouldyourather_add_option(self, ctx):
    """
    Message context application for adding an option to a "Would you rather?" message by Pibot
    --
    input:
      ctx: ctx: interactions.CommandContext
    """
    start = "> **Would you rather...**\n"
    await utils.custom_assert(self.check_if_wyr_message(ctx.target), "This is not a Pibot-generated 'Would you rather?'", ctx)

    separator = "\n> **or**\n"
    content = ctx.target.content[len(start):].split(separator)
    nb_options = len(content)

    await utils.custom_assert(nb_options < 5, "You have reached the maximum amount of options", ctx)
    
    values = [line[4:] for line in content] + [""]

    modal = self.get_wyr_modal(nb_options + 1, values=values, custom_id="wyr_edit")
    await ctx.popup(modal)

    db["wyr_edit"][str(ctx.author.id)] = int(ctx.target.id)


  @extension_message_command(name="WYR - remove option", scope=Constants.GUILD_IDS)
  @autodefer(ephemeral=True)
  async def wouldyourather_remove_option(self, ctx):
    """
    Message context application for removing an option to a "Would you rather?" message by Pibot
    --
    input:
      ctx: ctx: interactions.CommandContext
    """
    start = "> **Would you rather...**\n"
    await utils.custom_assert(self.check_if_wyr_message(ctx.target), "This is not a Pibot-generated 'Would you rather?'", ctx)

    separator = "\n> **or**\n"
    content = ctx.target.content[len(start):].split(separator)
    nb_options = len(content)

    await utils.custom_assert(nb_options > 1, "You have reached the minimum amount of options", ctx)
    
    values = [line[4:] for line in content[:-1]]

    modal = self.get_wyr_modal(nb_options - 1, values=values, custom_id="wyr_edit")
    await ctx.popup(modal)

    db["wyr_edit"][str(ctx.author.id)] = int(ctx.target.id)


  @extension_modal("wyr_edit")
  @autodefer(ephemeral=True)
  async def wouldyourather_edit_response(self, ctx, *options):
    """
    Response to the "Would you rather?" modal
    --
    input:
      ctx: interactions.ComponentContext
      options: string list
    """
    id = db["wyr_edit"][str(ctx.author.id)]
    
    channel = await self.bot.get_channel(ctx.channel_id)
    msg = await channel.get_message(id)

    await msg.edit(self.get_wyr_txt(options))
    await ctx.send("Done!", ephemeral=True)
    del db["wyr_edit"][str(ctx.author.id)]

    emojis = "🇦🇧🇨🇩🇪"

    bot_reac = [reac.emoji.name for reac in msg.reactions if reac.me and reac.emoji.name in emojis]
    for i in range(len(options)):
      if emojis[i] not in bot_reac:
        await msg.create_reaction(emojis[i])
    for i in range(len(options), len(emojis)):
      if emojis[i] in bot_reac:
        await msg.remove_all_reactions_of(emojis[i])

  
  def get_wyr_modal(self, nb_options, values=None, custom_id="wyr"):
    """
    Generates the modal object for a "Would you rather?"
    --
    input:
      nb_options: int
      values: string list -> the default value for each wyr option
      custom_id: str -> id for the modal
    """
    if values is None: values = ["" for _ in range(nb_options)]

    option_indexes = "ABCDE"
      
    components = [TextInput(style=TextStyleType.SHORT, label=f"Option {option_indexes[i]}", custom_id=f"wyr_option_{i}", value=values[i], placeholder="Type your option here", required=True) for i in range(nb_options)]
    return Modal(title="Would you rather...", custom_id=custom_id, components=components)


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
    text_end = text_separator.join([f"> {emojis[i]} {options[i]}" for i in range(len(options))])

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