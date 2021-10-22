from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import SlashCommandOptionType as option_type
from replit import db
from math import ceil

from constant import Constants
import piflouz_handlers
import utils


class Cog_duels(commands.Cog):
  """
  Cog containing all the interactions related to duels
  ---
  fields:
    bot: discord.ext.commands.Bot
  """

  def __init__(self, bot):
    self.bot = bot
  

  @cog_ext.cog_subcommand(base="duel", name="challenge", description="Duel someone to earn piflouz!", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="amount", description="How much do you want to bet?", required=True, option_type=option_type.INTEGER),
    create_option(name="duel_type", description="What game do you want to play?", required=True, option_type=option_type.STRING, choices=[
      create_choice("Shifumi", "Shifumi")
    ]),
    create_option(name="user", description="Who do you want to duel? Leave empty to duel anyone", required=False, option_type=option_type.USER),
  ])
  @utils.check_message_to_be_processed
  async def duel_challenge_cmd(self, ctx, amount, duel_type, user=None):
    """
    Callback for the duel challenge command
    --
    input:
      ctx: discord.ext.commands.Context
      amount: int -> how many piflouz involved by both users
      duel_type: string -> what kind of duel
      user: discord.User -> the person challenged
    """
    await ctx.defer(hidden=True)
    assert ctx.author != user, "You can't challenge yourself!"

    assert amount > 0, "The amount must be at least 1"
    assert piflouz_handlers.update_piflouz(ctx.author_id, qty=-amount, check_cooldown=False), "You don't have enough piflouz to do that"

    id_challenged = -1 if user is None else user.id

    new_duel = utils.create_duel(ctx.author_id, id_challenged, amount, duel_type)
    db["duels"].append(new_duel)

    mention = "anyone" if user is None else user.mention

    await ctx.channel.send(f"{ctx.author.mention} challenged {mention} at {duel_type} betting {amount} {Constants.PIFLOUZ_EMOJI}! Use `/duel accept {new_duel['duel_id']}` to accept or `/duel deny {new_duel['duel_id']}` to deny.")
    await ctx.send("Done!", hidden=True)
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("duel_created", ctx.author_id, id_challenged, amount, duel_type)


  @cog_ext.cog_subcommand(base="duel", name="accept", description="Accept someone's challenge", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="duel_id", description="The id of the duel (see the duel announcement message)", required=True, option_type=option_type.INTEGER)
  ])
  @utils.check_message_to_be_processed
  async def duel_accept_cmd(self, ctx, duel_id):
    """
    Callback for the duel accept command
    --
    input:
      ctx: discord.ext.commands.Context
      duel_id: int
    """
    await ctx.defer(hidden=True)

    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["duel_id"] == duel_id:
        duel_index = i
        break
    
    # Check the duel exists
    assert duel_index is not None, "This duel does not exist"

    # Check that the duel is still available
    assert not duel["accepted"], "This challenge has already been accepted"

    # Check that you are a target of the duel
    assert duel["user_id2"] == ctx.author_id or duel["user_id2"] == -1, "You are not targeted by this duel"

    # Check that you are not the one who made the challenge
    assert duel["user_id1"] != ctx.author_id, "You can't challenge yourself!"

    # Check the user has enough money
    assert piflouz_handlers.update_piflouz(ctx.author_id, qty=-duel["amount"], check_cooldown=False), "You don't have enough piflouz to do that"

    db["duels"][duel_index]["accepted"] = True
    db["duels"][duel_index]["user_id2"] = ctx.author_id
    duel_type = duel["duel_type"]

    await ctx.channel.send(f"{ctx.author.mention} accepted <@{duel['user_id1']}>'s challenge! Use `/duel play {duel_type} {duel['duel_id']} [your move]`")
    await ctx.send("Done!", hidden=True)
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("duel_accepted", ctx.author_id, duel_id)


  @cog_ext.cog_subcommand(base="duel", name="deny", description="Deny someone's challenge", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="duel_id", description="The id of the duel (see the duel announcement message)", required=True, option_type=option_type.INTEGER)
  ])
  @utils.check_message_to_be_processed
  async def duel_deny_cmd(self, ctx, duel_id):
    """
    Callback for the duel deny command
    --
    input:
      ctx: discord.ext.commands.Context
      duel_id: int
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["duel_id"] == duel_id:
        duel_index = i
        break
    
    assert duel_index is not None, "This duel does not exist"
    assert not duel["accepted"], "You already accepted this challenge"
    assert duel["user_id2"] != -1 , "You can't deny a challenge at anyone"
    assert duel["user_id2"] == ctx.author_id, "You are not targeted by this duel"

    # Give back the money to the challenger
    piflouz_handlers.update_piflouz(duel["user_id1"], qty=duel["amount"], check_cooldown=False)

    del db["duels"][duel_index]
    await ctx.channel.send(f"{ctx.author.mention} denied <@{duel['user_id1']}>'s challenge!")
    await ctx.send("Done", hidden=True)
    await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(base="duel", name="cancel", description="Cancel your challenge to someone", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="duel_id", description="The id of the duel (see the duel announcement message)", required=True, option_type=option_type.INTEGER)
  ])
  @utils.check_message_to_be_processed
  async def duel_cancel_cmd(self, ctx, duel_id):
    """
    Callback for the duel cancel command
    --
    input:
      ctx: discord.ext.commands.Context
      duel_id: int
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["duel_id"] == duel_id:
        duel_index = i
        break
    
    assert duel_index is not None, "This duel does not exist"
    assert not duel["accepted"], "The duel was already accepted"
    assert duel["user_id1"] == ctx.author_id, "You did not create this challenge"

    # Give back the money to the challenger
    piflouz_handlers.update_piflouz(ctx.author_id, qty=duel["amount"], check_cooldown=False)

    del db["duels"][duel_index]

    mention = "anyone" if duel["user_id2"] == -1 else f"<@{duel['user_id2']}>"

    await ctx.channel.send(f"{ctx.author.mention} cancelled his/her challenge to {mention}, what a loser")
    await ctx.send("Done!", hidden=True)
    await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(name="shifumi", base="duel", subcommand_group="play", description="Play shifumi!", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="duel_id", description="The id of the duel (see the duel announcement message)", required=True, option_type=option_type.INTEGER),
    create_option(name="value", description="What do you want to play?", required=True, option_type=option_type.STRING, choices=[
        create_choice("Rock", "Rock"),
        create_choice("Paper", "Paper"),
        create_choice("Scissors", "Scissors")
      ]
    )
  ])
  @utils.check_message_to_be_processed
  async def duel_play_shifumi_cmd(self, ctx, duel_id, value):
    """
    Callback for the duel accept command
    --
    input:
      ctx: discord.ext.commands.Context
      duel_id: int
      value: string -> the move played by the player
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["duel_id"] == duel_id:
        duel_index = i
        break
    
    assert duel_index is not None, "This duel does not exist"
    assert duel["accepted"], "This duel is not accepted yet"
    assert ctx.author_id in [duel["user_id1"], duel["user_id2"]], "You are not part of this challenge"

    if duel["user_id1"] == ctx.author_id:
      assert duel["move1"] is None, "You already played!"
      db["duels"][duel_index]["move1"] = value
      id1 = ctx.author_id
      id2 = duel["user_id2"]
    else:
      assert duel["move2"] is None, "You already played!"
      db["duels"][duel_index]["move2"] = value
      id1 = duel["user_id1"]
      id2 = ctx.author_id
    
    await ctx.send("Done! Just wait for the other player to make a move", hidden=True)

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

        await ctx.channel.send(f"<@{id1}> and <@{id2}> tied at {duel['duel_type']}! They both played {move1}! They both got their money back")
        self.bot.dispatch("duel_tie", id1, id2, duel["amount"], duel["duel_type"])

      # Player 1 won
      elif win_shifumi[move1] == move2:
        piflouz_handlers.update_piflouz(id1, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.user.id, qty=money_tax, check_cooldown=False)

        await ctx.channel.send(f"<@{id1}> won at {duel['duel_type']} against <@{id2}>, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move1} vs {move2}")
        self.bot.dispatch("duel_won", id1, id2, duel["amount"], duel["duel_type"])

      
      # Player 2 won
      else:
        piflouz_handlers.update_piflouz(id2, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.user.id, qty=money_tax, check_cooldown=False)

        await ctx.channel.send(f"<@{id2}> won at {duel['duel_type']} against <@{id1}>, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move2} vs {move1}")
        self.bot.dispatch("duel_won", id2, id1, duel["amount"], duel["duel_type"])


      del db["duels"][duel_index]
      await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(base="duel", name="status", description="Check your ongoing duels", guild_ids=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def duel_status_cmd(self, ctx):
    """
    Callback for the duel status command
    --
    input:
      ctx: discord.ext.commands.Context
    """
    await ctx.defer(hidden=True)

    my_duels = filter(lambda duel: ctx.author_id in [duel["user_id1"], duel["user_id2"]] or duel["user_id2"] == -1, db["duels"])

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
      await ctx.send("You have no ongoing duels", hidden=True)
    
    else:
      msg = "Here are your ongoing duels:\n" + "\n".join(msgs)
      await ctx.send(msg, hidden=True)