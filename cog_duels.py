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
    create_option(name="user", description="Who do you want to duel?", required=True, option_type=option_type.USER),
    create_option(name="amount", description="How much do you want to bet?", required=True, option_type=option_type.INTEGER),
    create_option(name="duel_type", description="What game do you want to play?", required=True, option_type=option_type.STRING, choices=[
      create_choice("Shifumi", "Shifumi")
    ]),
  ])
  @utils.check_message_to_be_processed
  async def duel_challenge_cmd(self, ctx, user, amount, duel_type):
    """
    Callback for the duel challenge command
    --
    input:
      ctx: discord.ext.commands.Context
      user: discord.User -> the person challenged
      amount: int -> how many piflouz involved by both users
      duel_type: string -> what kind of duel
    """
    await ctx.defer(hidden=True)
    assert ctx.author != user, "You can't challenge yourself!"

    # Check if there is no duel with the person
    assert not any(duel["user_id1"] == ctx.author_id and duel["user_id2"] == user.id for duel in db["duels"]), "You already challenged this person to a duel, finish this one first"
    assert not any(duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id for duel in db["duels"]), "This person already challenged you to a duel, finish this one first"

    assert user != ctx.author, "You can't challenge yourself"

    # Check that the challenger has enough money
    assert piflouz_handlers.update_piflouz(ctx.author_id, qty=-amount, check_cooldown=False), "You don't have enough piflouz to do that"

    new_duel = utils.create_duel(ctx, user, amount, duel_type)
    db["duels"].append(new_duel)

    await ctx.channel.send(f"{ctx.author.mention} challenged {user.mention} at {duel_type} betting {amount} {Constants.PIFLOUZ_EMOJI}! Use `/duel accept @{ctx.author.name}` to accept or `/duel deny @{ctx.author.name}` to deny.")
    await ctx.send("Done!", hidden=True)
    await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(base="duel", name="accept", description="Accept someone's challenge", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="user", description="The person who challenged you", required=True, option_type=option_type.USER)
  ])
  @utils.check_message_to_be_processed
  async def duel_accept_cmd(self, ctx, user):
    """
    Callback for the duel accept command
    --
    input:
      ctx: discord.ext.commands.Context
      user: discord.User -> the person challenged
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id:
        duel_index = i
        break
    
    # Check the duel exists
    assert duel_index is not None, "This person did not challenge you to a duel"

    # Check the user has enough money
    assert piflouz_handlers.update_piflouz(ctx.author_id, qty=-db["duels"][duel_index]["amount"], check_cooldown=False), "You don't have enough piflouz to do that"

    # Check that the user didn't already accept the duel
    assert not db["duels"][duel_index]["accepted"], "You already accepted this challenge"

    db["duels"][duel_index]["accepted"] = True
    duel_type = db["duels"][duel_index]["duel_type"]

    await ctx.channel.send(f"{ctx.author.mention} accepted {user.mention}'s challenge! Use `/duel play {duel_type} @[opponent] [your move]`")
    await ctx.send("Done!", hidden=True)
    await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(base="duel", name="deny", description="Deny someone's challenge", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="user", description="The person who challenged you", required=True, option_type=option_type.USER)
  ])
  @utils.check_message_to_be_processed
  async def duel_deny_cmd(self, ctx, user):
    """
    Callback for the duel deny command
    --
    input:
      ctx: discord.ext.commands.Context
      user: discord.User -> the person challenged
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id:
        duel_index = i
        break
    
    # Check the duel exists
    assert duel_index is not None, "This person did not challenge you to a duel"
    assert not db["duels"][duel_index]["accepted"], "You already accepted this challenge"

    # Give back the money to the challenger
    piflouz_handlers.update_piflouz(user.id, qty=db["duels"][duel_index]["amount"], check_cooldown=False)

    del db["duels"][duel_index]
    await ctx.channel.send(f"{ctx.author.mention} denied {user.mention}'s challenge!")
    await ctx.send("Done", hidden=True)
    await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(base="duel", name="cancel", description="Cancel your challenge to someone", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="user", description="The person you challenged", required=True, option_type=option_type.USER)
  ])
  @utils.check_message_to_be_processed
  async def duel_cancel_cmd(self, ctx, user):
    """
    Callback for the duel cancel command
    --
    input:
      ctx: discord.ext.commands.Context
      user: discord.User -> the person challenged
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["user_id1"] == ctx.author_id and duel["user_id2"] == user.id:
        duel_index = i
        break
    
    # Check the duel exists
    assert duel_index is not None, "You did not challenge this person to a duel"
    assert not db["duels"][duel_index]["accepted"], "This person already accepted the duel"

    # Give back the money to the challenger
    piflouz_handlers.update_piflouz(ctx.author_id, qty=db["duels"][duel_index]["amount"], check_cooldown=False)

    del db["duels"][duel_index]

    await ctx.channel.send(f"{ctx.author.mention} cancelled his/her challenge to {user.mention}, what a loser")
    await ctx.send("Done!", hidden=True)
    await utils.update_piflouz_message(self.bot)


  @cog_ext.cog_subcommand(name="shifumi", base="duel", subcommand_group="play", description="Play shifumi!", guild_ids=Constants.GUILD_IDS, options=[
    create_option(name="user", description="Who do you play against?", required=True, option_type=option_type.USER),
    create_option(name="value", description="What do you want to play?", required=True, option_type=option_type.STRING, choices=[
        create_choice("Rock", "Rock"),
        create_choice("Paper", "Paper"),
        create_choice("Scissors", "Scissors")
      ]
    )
  ])
  @utils.check_message_to_be_processed
  async def duel_play_shifumi_cmd(self, ctx, user, value):
    """
    Callback for the duel accept command
    --
    input:
      ctx: discord.ext.commands.Context
      user: discord.User
      value: string -> the move played by the player
    """
    await ctx.defer(hidden=True)
    duel_index = None
    for i, duel in enumerate(db["duels"]):
      if duel["user_id1"] == ctx.author_id and duel["user_id2"] == user.id or duel["user_id2"] == ctx.author_id and duel["user_id1"] == user.id:
        duel_index = i
        break
    
    # Check the duel exists
    assert duel_index is not None, "There is no challenge between you two"
    assert db["duels"][duel_index]["accepted"], "This duel is not accepted yet"

    if db["duels"][duel_index]["user_id1"] == ctx.author_id:
      assert db["duels"][duel_index]["move1"] is None, "You already played!"
      db["duels"][duel_index]["move1"] = value
      player1 = ctx.author
      player2 = user
    else:
      assert db["duels"][duel_index]["move2"] is None, "You already played!"
      db["duels"][duel_index]["move2"] = value
      player1 = user
      player2 = ctx.author
    
    # Bot players played
    move1 = db["duels"][duel_index]["move1"]
    move2 = db["duels"][duel_index]["move2"]

    await ctx.send("Done! Just wait for the other player to make a move", hidden=True)

    total_money = 2 * db["duels"][duel_index]["amount"]
    money_tax = ceil(total_money * Constants.DUEL_TAX_RATIO / 100)
    money_if_win = total_money - money_tax

    win_shifumi = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
    if move1 is not None and move2 is not None:
      # Tie, everyone gets all of their money back
      if move1 == move2:
        piflouz_handlers.update_piflouz(player1.id, qty=db["duels"][duel_index]["amount"], check_cooldown=False)
        piflouz_handlers.update_piflouz(player2.id, qty=db["duels"][duel_index]["amount"], check_cooldown=False)

        await ctx.channel.send(f"{player1.mention} and {player2.mention} tied at {db['duels'][duel_index]['duel_type']}! They both played {move1}! They both got their money back")

      # Player 1 won
      elif win_shifumi[move1] == move2:
        piflouz_handlers.update_piflouz(player1.id, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.user.id, qty=money_tax, check_cooldown=False)

        await ctx.channel.send(f"{player1.mention} won at {db['duels'][duel_index]['duel_type']} against {player2.mention}, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move1} vs {move2}")
      
      # Player 2 won
      else:
        piflouz_handlers.update_piflouz(player2.id, qty=money_if_win, check_cooldown=False)
        piflouz_handlers.update_piflouz(self.bot.user.id, qty=money_tax, check_cooldown=False)

        await ctx.channel.send(f"{player2.mention} won at {db['duels'][duel_index]['duel_type']} against {player1.mention}, earning {money_if_win} {Constants.PIFLOUZ_EMOJI}! They played {move2} vs {move1}")

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

    my_duels = filter(lambda duel: ctx.author_id in [duel["user_id1"], duel["user_id2"]], db["duels"])

    msgs = []
    for duel in my_duels:
      s = f"<@{duel['user_id1']}> vs <@{duel['user_id2']}> - {duel['duel_type']} - {duel['amount']} {Constants.PIFLOUZ_EMOJI}\n"
      
      if not duel["accepted"]:
        s += f"Waiting on <@{duel['user_id2']}> to accept\n"
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