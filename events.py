from discord.ext import tasks
import random
from replit import db
import discord
import asyncio
from math import floor

from constant import Constants
import piflouz_handlers
import powerups
import utils


@tasks.loop(hours=24)
async def event_handlers(bot):
  await utils.wait_until(Constants.EVENT_TIME)
  
  # End the current event
  if "current_event" in db.keys():
    current_event = eval(db["current_event"][len(__name__) + 1:])
    await current_event.on_end(bot)

  # Chose the new event of the day
  new_event = random.choice(Constants.RANDOM_EVENTS)
  await new_event.on_begin(bot)
  db["current_event"] = new_event.to_str()
  

class Event:
  """
  Base class for the events, inherited by every event class
  """

  async def on_begin(self, bot):
    """
    Actions to be done when the event starts
    --
    input:
      bot: discord.ext.commands.Bot
    """
    pass
  
  
  async def on_end(self, bot):
    """
    Actions to be done when the event ends
    --
    input:
      bot: discord.ext.commands.Bot
    """
    pass
  

  def get_powerups(self):
    """
    Returns the list of powerups active during the event
    --
    output:
      res: Powerup list
    """
    return []


  def to_str(self):
    """
    Returns a string used to store in the database, and get back the object with eval
    --
    output:
      res: str
    """
    return ""


class Raffle_event(Event):
  """
  Raffle event, people can buy tickets and the person with the winning ticket wins all the money (minus taxes)
  """
  def __init__(self, ticket_price, tax_ratio):
    self.ticket_price = ticket_price
    self.tax_ratio = tax_ratio


  async def on_begin(self, bot):
    if "out_channel" not in db.keys():
      return
    
    out_channel = bot.get_channel(db["out_channel"])

    # Starting new raffle
    embed = await self.get_embed_raffle(bot)
    message = await out_channel.send(embed=embed)
    db["last_raffle_message"] = message.id
    await message.pin()
  

  async def on_end(self, bot):
    if "out_channel" not in db.keys():
      return
    
    message_exists = False
    out_channel = bot.get_channel(db["out_channel"])

    if "last_raffle_message" in db.keys():
      message_exists = True
      message = await out_channel.fetch_message(db["last_raffle_message"])
      del db["last_raffle_message"]
      await message.unpin()

    participation = db["raffle_participation"]

    # Computing the winner for the last raffle
    if message_exists and len(participation) > 0:
      
      total_tickets = sum(participation.values())
      winning_index = random.randrange(0, total_tickets)
      
      partial_sum = 0
      for id, value in participation.items():
        if partial_sum <= winning_index < partial_sum + value:
          break
        partial_sum += value
      
      prize = self.get_raffle_total_prize()
      db["raffle_participation"] = dict()

      # Giving the tax to the bot
      tax_value = total_tickets * self.ticket_price - prize
      piflouz_handlers.update_piflouz(bot.user, qty=tax_value, check_cooldown=False)

      member = await bot.guilds[0].fetch_member(id)
      message = f"Congratulations to {member.mention} for winning the raffle, earning {prize} {Constants.PIFLOUZ_EMOJI}!"

      piflouz_handlers.update_piflouz(member, prize, check_cooldown=False)
      await out_channel.send(message)
      
      await utils.update_piflouz_message(bot)


  def to_str(self):
    return f"{__name__}.{type(self).__name__}({self.ticket_price}, {self.tax_ratio})"
  

  async def update_raffle_message(self, bot):
    """
    Updates the piflouz message with the rankings
    --
    input:
      bot: discord.ext.commands.Bot
    """
    if "last_raffle_message" not in db.keys():
      return

    channel = bot.get_channel(db["out_channel"])
    embed = await self.get_embed_raffle(bot)
    raffle_message = await channel.fetch_message(db["last_raffle_message"])
    await raffle_message.edit(embed=embed)


  async def get_embed_raffle(self, bot):
    """
    Returns an embed message corresponding to the raffle message
    --
    input:
      bot: discord.ext.commands.Bot
    """
    desc = f"Here is the new raffle! Use `/raffle n` to buy `n` tickets!\n\
    They cost {self.ticket_price} {Constants.PIFLOUZ_EMOJI} each\n\
    The user with the winning ticket will earn {100 - self.tax_ratio}% of the total money spent by everyone!"

    embed = discord.Embed(
      title="New raffle!",
      description=desc,
      colour=discord.Colour.random()
    )

    embed.set_thumbnail(url=Constants.PIBOU4STONKS_URL)

    if "raffle_participation" in db.keys() and len(db["raffle_participation"]) > 0:
      participation = db["raffle_participation"]

      async def get_str(key_val):
        user_id, nb_tickets = key_val
        return f"<@{user_id}> - {nb_tickets}\n"

      tasks = [get_str(key_val) for key_val in participation.items()]
      res = await asyncio.gather(*tasks)
      val = "".join(res)
      
      total_prize = self.get_raffle_total_prize()

      embed.add_field(  
        name="Current tickets bought",
        value=val,
        inline=False
      )
      embed.add_field(
        name="Total prize",
        value=f"The winner will earn {total_prize} {Constants.PIFLOUZ_EMOJI}!",
        inline=False
      )
    
    return embed
  

  def get_raffle_total_prize(self):
    """
    Returns the total prize in the current raffle
    Returns 0 if there is no current raffle
    --
    output:
      prize: int
    """
    nb_tickets = sum(db["raffle_participation"].values())
    prize = floor(nb_tickets * self.ticket_price * (100 - self.tax_ratio) / 100)
    return prize


class Increased_pibox_drop_rate_event(Event):
  """
  Event with a powerup that increases the pibox drop rate
  """
  def __init__(self, value):
    self.value = value

  async def on_begin(self, bot):
    if "out_channel" not in db.keys():
      return

    out_channel = bot.get_channel(db["out_channel"])

    # Starting new event
    embed = self.get_embed()
    message = await out_channel.send(embed=embed)
    await message.pin()


  async def on_end(self, bot):
    pass
  

  def get_powerups(self):
    return [powerups.Pibox_drop_rate_multiplier(self.value)]
  

  def get_embed(self):
    """
    Returns an embed to announce the event
    --
    output:
      embed: discord.Embed
    """
    embed = discord.Embed(
      title="Increased pibox rate!",
      description=f"Pibox drop rate increased by {self.value}%",
      colour=discord.Colour.random()
    )
    embed.set_thumbnail(url=Constants.PIBOU4STONKS_URL)
    return embed
  
  def to_str(self):
    return f"{__name__}.{type(self).__name__}({self.value})"