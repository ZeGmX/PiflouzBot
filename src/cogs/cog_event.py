from interactions import Extension, OptionType, Embed, EmbedAttachment, MaterialColors, RoleColors, slash_option, auto_defer, slash_command, component_callback
from my_database import db
import os

from constant import Constants
from embed_messages import get_embed_wordle
import events.events  # used in eval()
from events.matches_challenge import Matches_Expression
from events.subsequence_challenge import Subseq_challenge
from wordle import Wordle
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
    /birthday
    /match guess
    /subseq guess
  Components
    events.Birthday_raffle_event.BUTTON_ID
  """

  def __init__(self, bot):
    self.bot = bot

    # Register the button callbacks
    for emoji in events.events.Birthday_event.INGREDIENTS:
      self.bot.add_component_callback(self.callback_from_emoji(emoji))

    
  @slash_command(name="raffle", description="Buy raffle 🎟️ to test your luck ⚠️ Costs piflouz", scopes=Constants.GUILD_IDS)
  @slash_option(name="nb_tickets", description="How many tickets?", opt_type=OptionType.INTEGER, required=True, min_value=1)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def raffle_cmd(self, ctx, nb_tickets):
    """
    Callback for the /raffle command
    --
    input:
      ctx: interactions.SlashContext
      nb_tickets: int
    """
    await utils.custom_assert("current_event_passive" in db.keys(), "No current event registered", ctx)
  
    current_raffle = eval(db["current_event_passive"])
    await utils.custom_assert(isinstance(current_raffle, events.events.Raffle_event), "The current event is not a raffle", ctx)
  
    price = nb_tickets * current_raffle.ticket_price
    
    user_id = str(ctx.author.id)
  
    # user doesn't have enough money
    await utils.custom_assert(piflouz_handlers.update_piflouz(user_id, qty=-price, check_cooldown=False), f"You don't have enough money to buy {nb_tickets} tickets", ctx)
    
    if not user_id in db["raffle_participation"].keys():
      db["raffle_participation"][user_id] = 0
    db["raffle_participation"][user_id] += nb_tickets
  
    await ctx.send(f"Successfully bought {nb_tickets} tickets", ephemeral=True)
    await current_raffle.update_raffle_message(self.bot)
    await utils.update_piflouz_message(self.bot)
    self.bot.dispatch("raffle_participation_successful", ctx.author.id, nb_tickets)


  @slash_command(name="wordle", description="TBD", sub_cmd_name="guess", sub_cmd_description="Take a guess on the word the day")
  @slash_option(name="word", description="5-letter english word", opt_type=OptionType.STRING, required=True, min_length=Wordle.WORD_SIZE, max_length=Wordle.WORD_SIZE)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def wordle_guess_cmd(self, ctx, word):
    """
    Callback for the /wordle guess command
    --
    input:
      ctx: interactions.SlashContext
      word: str
    """
    await utils.custom_assert("current_event_challenge" in db.keys(), "No current event registered", ctx)
  
    current_wordle = eval(db["current_event_challenge"])
    await utils.custom_assert(isinstance(current_wordle, events.events.Wordle_event), "The current event is not a wordle", ctx)

    wordle = Wordle(db["word_of_the_day"])

    user_id = str(int(ctx.author.id))
    if user_id not in db["wordle_guesses"].keys():
      db["wordle_guesses"][user_id] = []

    guesses = list(db["wordle_guesses"][user_id])
    word = word.lower()
    await utils.custom_assert(len(guesses) < wordle.NB_TRIALS, "The maximum amount of trials has been reached!", ctx)
    await utils.custom_assert(wordle.is_valid(word), "This is not a valid word!", ctx)
    await utils.custom_assert(guesses == [] or wordle.solution != guesses[-1], "You already won!", ctx)

    guesses.append(word)
    db["wordle_guesses"][user_id] = guesses
    
    header_str = "\n".join(wordle.guess(w) for w in guesses)

    if guesses[-1] == wordle.solution:
      progress = 1 + (1 - len(guesses)) / (wordle.NB_TRIALS - 1)
      reward = round(current_wordle.min_reward + progress * (current_wordle.max_reward - current_wordle.min_reward))
      
      header_str += f"\n\nCongratulations, you found the word of the day with {len(guesses)}/{wordle.NB_TRIALS} trials!\nYou earned {reward}{Constants.PIFLOUZ_EMOJI}"
      piflouz_handlers.update_piflouz(user_id, reward, check_cooldown=False)

      results = "\n".join([wordle.guess(word) for word in guesses])
      announcement_msg = f"{ctx.author.mention} solved today's Wordle ({len(guesses)}/{wordle.NB_TRIALS})!\n{results}"
      thread = await ctx.bot.fetch_channel(db["current_event_challenge_thread_id"])
      await thread.send(announcement_msg)

      db["piflouz_generated"]["event"] += reward
      await utils.update_piflouz_message(self.bot)

    elif len(guesses) == wordle.NB_TRIALS:
      header_str += f"\n\nOuch, you failed :(\nThe answer was: **{wordle.solution}**"

    await self.send_wordle_embed(ctx, wordle, guesses, header_str)  


  @slash_command(name="wordle", description="TBD", sub_cmd_name="status", sub_cmd_description="Check how your wordle is going")
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def wordle_status_cmd(self, ctx):
    """
    Callback for the /wordle status command
    --
    input:
      ctx: interactions.SlashContext
    """
    await utils.custom_assert("current_event_challenge" in db.keys(), "No current event registered", ctx)
    
    current_wordle = eval(db["current_event_challenge"])
    await utils.custom_assert(isinstance(current_wordle, events.events.Wordle_event), "The current event is not a wordle", ctx)
    
    wordle = Wordle(db["word_of_the_day"])

    user_id = str(int(ctx.author.id))
    await utils.custom_assert(user_id in db["wordle_guesses"].keys(), "You haven't participated to today's wordle yet!", ctx)

    guesses = list(db["wordle_guesses"][user_id])

    await utils.custom_assert(len(guesses) > 0, "You haven't participated to today's wordle yet!", ctx)
    
    header_str = "\n".join(wordle.guess(w) for w in guesses)
    header_str += f"\n{len(guesses)}/{wordle.NB_TRIALS}"

    if guesses != [] and guesses[-1] == wordle.solution:
      header_str += "\nYou won!"
    elif len(guesses) == wordle.NB_TRIALS:
      header_str += f"\nYou lost :( The correct word was {wordle.solution}"

    await self.send_wordle_embed(ctx, wordle, guesses, header_str)


  async def send_wordle_embed(self, ctx, wordle, guesses, header_str):
    """
    Generates the wordle image, host it on imgur and send it as an interaction response
    --
    input:
      ctx: interactions.SlashContext
      wordle: wordle.Wordle
      guesses: List[str]
      header_str: str
    """
    embed = await get_embed_wordle(wordle.solution, guesses, header_str)
    await ctx.send(embed=embed, ephemeral=True)


  async def birthday_ingredient_button_callback(self, ctx, emoji):
    """
    callback for the birthday event buttons with the given emoji
    --
    input:
      ctx: interactions.SlashContext
      emoji: str
    """
    user_id = str(ctx.author.id)

    if user_id not in db["birthday_event_ingredients"].keys():
      db["birthday_event_ingredients"][user_id] = {e: 0 for e in events.events.Birthday_event.INGREDIENTS}
      db["birthday_event_ingredients"][user_id]["last_react_time"] = -1
    if user_id not in db["baked_cakes"].keys():
      db["baked_cakes"][user_id] = 0

    date = int(ctx.message.timestamp.timestamp())
    await utils.custom_assert(db["birthday_event_ingredients"][user_id]["last_react_time"] != date, "You already took one ingredient from this delivery!", ctx)

    qty = db["last_birthday_delivery"]["qty"][emoji]
    db["birthday_event_ingredients"][user_id]["last_react_time"] = date
    db["birthday_event_ingredients"][user_id][emoji] += qty

    event = eval(db["current_event_passive"])
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
      interactions.ComponentCommand
    """
    @component_callback(emoji)
    @auto_defer(ephemeral=True)
    async def callback(ctx):
      await self.birthday_ingredient_button_callback(ctx, emoji)
    return callback


  @slash_command(name="birthday", description=f"Check how your baking skills are going", scopes=Constants.GUILD_IDS, options=[])
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def birthday_cmd(self, ctx):
    """
    Callback for the /birthday command
    --
    input:
      ctx: interactions.SlashContext
    """
    await utils.custom_assert("current_event_passive" in db.keys(), "No current event registered", ctx)
  
    current_bday = eval(db["current_event_passive"])
    await utils.custom_assert(isinstance(current_bday, events.events.Birthday_event), "The current event is not a Birthay event", ctx)

    user_id = str(ctx.author.id)
    if user_id not in db["birthday_event_ingredients"].keys():
      db["birthday_event_ingredients"][user_id] = {e: 0 for e in events.events.Birthday_event.INGREDIENTS}
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
    for e in events.events.Birthday_event.INGREDIENTS:
      res += f"• {e}: {db['birthday_event_ingredients'][user_id][e]}\n"
    res += f"\nYou baked {db['baked_cakes'][user_id]} cakes!"
    return res


  @component_callback(events.events.Birthday_raffle_event.BUTTON_ID)
  @auto_defer(ephemeral=True)
  async def birthday_raffle_register(self, ctx):
    """
    Callback for the button to register to the birthday raffle
    --
    input:
      ctx: interactions.ComponentContext
    """
    await utils.custom_assert("current_event_passive" in db.keys(), "No current event registered", ctx)
    
    current_bday_raffle = eval(db["current_event_passive"])
    await utils.custom_assert(isinstance(current_bday_raffle, events.events.Birthday_raffle_event), "The current event is not a brithday raffle", ctx)

    user_id = str(ctx.author.id)
    await utils.custom_assert(user_id not in db["birthday_raffle_participation"], "You are already registered!", ctx)
    db["birthday_raffle_participation"].append(user_id)

    await current_bday_raffle.update_raffle_message(self.bot)
    
    await ctx.send("You are now registered!", ephemeral=True)
  

  @slash_command(name="match", description="TBD", sub_cmd_name="guess", sub_cmd_description="Take a guess on the match event of the day", scopes=Constants.GUILD_IDS)
  @slash_option(name="guess", description="Your guessed equation", opt_type=OptionType.STRING, required=True)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def match_guess_cmd(self, ctx, guess):
    """
    Callback for the /match guess command
    --
    input:
      ctx: interactions.SlashContext
      guess: str
    """
    await utils.custom_assert("current_event_challenge" in db.keys(), "No current challenge event registered", ctx)
    
    current_match = eval(db["current_event_challenge"])
    await utils.custom_assert(isinstance(current_match, events.events.Move_match_event), "The current event is not a match moving event", ctx)

    user_id = str(ctx.author.id)
    await utils.custom_assert(user_id not in db["match_challenge_completed"], "You already won the event!", ctx)

    expression = Matches_Expression(s=guess)
    await utils.custom_assert(expression.is_valid(), "This is not a valid equation!", ctx)
    await utils.custom_assert(expression.is_correct(), "This equation is incorrect!", ctx)
    await utils.custom_assert(expression.str in db["match_challenge"]["all_sols"], "This equation is not one of my solution, try again!", ctx)

    db["match_challenge_completed"].append(user_id)
    piflouz_handlers.update_piflouz(user_id, current_match.reward, check_cooldown=False)
    await ctx.send(f"Congratulations, this is correct! You earned {current_match.reward} {Constants.PIFLOUZ_EMOJI}", ephemeral=True)
    
    thread = await ctx.bot.fetch_channel(db["current_event_challenge_thread_id"])
    await thread.send(f"{ctx.author.mention} solved today's match event!")

    db["piflouz_generated"]["event"] += current_match.reward
    await utils.update_piflouz_message(self.bot)
  

  @slash_command(name="subseq", description="TBD", sub_cmd_name="guess", sub_cmd_description="Take a guess on the subsequence event of the day", scopes=Constants.GUILD_IDS)
  @slash_option(name="guess", description="Your guessed word", opt_type=OptionType.STRING, required=True)
  @auto_defer(ephemeral=True)
  @utils.check_message_to_be_processed
  async def subseq_guess_cmd(self, ctx, guess):
    """
    Callback for the `/subseq guess` command
    --
    input:
      ctx: interactions.SlashContext
      guess: str
    """
    await utils.custom_assert("current_event_challenge" in db.keys(), "No current challenge event registered", ctx)
    
    current_match = eval(db["current_event_challenge"])
    await utils.custom_assert(isinstance(current_match, events.events.Subseq_challenge_event), "The current event is not a subsequence event", ctx)

    user_id = str(ctx.author.id)
    await utils.custom_assert(user_id not in db["subseq_challenge_completed"], "You already won the event!", ctx)

    s = Subseq_challenge(subseq=db["subseq_challenge"]["subseq"], sol=db["subseq_challenge"]["sol"])
    await utils.custom_assert(s.check(guess), "Incorrect!", ctx)

    db["subseq_challenge_completed"].append(user_id)
    piflouz_handlers.update_piflouz(user_id, current_match.reward, check_cooldown=False)
    await ctx.send(f"Congratulations, this is correct! You earned {current_match.reward} {Constants.PIFLOUZ_EMOJI}", ephemeral=True)

    thread = await ctx.bot.fetch_channel(db["current_event_challenge_thread_id"])
    await thread.send(f"{ctx.author.mention} solved today's subsequence event!")

    db["piflouz_generated"]["event"] += current_match.reward
    await utils.update_piflouz_message(self.bot)


def setup(bot):
  Cog_event(bot)