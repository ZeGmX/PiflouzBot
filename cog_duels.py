from interactions import extension_command, Extension, OptionType, Choice, option, autodefer, Button, ButtonStyle, Emoji, extension_component
from replit import db
from math import ceil

from constant import Constants
import piflouz_handlers
import utils


class Cog_duels(Extension):
  """
  Cog containing all the interactions related to duels
  --
  fields:
    bot: interactions.Client
  --
  Slash commands:  
    /duel challenge
    /duel play Shifumi
    /duel status
  Components:
    duel_accept_button_name
    duel_deny_button_name
    duel_cancel_button_name
  """
  duel_accept_button_name = "duel_accept"
  duel_deny_button_name = "duel_deny"
  duel_cancel_button_name = "duel_cancel"

  def __init__(self, bot):
    self.bot = bot


  @extension_command(name="duel", description="TBD", scope=Constants.GUILD_IDS)
  async def duel_cmd(self, ctx):
    """
    Callback for the duel command
    --
    input:
      ctx: interactions.CommandContext
    """
    pass
  

  @duel_cmd.subcommand(name="challenge", description="Duel someone to earn piflouz!")
  @option(name="amount", description="How much do you want to bet?", required=True, type=OptionType.INTEGER, min_value=1)
  @option(name="duel_type", description="What game do you want to play?", required=True, type=OptionType.STRING, choices=[
        Choice(name="Shifumi", value="Shifumi")
      ])
  @option(name="user", description="Who do you want to duel? Leave empty to duel anyone", required=False, type=OptionType.USER)
  @autodefer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def duel_challenge_cmd(self, ctx, amount, duel_type, user=None):
    """
    Callback for the duel challenge subcommand
    --
    input:
      ctx: interactions.CommandContext
      amount: int -> how many piflouz involved by both users
      duel_type: string -> what kind of duel
      user: interactions.User -> the person challenged
    """
    await utils.custom_assert(user is None or int(ctx.author.id) != int(user.id), "You can't challenge yourself!", ctx)

    await utils.custom_assert(piflouz_handlers.update_piflouz(ctx.author.id, qty=-amount, check_cooldown=False), "You don't have enough piflouz to do that", ctx)

    id_challenged = -1 if user is None else int(user.id)  

    new_duel = utils.create_duel(int(ctx.author.id), id_challenged, amount, duel_type)
    
    mention = "anyone" if user is None else user.mention

    buttons = [
      Button(style=ButtonStyle.SUCCESS, label="", custom_id=Cog_duels.duel_accept_button_name, emoji=Emoji(name="✅")),
      Button(style=ButtonStyle.DANGER, label="", custom_id=Cog_duels.duel_deny_button_name, emoji=Emoji(name="❎")),
      Button(style=ButtonStyle.SECONDARY, label="", custom_id=Cog_duels.duel_cancel_button_name, emoji=Emoji(name="🚫"))
    ]

    channel = await ctx.get_channel()
    msg = await channel.send(f"{ctx.author.mention} challenged {mention} at {duel_type} betting {amount} {Constants.PIFLOUZ_EMOJI}! Click the green button below to accept or click the red one to deny. Click the gray one to cancel the challenge.", components=buttons)

    opponent_name = "anyone" if user is None else user.name

    thread = await msg.create_thread(f"{new_duel['duel_type']} duel - {ctx.author.name} vs {opponent_name}")
    await thread.add_member(ctx.author.id)
    if user is not None: await thread.add_member(user.id)

    new_duel["message_id"] = int(msg.id)
    new_duel["thread_id"] = int(thread.id)
    db["duels"].append(new_duel)

    await ctx.send("Done!", ephemeral=True)
    
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("duel_created", ctx.author.id, id_challenged, amount, duel_type)


  @extension_component(duel_accept_button_name)
  @autodefer(ephemeral=True)
  async def duel_accept_button_callback(self, ctx):
    """
    Callback for the button that accepts a duel
    --
    input:
      ctx: interactions.ComponentContext
    """
    msg_id = int(ctx.message.id)

    # Finding the right duel
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["message_id"] == msg_id:
        duel_index = i
        break

    await utils.custom_assert(duel_index is not None, "Could not find the duel", ctx)
    
    # Check that the duel is still available
    await utils.custom_assert(not duel["accepted"], "This challenge has already been accepted", ctx)

    # Check that you are a target of the duel
    await utils.custom_assert(duel["user_id2"] == int(ctx.author.id) or duel["user_id2"] == -1, "You are not targeted by this duel", ctx)

    # Check that you are not the one who made the challenge
    await utils.custom_assert(duel["user_id1"] != int(ctx.author.id), "You can't challenge yourself!", ctx)

    # Check the user has enough money
    await utils.custom_assert(piflouz_handlers.update_piflouz(ctx.author.id, qty=-duel["amount"], check_cooldown=False), "You don't have enough piflouz to do that", ctx)

    db["duels"][duel_index]["accepted"] = True
    db["duels"][duel_index]["user_id2"] = int(ctx.author.id)
    duel_type = duel["duel_type"]

    duel_id = duel["duel_id"]

    thread_id = duel["thread_id"]
    thread = await self.bot.get_channel(thread_id)
    await thread.add_member(ctx.author.id)

    await thread.send(f"{ctx.author.mention} accepted <@{duel['user_id1']}>'s challenge! Use `/duel play {duel_type} [your move]`")
    await thread.modify(name=f"[Accepted] {thread.name}")
    await ctx.disable_all_components()
    await ctx.send("Done!", ephemeral=True)
    
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("duel_accepted", int(ctx.author.id), duel_id)
    
  
  @extension_component(duel_deny_button_name)
  @autodefer(ephemeral=True)
  async def duel_deny_button_callback(self, ctx):
    """
    Callback for the button that denies a duel
    --
    input:
      ctx: interactions.ComponentContext
    """
    msg_id = int(ctx.message.id)

    # Finding the right duel
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["message_id"] == msg_id:
        duel_index = i
        break
    
    await utils.custom_assert(duel_index is not None, "This duel does not exist", ctx)
    await utils.custom_assert(not duel["accepted"], "You already accepted this challenge", ctx)
    await utils.custom_assert(duel["user_id2"] != -1 , "You can't deny a challenge at anyone", ctx)
    await utils.custom_assert(duel["user_id2"] == int(ctx.author.id), "You are not targeted by this duel", ctx)

    # Give back the money to the challenger
    piflouz_handlers.update_piflouz(duel["user_id1"], qty=duel["amount"], check_cooldown=False)

    del db["duels"][duel_index]

    thread_id = duel["thread_id"]
    thread = await self.bot.get_channel(thread_id)
    await thread.send(f"{ctx.author.mention} denied <@{duel['user_id1']}>'s challenge!")
    await thread.modify(name=f"[Denied] {thread.name}")
    await thread.archive()
    await ctx.disable_all_components()
    
    await ctx.send("Done", ephemeral=True)
    await utils.update_piflouz_message(self.bot)


  @extension_component(duel_cancel_button_name)
  @autodefer(ephemeral=True)
  async def duel_cancel_button_callback(self, ctx):
    """
    Callback for the button that denies a duel
    --
    input:
      ctx: interactions.ComponentContext
    """
    msg_id = int(ctx.message.id)

    # Finding the right duel
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["message_id"] == msg_id:
        duel_index = i
        break
    
    await utils.custom_assert(duel_index is not None, "This duel does not exist", ctx)
    await utils.custom_assert(not duel["accepted"], "The duel was already accepted", ctx)
    await utils.custom_assert(duel["user_id1"] == int(ctx.author.id), "You did not create this challenge", ctx)

    # Give back the money to the challenger
    piflouz_handlers.update_piflouz(ctx.author.id, qty=duel["amount"], check_cooldown=False)

    del db["duels"][duel_index]

    mention = "anyone" if duel["user_id2"] == -1 else f"<@{duel['user_id2']}>"

    thread_id = duel["thread_id"]
    thread = await self.bot.get_channel(thread_id)
    await thread.send(f"{ctx.author.mention} cancelled their challenge to {mention}, what a loser")
    await thread.modify(name=f"[Cancelled] {thread.name}")
    await thread.archive()
    await ctx.disable_all_components()
    
    await ctx.send("Done!", ephemeral=True)
    await utils.update_piflouz_message(self.bot)


  @duel_cmd.subcommand(name="status", description="Check your ongoing duels")
  @autodefer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def duel_status_cmd(self, ctx):
    """
    Callback for the duel subcommand command
    --
    input:
      ctx: interactions.CommandContext
    """
    my_duels = filter(lambda duel: int(ctx.author.id) in [duel["user_id1"], duel["user_id2"]] or duel["user_id2"] == -1, db["duels"])

    msgs = []
    for duel in my_duels:
      mention = "anyone" if duel["user_id2"] == -1 else f"<@{duel['user_id2']}>"
      s = f"id: {duel['duel_id']} - <@{duel['user_id1']}> vs {mention} - {duel['duel_type']} - {duel['amount']} {Constants.PIFLOUZ_EMOJI}\n"
      
      if not duel["accepted"]:
        s += f"Waiting on {mention} to accept\n"
      else:
        if duel["move1"] is None:
          s += f"Waiting on <@{duel['user_id1']}> to play\n"
        if duel["move2"] is None:
          s += f"Waiting on <@{duel['user_id2']}> to play\n"
      
      msgs.append(s)
    
    if len(msgs) == 0:
      await ctx.send("You have no ongoing duels", ephemeral=True)
    
    else:
      msg = "Here are your ongoing duels:\n" + "\n".join(msgs)
      await ctx.send(msg, ephemeral=True)


  @duel_cmd.group(name="play", description="TBD")
  async def duel_cmd_group_cmd(self, ctx):
    """
    Callback for the duel play command group
    --
    input:
      ctx: interactions.CommandContext
    """
    pass


  @duel_cmd_group_cmd.subcommand(name="shifumi", description="Play shifumi!")
  @option(name="value", description="What do you want to play?", required=True, type=OptionType.STRING, choices=[
    Choice(name="Rock", value="Rock"),
    Choice(name="Paper", value="Paper"),
    Choice(name="Scissors", value="Scissors")
  ])
  @autodefer(ephemeral=True)
  async def duel_play_shifumi_cmd(self, ctx, value):
    """
    Callback for the duel play shifumi subcommand
    --
    input:
      ctx: interactions.CommandContext
      value: string -> the move played by the player
    """
    thread = await ctx.get_channel()
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["thread_id"] == int(thread.id):
        duel_index = i
        break
    
    await utils.custom_assert(duel_index is not None, "You are not inside an ongoing duel thread", ctx)
    await utils.custom_assert(duel["accepted"], "This duel is not accepted yet", ctx)
    await utils.custom_assert(int(ctx.author.id) in [duel["user_id1"], duel["user_id2"]], "You are not part of this challenge", ctx)

    if duel["user_id1"] == ctx.author.id:
      await utils.custom_assert(duel["move1"] is None, "You already played!", ctx)
      db["duels"][duel_index]["move1"] = value
      id1 = int(ctx.author.id)
      id2 = duel["user_id2"]
    else:
      await utils.custom_assert(duel["move2"] is None, "You already played!", ctx)
      db["duels"][duel_index]["move2"] = value
      id1 = duel["user_id1"]
      id2 = int(ctx.author.id)
    
    await ctx.send("Done! Just wait for the other player to make a move", ephemeral=True)

    user1 = await ctx.guild.get_member(id1)
    user2 = await ctx.guild.get_member(id2)

    move1 = db["duels"][duel_index]["move1"]
    move2 = db["duels"][duel_index]["move2"]

    total_money = 2 * duel["amount"]
    money_tax = ceil(total_money * Constants.DUEL_TAX_RATIO / 100)
    money_if_win = total_money - money_tax

    win_shifumi = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
    if move1 is not None and move2 is not None:
      # Tie, everyone gets all of their money back
      if move1 == move2:
        piflouz_handlers.update_piflouz(id1, qty=duel["amount"], check_cooldown=False)
        piflouz_handlers.update_piflouz(id2, qty=duel["amount"], check_cooldown=False)
          
        await thread.send(f"{user1.mention} and {user2.mention} tied at {duel['duel_type']}! They both played {move1}! They both got their money back")
        await thread.modify(f"[Tie] {thread.name[11:]}") # We remove the [Accepted]
        self.bot.dispatch("duel_tie", id1, id2, duel["amount"], duel["duel_type"])

      # Player 1 won
      elif win_shifumi[move1] == move2:
        piflouz_handlers.update_piflouz(id1, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.me.id, qty=money_tax, check_cooldown=False)

        await thread.send(f"{user1.mention} won at {duel['duel_type']} against {user2.mention}, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move1} vs {move2}")
        await thread.modify(f"[{user1.name} won] {thread.name[11:]}") # We remove the [Accepted]
        self.bot.dispatch("duel_won", id1, id2, duel["amount"], duel["duel_type"])

      
      # Player 2 won
      else:
        piflouz_handlers.update_piflouz(id2, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.me.id, qty=money_tax, check_cooldown=False)

        await thread.send(f"{user2.mention} won at {duel['duel_type']} against {user1.mention}, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move2} vs {move1}")
        await thread.modify(f"[{user2.name} won] {thread.name[11:]}") # We remove the [Accepted]
        self.bot.dispatch("duel_won", id2, id1, duel["amount"], duel["duel_type"])

      await thread.archive()

      del db["duels"][duel_index]
      await utils.update_piflouz_message(self.bot)


def setup(bot):
  Cog_duels(bot)