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

    old_message = await bot.get_channel(db["out_channel"]).fetch_message(db["current_event_message_id"])
    await old_message.unpin()

  # Chose the new event of the day
  new_event = random.choice(Constants.RANDOM_EVENTS)
  message = await new_event.on_begin(bot)
  await message.pin()
  db["current_event_message_id"] = message.id
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
    --
    output:
      msg: int -> id of the message announcing the event
    """
    return None
  
  
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
    return message
  

  async def on_end(self, bot):
    if "out_channel" not in db.keys():
      return

    out_channel = bot.get_channel(db["out_channel"])
    participation = db["raffle_participation"]

    # Computing the winner for the last raffle
    if len(participation) > 0:
      
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
      piflouz_handlers.update_piflouz(bot.user.id, qty=tax_value, check_cooldown=False)

      message = f"Congratulations to <@{id}> for winning the raffle, earning {prize} {Constants.PIFLOUZ_EMOJI}!"

      piflouz_handlers.update_piflouz(id, prize, check_cooldown=False)
      await out_channel.send(message)
      
      await utils.update_piflouz_message(bot)
      bot.dispatch("raffle_won", id)


  def to_str(self):
    return f"{__name__}.{type(self).__name__}({self.ticket_price}, {self.tax_ratio})"
  

  async def update_raffle_message(self, bot):
    """
    Updates the piflouz message with the rankings
    --
    input:
      bot: discord.ext.commands.Bot
    """
    if "current_event_message_id" not in db.keys():
      return

    channel = bot.get_channel(db["out_channel"])
    embed = await self.get_embed_raffle(bot)
    raffle_message = await channel.fetch_message(db["current_event_message_id"])
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
      title="New Raffle!",
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


class Event_from_powerups(Event):
  """
  Creates an event with just a list of powerups
  """
  def __init__(self, *powerup_list):
    self.powerups = list(powerup_list)
  
  async def on_begin(self, bot):
    if "out_channel" not in db.keys():
      return

    out_channel = bot.get_channel(db["out_channel"])

    # Starting new event
    embed = self.get_embed()
    message = await out_channel.send(embed=embed)
    await message.pin()
    return message
  

  async def on_end(self, bot):
    pass
  

  def get_powerups(self):
    return self.powerups
  

  def get_embed(self):
    """
    Returns an embed to announce the event
    --
    output:
      embed: discord.Embed
    """
    embed = discord.Embed(
      title="Event of the day",
      colour=discord.Colour.random()
    )
    descriptions = [p.get_info_str() for p in self.powerups]
    content = "\n".join(descriptions)
    embed.add_field(
      name="The following powerups are active:",
      value=content
    )
    embed.set_thumbnail(url=Constants.PIBOU4STONKS_URL)
    return embed
  

  def to_str(self):
    powerups_str = ", ".join([p.to_str() for p in self.powerups])
    return f"{__name__}.{Event_from_powerups.__name__}({powerups_str})"


class Increased_pibox_drop_rate_event(Event_from_powerups):
  def __init__(self, value):
    p = powerups.Pibox_drop_rate_multiplier(value)
    super().__init__(p)


class Increased_piflouz_event(Event_from_powerups):
  def __init__(self, value):
    p = powerups.Piflouz_multiplier(None, value, None)
    super().__init__(p)


class Cooldown_reduction_event(Event_from_powerups):
  def __init__(self, value):
    p = powerups.Cooldown_reduction(None, value, None)
    super().__init__(p)