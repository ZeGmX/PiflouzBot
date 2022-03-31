from interactions import extension_command, extension_component, Extension, Option, OptionType, Embed, EmbedImageStruct
from discord import Color
from replit import db
import os

from constant import Constants
import events
import piflouz_handlers
import powerups # used in eval()
import utils
from wordle import Wordle


class Cog_event(Extension):
  """
  Cog containing all the interactions related to events
  --
  fields:
    bot: interactions.Client
  --
  Slash commands:  
    /raffle
    /wordle guess
    /wordle status
  """

  def __init__(self, bot):
    self.bot = bot

    # Register the button callbacks
    for emoji in events.Birthday_event.ingredients:
      self.bot.component(emoji)(self.callback_from_emoji(emoji))


  @extension_command(name="raffle", description=f"Buy raffle 🎟️ to test your luck /!\ Costs piflouz", scope=Constants.GUILD_IDS, options=[
    Option(name="nb_tickets", description="How many tickets?", type=OptionType.INTEGER, required=True, min_value=1)
  ])
  @utils.check_message_to_be_processed
  async def raffle_cmd(self, ctx, nb_tickets):
    """
    Callback for the /raffle command
    --
    input:
      ctx: interactions.CommandContext
      nb_tickets: int
    """
    await ctx.defer(ephemeral=True)
    await utils.custom_assert("current_event" in db.keys(), "No current event registered", ctx)
  
    current_event = eval(db["current_event"])
    await utils.custom_assert(isinstance(current_event, events.Raffle_event), "The current event is not a raffle", ctx)
  
    price = nb_tickets * current_event.ticket_price
    
    user_id = str(ctx.author.id)
  
    # user doesn't have enough money
    await utils.custom_assert(piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False), f"User {ctx.author} doesn't have enough money to buy {nb_tickets} tickets", ctx)
    
    if not user_id in db["raffle_participation"].keys():
      db["raffle_participation"][user_id] = 0
    db["raffle_participation"][user_id] += nb_tickets
  
    await ctx.send(f"Successfully bought {nb_tickets} tickets", ephemeral=True)
    await current_event.update_raffle_message(self.bot)
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("raffle_participation_successful", ctx.author.id, nb_tickets)


  @extension_command(name="wordle", description="TBD", scope=Constants.GUILD_IDS, options=[
    Option(name="guess", description="Take a guess on the word the day", type=OptionType.SUB_COMMAND, options=[
      Option(name="word", description="5-letter english word", type=OptionType.STRING, required=True)
    ]),
    Option(name="status", description="Check how your wordle is going", type=OptionType.SUB_COMMAND, options=[])
  ])
  @utils.check_message_to_be_processed
  async def wordle_cmd_group_dispatch(self, ctx, sub_command="status", word=None): # If the subcommand does not have options, the sub_command parameter is not sent
    """
    Dispatches the interaction for a /wordle depending on the sub command
    --
    input:
      ctx: interactions.CommandContext
    """
    if sub_command == "guess":
      await self.wordle_guess_cmd(ctx, word)
    elif sub_command == "status":
      await self.wordle_status_cmd(ctx)


  async def wordle_guess_cmd(self, ctx, word):
    """
    Callback for the /wordle guess command
    --
    input:
      ctx: interactions.CommandContext
      word: str
    """
    await ctx.defer(ephemeral=True)
    await utils.custom_assert("current_event" in db.keys(), "No current event registered", ctx)
  
    current_event = eval(db["current_event"])
    await utils.custom_assert(isinstance(current_event, events.Wordle_event), "The current event is not a wordle", ctx)

    wordle = Wordle(db["word_of_the_day"])

    user_id = str(int(ctx.author.id))
    if user_id not in db["wordle_guesses"].keys():
      db["wordle_guesses"][user_id] = []

    guesses = list(db["wordle_guesses"][user_id])
    word = word.lower()
    await utils.custom_assert(len(guesses) < wordle.nb_trials, "The maximum amount of trials has been reached!", ctx)
    await utils.custom_assert(wordle.is_valid(word), "This is not a valid word!", ctx)
    await utils.custom_assert(guesses == [] or wordle.solution != guesses[-1], "You already won!", ctx)

    guesses.append(word)
    db["wordle_guesses"][user_id] = guesses
    
    header_str = "\n".join(wordle.guess(w) for w in guesses)

    if guesses[-1] == wordle.solution:
      header_str += f"\n\nCongratulations, you found the word of the day with {len(guesses)}/{wordle.nb_trials} trials!\nYou earnt {current_event.reward}{Constants.PIFLOUZ_EMOJI}"
      piflouz_handlers.update_piflouz(user_id, current_event.reward, check_cooldown=False)
    elif len(guesses) == wordle.nb_trials:
      header_str += f"\n\nOuch, you failed :(\nThe answer was: **{wordle.solution}**"

    await self.send_wordle_embed(ctx, wordle, guesses, header_str)  


  async def wordle_status_cmd(self, ctx):
    """
    Callback for the /wordle status command
    --
    input:
      ctx: interactions.CommandContext
    """
    await ctx.defer(ephemeral=True)
    await utils.custom_assert("current_event" in db.keys(), "No current event registered", ctx)
    
    current_event = eval(db["current_event"])
    await utils.custom_assert(isinstance(current_event, events.Wordle_event), "The current event is not a wordle", ctx)
    
    wordle = Wordle(db["word_of_the_day"])

    user_id = str(int(ctx.author.id))
    await utils.custom_assert(user_id in db["wordle_guesses"].keys(), "You haven't participated to today's wordle yet!", ctx)

    guesses = list(db["wordle_guesses"][user_id])

    await utils.custom_assert(len(guesses) > 0, "You haven't participated to today's wordle yet!", ctx)
    
    header_str = "\n".join(wordle.guess(w) for w in guesses)
    header_str += f"\n{len(guesses)}/{wordle.nb_trials}"

    if guesses != [] and guesses[-1] == wordle.solution:
      header_str += "\nYou won!"
    elif len(guesses) == wordle.nb_trials:
      header_str += f"You lost :( The correct word was {wordle.solution}"

    await self.send_wordle_embed(ctx, wordle, guesses, header_str)


  async def send_wordle_embed(self, ctx, wordle, guesses, header_str):
    """
    Generates the wordle image, host it on imgur and send the it as an interaction response
    --
    input:
      ctx: interactions.CommandContext
      wordle: wordle.Wordle
      guesses: List[str]
      header_str: str
    """
    img_path = "wordle_tmp.png"
    wordle.generate_image(guesses, img_path)
    link = utils.upload_image_to_imgur(img_path)
    os.remove(img_path)

    color = Color.gold()
    if len(guesses) > 0 and guesses[-1] == wordle.solution:
      color = Color.dark_green()
    elif len(guesses) == wordle.nb_trials and guesses[-1] != wordle.solution:
      color = Color.dark_red()

    embed = Embed(
      title="Wordle",
      description=header_str,
      color = color.value,
      image=EmbedImageStruct(url=link)._json
    )
    await ctx.send(embeds=embed, ephemeral=True)


  async def birthday_ingredient_button_callback(self, ctx, emoji):
    """
    callback for the birthday event buttons with the given emoji
    --
    input:
      ctx: interactions.CommandContext
      emoji: str
    """
    await ctx.defer(ephemeral=True)
    user_id = str(ctx.author.id)

    if user_id not in db["birthday_event_ingredients"].keys():
      db["birthday_event_ingredients"][user_id] = {e: 0 for e in events.Birthday_event.ingredients}
      db["birthday_event_ingredients"][user_id]["last_react_time"] = -1
    if user_id not in db["baked_cakes"].keys():
      db["baked_cakes"][user_id] = 0

    date = int(ctx.message.timestamp.timestamp())
    await utils.custom_assert(db["birthday_event_ingredients"][user_id]["last_react_time"] != date, "You already took one ingredient from this delivery!", ctx)

    qty = db["last_birthday_delivery"]["qty"][emoji]
    db["birthday_event_ingredients"][user_id]["last_react_time"] = date
    db["birthday_event_ingredients"][user_id][emoji] += qty

    event = eval(db["current_event"])
    event.bake_cakes(user_id)

    res = self.get_birthday_str(user_id)    
    await ctx.send(res, ephemeral=True)
    await event.update_birthday_message(self.bot)

    
  def callback_from_emoji(self, emoji):
    """
    Returns the callback function for the birthday event buttons with the given emoji
    --
    input:
      emoji: str
    --
    output:
      callback function
    """
    async def callback(ctx):
      await self.birthday_ingredient_button_callback(ctx, emoji)
    return callback


  @extension_command(name="birthday", description=f"Check how your baking skills are going", scope=Constants.GUILD_IDS, options=[])
  @utils.check_message_to_be_processed
  async def birthday_cmd(self, ctx):
    """
    Callback for the /birthday command
    --
    input:
      ctx: interactions.CommandContext
    """
    await ctx.defer(ephemeral=True)
    await utils.custom_assert("current_event" in db.keys(), "No current event registered", ctx)
  
    current_event = eval(db["current_event"])
    await utils.custom_assert(isinstance(current_event, events.Birthday_event), "The current event is not a Birthay event", ctx)

    user_id = str(ctx.author.id)
    if user_id not in db["birthday_event_ingredients"].keys():
      db["birthday_event_ingredients"][user_id] = {e: 0 for e in events.Birthday_event.ingredients}
      db["birthday_event_ingredients"][user_id]["last_react_time"] = -1
    if user_id not in db["baked_cakes"].keys():
      db["baked_cakes"][user_id] = 0

    res = self.get_birthday_str(user_id)
    await ctx.send(res, ephemeral=True)


  def get_birthday_str(self, user_id):
    """
    Returns a string detailing the inventory of a user
    --
    input:
      user_id: str (of an int)
    --
    output:
      res: str
    """
    res = "Your ingredients: \n"
    for e in events.Birthday_event.ingredients:
      res += f"• {e}: {db['birthday_event_ingredients'][user_id][e]}\n"
    res += f"\nYou baked {db['baked_cakes'][user_id]} cakes!"
    return res


  @extension_component(events.Birthday_raffle_event.button_id)
  async def birthday_raffle_register(self, ctx):
    """
    Callback for the button to register to the birthday raffle
    """
    await ctx.defer(ephemeral=True)
    await utils.custom_assert("current_event" in db.keys(), "No current event registered", ctx)
    
    current_event = eval(db["current_event"])
    await utils.custom_assert(isinstance(current_event, events.Birthday_raffle_event), "The current event is not a wordle", ctx)

    user_id = str(ctx.author.id)
    await utils.custom_assert(user_id not in db["birthday_raffle_participation"], "You are already registered!", ctx)
    db["birthday_raffle_participation"] += [user_id]

    await current_event.update_raffle_message(self.bot)
    
    await ctx.send("You are now registered!", ephemeral=True)
  

def setup(bot):
  Cog_event(bot)