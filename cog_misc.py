from interactions import extension_command, Extension, Emoji, Option, OptionType, Button, ButtonStyle, Choice, ApplicationCommandType
from math import ceil
import random
from replit import db

from cog_piflouz_mining import Cog_piflouz_mining
from constant import Constants
import embed_messages
import events
import piflouz_handlers
import powerups  # Used in eval
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
    /raffle
    /giveaway
    /spawn-pibox
    /role [get | remove]
    /pichapouche
  Message commands:
    Du quoi?
    Du tarpin !
  """

  def __init__(self, bot):
    self.bot = bot


  @extension_command(name="help", description="Show the help message", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def help_cmd(self, ctx):
    """
    Callback for the help command
    --
    input:
      ctx: interactions.CommandContext
    """
    await ctx.send(f"Here is some help. Hopes you understand me better after reading this! {Constants.PIFLOUZ_EMOJI}\n", embeds=embed_messages.get_embed_help_message(), ephemeral=True)


  @extension_command(name="hello", description="Say hi!", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def hello_cmd(self, ctx):
    """
    Callback for the hello command
    --
    input:
      ctx: interactions.CommandContext
    """
    index = random.randint(0, len(Constants.GREETINGS) - 1)
    await ctx.send(Constants.GREETINGS[index].format(ctx.author.user.mention))


  @extension_command(name="setup-channel", description="TBD", scope=Constants.GUILD_IDS, options=[
    Option(name="main", description="Change my default channel", type=OptionType.SUB_COMMAND, options=[]),
    Option(name="twitch", description="Change the channel where I announce new lives", type=OptionType.SUB_COMMAND, options=[])
  ])
  async def setup_channel_cmd_group_dispatch(self, ctx):
    """
    Dispatches the interaction for a /setup-channel depending on the sub command
    --
    input:
      ctx: interactions.CommandContext
    """
    sub_command = ctx.data.options[0].name
    if sub_command == "main":
      await self.setup_channel_main_cmd(ctx)
    elif sub_command == "twitch":
      await self.setup_channel_twitch_cmd(ctx)


  async def setup_channel_main_cmd(self, ctx):
    """
    Callback for the setup-channnel main command
    --
    input:
      ctx: interactions.CommandContext
    """
    await ctx.send("Done!", ephemeral=True)
  
    # Saving the channel in the database in order not to need to do /setupChannel when rebooting
    db["out_channel"] = int(ctx.channel_id)
  
    channel = await ctx.get_channel()
  
    await channel.send("This channel is now my default channel")
  
    piflouz_button = Button(style=ButtonStyle.SECONDARY, label="", custom_id=Cog_piflouz_mining.button_name, emoji=Emoji(id=Constants.PIFLOUZ_EMOJI_ID)._json)
    
    embed = embed_messages.get_embed_piflouz(self.bot)
  
    # Piflouz mining message
    message = await ctx.channel.send(embeds=embed, components=piflouz_button)
    db["piflouz_message_id"] = int(message.id)
    db["current_season_message_id"] = int(message.id)
    await message.pin()
  
  
  async def setup_channel_twitch_cmd(self, ctx):
    """
    Callback for the setup-channnel twitch command
    --
    input:
      ctx: interactions.CommandContext
    """
    db["twitch_channel"] = int(ctx.channel_id)
    await ctx.send("Done!", ephemeral=True)


  @extension_command(name="donate", description="Be generous to others", scope=Constants.GUILD_IDS, options=[
    Option(name="user_receiver", description="Revceiver", type=OptionType.USER, required=True),
    Option(name="amount", description="How much you want to give", type=OptionType.INTEGER, required=True, min_value=1)
  ])
  @utils.check_message_to_be_processed
  async def donate_cmd(self, ctx, user_receiver, amount):
    """
    Callback for the donate command
    --
    input:
      ctx: interactions.CommandContext
      user_receiver: interactions.User
      amount: int
    """
    await ctx.defer(ephemeral=True)
  
    user_sender = ctx.author 
  
    # Trading
    assert piflouz_handlers.update_piflouz(user_sender.id, qty=-amount, check_cooldown=False), "Sender does not have enough money to donate"
  
    qty_tax = ceil(Constants.DONATE_TAX_RATIO / 100 * amount)
    qty_receiver = amount - qty_tax
  
    piflouz_handlers.update_piflouz(self.bot.me.id, qty=qty_tax, check_cooldown=False)
    piflouz_handlers.update_piflouz(user_receiver.id, qty=qty_receiver, check_cooldown=False)
  
    await ctx.send("Done!", ephemeral=True)
  
    channel = await ctx.get_channel()
    await channel.send(f"{user_sender.mention} sent {amount} {Constants.PIFLOUZ_EMOJI} to {user_receiver.mention}")
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("donation_successful", ctx.author.id, amount, user_receiver.id)
  
    # Update the statistics to see the most generous donators
    id_sender = str(user_sender.id)
    id_receiver = str(user_receiver.id)
    if id_sender not in db["donation_balance"].keys():
      db["donation_balance"][id_sender] = 0
    if id_receiver not in db["donation_balance"].keys():
      db["donation_balance"][id_receiver] = 0
    
    db["donation_balance"][id_sender] += amount
    db["donation_balance"][id_receiver] -= qty_receiver


  @extension_command(name="joke", description="To laugh your ass off (or not, manage your expectations)", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def joke_cmd(self, ctx):
    """
    Callback for the joke command
    --
    input:
      ctx: interactions.CommandContext
    """
    joke = utils.get_new_joke()
    output_message = f"Here is a joke for you:\n{joke}"
    await ctx.send(output_message)


  @extension_command(name="raffle", description=f"Buy raffle tickets to test your luck /!\ Costs piflouz", scope=Constants.GUILD_IDS, options=[
    Option(name="nb_tickets", description="How many tickets?", type=OptionType.INTEGER, required=True, min_value=1)
  ])
  @utils.check_message_to_be_processed
  async def raffle_cmd(self, ctx, nb_tickets):
    """
    Callback for the raffle command
    --
    input:
      ctx: interactions.CommandContext
      nb_tickets: int
    """
    await ctx.defer(ephemeral=True)
    assert "current_event" in db.keys(), "No current event registered"
  
    current_event = eval(db["current_event"])
    assert isinstance(current_event, events.Raffle_event), "Current event is not a raffle"
  
    price = nb_tickets * current_event.ticket_price
    
    user_id = str(ctx.author.id)
  
    # user doesn't have enough money
    assert piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False), f"User {ctx.author} doesn't have enough money to buy {nb_tickets} tickets"
    
    if not user_id in db["raffle_participation"].keys():
      db["raffle_participation"][user_id] = 0
    db["raffle_participation"][user_id] += nb_tickets
  
    await ctx.send(f"Successfully bought {nb_tickets} tickets", ephemeral=True)
    await current_event.update_raffle_message(self.bot)
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("raffle_participation_successful", ctx.author.id, nb_tickets)


  @extension_command(name="giveaway", description="Drop a pibox with your own money", scope=Constants.GUILD_IDS, options=[
    Option(name="amount", description="How many piflouz are inside the pibox", type=OptionType.INTEGER, required=True, min_value=1)
  ])
  @utils.check_message_to_be_processed
  async def giveaway_cmd(self, ctx, amount):
    """
    Callback for the giveway command
    --
    input:
      ctx: interactions.CommandContext
      amount: int -> how many piflouz given
    """
    await ctx.defer(ephemeral=True)
  
    user_sender = ctx.author 
    
    # Trading
    assert piflouz_handlers.update_piflouz(user_sender.id, qty=-amount, check_cooldown=False), "Sender does not have enough money to giveaway"
    custom_message = f"This is a gift from the great {user_sender.mention}, be sure to thank them! "
    await piflouz_handlers.spawn_pibox(self.bot, amount, custom_message=custom_message)
    await ctx.send("Done!", ephemeral=True)
  
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("giveaway_successful", ctx.author.id)


  @extension_command(name="spawn-pibox", description="The pibox master can spawn a pibox", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def spawn_pibox_cmd(self, ctx):
    """
    Callback for the spawn-pibox command
    --
    input:
      ctx: interactions.CommandContext
    """
    assert int(ctx.author.id) == Constants.PIBOX_MASTER_ID, "Only the pibox master can use this command"
    piflouz_quantity = random.randrange(Constants.MAX_PIBOX_AMOUNT)
    custom_message = "It was spawned by the pibox master"
    await piflouz_handlers.spawn_pibox(self.bot, piflouz_quantity, custom_message)
    await ctx.send("Done!", ephemeral=True)


  @extension_command(name="role", description="TBD", scope=Constants.GUILD_IDS, options=[
    Option(name="get", description="Get a role", type=OptionType.SUB_COMMAND, options=[
      Option(name="role", description="Which role?", type=OptionType.STRING, required=True, choices=[
        Choice(value=str(Constants.TWITCH_NOTIF_ROLE_ID), name="Twitch Notifications"),
        Choice(value=str(Constants.PIBOX_NOTIF_ROLE_ID), name="Pibox Notifications"),
      ])
    ]),
    Option(name="remove", description="Remove a role", type=OptionType.SUB_COMMAND, options=[
      Option(name="role", description="Which role?", type=OptionType.STRING, required=True, choices=[
        Choice(value=str(Constants.TWITCH_NOTIF_ROLE_ID), name="Twitch Notifications"),
        Choice(value=str(Constants.PIBOX_NOTIF_ROLE_ID), name="Pibox Notifications")
      ])
    ])
  ])
  @utils.check_message_to_be_processed
  async def role_cmd_group_dispatch(self, ctx, sub_command, role):
    """
    Dispatches the interaction for a /role depending on the subcommand
    --
    input:
      ctx: interactions.CommandContext
      sub_command: str
      role: str
    """
    if sub_command == "get": await self.get_role_cmd(ctx, role)
    elif sub_command == "remove": await self.remove_role_cmd(ctx, role)


  async def get_role_cmd(self, ctx, role):
    """
    Gives a role to the user
    --
    input:
      ctx: interactions.CommandContext
      role: str -> id of the role as a string. We use a string because the integer value of the role id is greater than integer arguments' upper bound
    """
    member = ctx.author
    await member.add_role(role=int(role), guild_id=ctx.guild_id)
    await ctx.send("Done!", ephemeral=True)
  
  
  async def remove_role_cmd(self, ctx, role):
    """
    Gives a role to the user
    --
    input:
      ctx: interactions.CommandContext
      role: str -> id of the role as a string. We use a string because the integer value of the role id is greater than integer arguments' upper bound
    """
    member = ctx.author
    await member.remove_role(role=int(role), guild_id=ctx.guild_id)
    await ctx.send("Done!", ephemeral=True)


  @extension_command(name="pichapouche", description="Picha picha!", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def pichapouche_cmd(self, ctx):
    """
    Picha picha!
    --
    input:
      ctx: interactions.CommandContext
    """
    await ctx.send("Picha picha! <:pikadab:687208856719196161>")


  @extension_command(type=ApplicationCommandType.MESSAGE, name="Du quoi ?", scope=Constants.GUILD_IDS)
  async def du_quoi_context_app(self, ctx):
    """
    Answers "Du quoi ?" to a message (probably in response to message containing the word "tarpin")
    --
    input:
      ctx: discord_slash.context.MenuContext
    """
    ctx.target._client = self.bot._http
    await ctx.target.reply("Du quoi ?")
    await ctx.send("Done!", ephemeral=True)
  
  
  @extension_command(type=ApplicationCommandType.MESSAGE, name="Du tarpin !", scope=Constants.GUILD_IDS)
  async def du_tarpin_context_app(self, ctx):
    """
    Answers "Du tarpin !" to a message (probably in response to message containing "Du quoi ?")
    --
    input:
      ctx: discord_slash.context.MenuContext
    """
    ctx.target._client = self.bot._http
    await ctx.target.reply("Du tarpin !")
    await ctx.send("Done!", ephemeral=True)


def setup(bot):
  Cog_misc(bot)