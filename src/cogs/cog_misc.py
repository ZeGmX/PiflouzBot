from interactions import Extension, OptionType, Button, ButtonStyle, SlashCommandChoice, auto_defer, slash_command, slash_option, message_context_menu
from interactions.ext.paginators import Paginator
from math import ceil
import random

from cogs.cog_piflouz_mining import Cog_piflouz_mining
from constant import Constants
import embed_messages
from my_database import db
import piflouz_handlers
import utils


class Cog_misc(Extension):
  """
  Miscellaneous commands
  --
  fields:
    bot: interactions.Client
  --
  Slash commands:
    /help
    /hello
    /setup-channel [main | twitch]
    /donate
    /joke
    /giveaway
    /spawn-pibox
    /role [get | remove]
    /pichapouche
    /otter
  Message commands:
    Du quoi?
    Du tarpin !
  """

  def __init__(self, bot):
    self.bot = bot


  @slash_command(name="help", description="Show the help message", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def help_cmd(self, ctx):
    """
    Callback for the help command
    --
    input:
      ctx: interactions.SlashContext
    """
    embeds = embed_messages.get_embeds_help_message()
    p = Paginator.create_from_embeds(self.bot, *embeds)
    await p.send(ctx, ephemeral=True)
    

  @slash_command(name="hello", description="Say hi!", scopes=Constants.GUILD_IDS)
  @auto_defer()
  @utils.check_message_to_be_processed
  async def hello_cmd(self, ctx):
    """
    Callback for the hello command
    --
    input:
      ctx: interactions.SlashContext
    """
    index = random.randint(0, len(Constants.GREETINGS) - 1)
    await ctx.send(Constants.GREETINGS[index].format(ctx.author.mention))


  @slash_command(name="setup-channel", description="TBD", sub_cmd_name="main", sub_cmd_description="Change my default channel", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  async def setup_channel_main_cmd(self, ctx):
    """
    Callback for the setup-channnel main command
    --
    input:
      ctx: interactions.SlashContext
    """
    await ctx.send("Done!", ephemeral=True)
  
    # Saving the channel in the database in order not to need to do /setupChannel when rebooting
    db["out_channel"] = int(ctx.channel.id)
  
    channel = ctx.channel
    await channel.send("This channel is now my default channel")
  
    piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id=Cog_piflouz_mining.BUTTON_NAME, emoji=Constants.PIFLOUZ_EMOJI)
    
    embed = embed_messages.get_embed_piflouz()
  
    # Piflouz mining message
    message = await channel.send(embed=embed, components=piflouz_button)
    db["piflouz_message_id"] = int(message.id)
    db["current_season_message_id"] = int(message.id)
    await message.pin()
  

  @slash_command(name="setup-channel", description="TBD", sub_cmd_name="twitch", sub_cmd_description="Change the channel where I announce new lives", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  async def setup_channel_twitch_cmd(self, ctx):
    """
    Callback for the setup-channnel twitch command
    --
    input:
      ctx: interactions.SlashContext
    """
    db["twitch_channel"] = int(ctx.channel_id)
    await ctx.send("Done!", ephemeral=True)


  @slash_command(name="donate", description="Be generous to others", scopes=Constants.GUILD_IDS)
  @slash_option(name="user_receiver", description="Revceiver", opt_type=OptionType.USER, required=True)
  @slash_option(name="amount", description="How much you want to give", opt_type=OptionType.INTEGER, required=True, min_value=1)
  @slash_option(name="custom_message", description="Message to send with the donation", opt_type=OptionType.STRING, required=False)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def donate_cmd(self, ctx, user_receiver, amount, custom_message=""):
    """
    Callback for the donate command
    --
    input:
      ctx: interactions.SlashContext
      user_receiver: interactions.User
      amount: int
      custom_message: str
    """
    user_sender = ctx.author 
  
    # Trading
    await utils.custom_assert(piflouz_handlers.update_piflouz(user_sender.id, qty=-amount, check_cooldown=False), "Sender does not have enough money to donate", ctx)
  
    qty_tax = ceil(Constants.DONATE_TAX_RATIO / 100 * amount)
    qty_receiver = amount - qty_tax
  
    piflouz_handlers.update_piflouz(self.bot.user.id, qty=qty_tax, check_cooldown=False)
    piflouz_handlers.update_piflouz(user_receiver.id, qty=qty_receiver, check_cooldown=False)
  
    await ctx.send("Done!", ephemeral=True)
  
    channel = ctx.channel
    await channel.send(f"{user_sender.mention} sent {amount} {Constants.PIFLOUZ_EMOJI} to {user_receiver.mention}\nMessage from the sender: {custom_message}")
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("donation_successful", ctx.author.id, amount, user_receiver.id, self.bot.user.id)
  
    # Update the statistics to see the most generous donators
    id_sender = str(user_sender.id)
    id_receiver = str(user_receiver.id)
    if id_sender not in db["donation_balance"].keys():
      db["donation_balance"][id_sender] = 0
    if id_receiver not in db["donation_balance"].keys():
      db["donation_balance"][id_receiver] = 0
    
    db["donation_balance"][id_sender] += amount
    db["donation_balance"][id_receiver] -= qty_receiver


  @slash_command(name="joke", description="To laugh your ass off (or not, manage your expectations)", scopes=Constants.GUILD_IDS)
  @auto_defer()
  @utils.check_message_to_be_processed
  async def joke_cmd(self, ctx):
    """
    Callback for the joke command
    --
    input:
      ctx: interactions.SlashContext
    """
    joke = utils.get_new_joke()
    output_message = f"Here is a joke for you:\n{joke}"
    await ctx.send(output_message)


  @slash_command(name="giveaway", description="Drop a pibox with your own money", scopes=Constants.GUILD_IDS)
  @slash_option(name="amount", description="How many piflouz are inside the pibox", opt_type=OptionType.INTEGER, required=True, min_value=1)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def giveaway_cmd(self, ctx, amount):
    """
    Callback for the giveway command
    --
    input:
      ctx: interactions.SlashContext
      amount: int -> how many piflouz given
    """
    user_sender = ctx.author 
    
    # Trading
    await utils.custom_assert(piflouz_handlers.update_piflouz(user_sender.id, qty=-amount, check_cooldown=False), "Sender does not have enough money to giveaway", ctx)
    custom_message = f"This is a gift from the great {user_sender.mention}, be sure to thank them! "
    await piflouz_handlers.spawn_pibox(self.bot, amount, custom_message=custom_message, pibox_type=piflouz_handlers.Pibox_type.FROM_GIVEAWAY)
    await ctx.send("Done!", ephemeral=True)
  
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("giveaway_successful", ctx.author.id)


  @slash_command(name="spawn-pibox", description="The pibox master can spawn a pibox", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def spawn_pibox_cmd(self, ctx):
    """
    Callback for the spawn-pibox command
    --
    input:
      ctx: interactions.SlashContext
    """
    await utils.custom_assert(int(ctx.author.id) == Constants.PIBOX_MASTER_ID, "Only the pibox master can use this command", ctx)
    piflouz_quantity = random.randrange(Constants.MAX_PIBOX_AMOUNT)
    custom_message = "It was spawned by the pibox master"
    await piflouz_handlers.spawn_pibox(self.bot, piflouz_quantity, custom_message, piflouz_handlers.Pibox_type.FROM_PIBOX_MASTER)
    await ctx.send("Done!", ephemeral=True)
    

  @slash_command(name="role", description="TBD", sub_cmd_name="get", sub_cmd_description="Get a role", scopes=Constants.GUILD_IDS)
  @slash_option(name="role", description="Which role?", opt_type=OptionType.STRING, required=True, choices=[
    SlashCommandChoice(value=str(Constants.TWITCH_NOTIF_ROLE_ID), name="Twitch Notifications"),
    SlashCommandChoice(value=str(Constants.PIBOX_NOTIF_ROLE_ID), name="Pibox Notifications"),
    SlashCommandChoice(value=str(Constants.BIRTHDAY_NOTIF_ROLE_ID), name="Birthday Notifications"),
    SlashCommandChoice(value=str(Constants.CHAOS_ROLE_ID), name="CHAOS")
  ])
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def get_role_cmd(self, ctx, role):
    """
    Gives a role to the user
    --
    input:
      ctx: interactions.SlashContext
      role: str -> id of the role as a string. We use a string because the integer value of the role id is greater than integer arguments' upper bound
    """
    member = ctx.author
    await member.add_role(int(role))
    await ctx.send("Done!", ephemeral=True)
  

  @slash_command(name="role", description="TBD", sub_cmd_name="remove", sub_cmd_description="Remove a role", scopes=Constants.GUILD_IDS)
  @slash_option(name="role", description="Which role?", opt_type=OptionType.STRING, required=True, choices=[
    SlashCommandChoice(value=str(Constants.TWITCH_NOTIF_ROLE_ID), name="Twitch Notifications"),
    SlashCommandChoice(value=str(Constants.PIBOX_NOTIF_ROLE_ID), name="Pibox Notifications"),
    SlashCommandChoice(value=str(Constants.BIRTHDAY_NOTIF_ROLE_ID), name="Birthday Notifications"),
    SlashCommandChoice(value=str(Constants.CHAOS_ROLE_ID), name="CHAOS")
  ])
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def remove_role_cmd(self, ctx, role):
    """
    Removes a role from the user
    --
    input:
      ctx: interactions.SlashContext
      role: str -> id of the role as a string. We use a string because the integer value of the role id is greater than integer arguments' upper bound
    """
    member = ctx.author
    await member.remove_role(int(role))
    await ctx.send("Done!", ephemeral=True)


  @slash_command(name="pichapouche", description="Picha picha!", scopes=Constants.GUILD_IDS)
  @auto_defer()
  async def pichapouche_cmd(self, ctx):
    """
    Picha picha!
    --
    input:
      ctx: interactions.SlashContext
    """
    await ctx.send(f"Picha picha! {Constants.PIKADAB_EMOJI}")


  @message_context_menu(name="Du quoi ?", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  async def du_quoi_context_app(self, ctx):
    """
    Answers "Du quoi ?" to a message (probably in response to message containing the word "tarpin")
    --
    input:
      ctx: interactions.ContextMenuContext 
    """
    await ctx.target.reply("Du quoi ?")
    await ctx.send("Done!", ephemeral=True)
  
  
  @message_context_menu(name="Du tarpin !", scopes=Constants.GUILD_IDS)
  @auto_defer(ephemeral=True)
  async def du_tarpin_context_app(self, ctx):
    """
    Answers "Du tarpin !" to a message (probably in response to message containing "Du quoi ?")
    --
    input:
      ctx: interactions.ContextMenuContext 
    """
    await ctx.target.reply("Du tarpin !")
    await ctx.send("Done!", ephemeral=True)


  @slash_command(name="otter", description="Get a cute otter image", scopes=Constants.GUILD_IDS)
  @auto_defer()
  @utils.check_message_to_be_processed
  async def otter_cmd(self, ctx):
    """
    Callback for the /otter command
    --
    input:
      ctx: interactions.SlashContext
    """
    embed = await embed_messages.get_embed_otter(title="Look at this cute otter!")
    await ctx.send(embeds=embed)


  @slash_command(name="reboot", description="DEAD", scopes=Constants.GUILD_IDS)
  async def reboot_cmd(self, ctx):
    """
    Stops the bot
    """
    exit(1)
    

def setup(bot):
  Cog_misc(bot)