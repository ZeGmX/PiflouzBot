from interactions import extension_command, Extension, Option, OptionType
from replit import db

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

    img_path = "wordle_tmp.png"
    guesses.append(word)
    db["wordle_guesses"][user_id] = guesses
    wordle.generate_image(guesses, img_path)
    link = utils.upload_image_to_imgur(img_path)
    res = link + "\n" + "\n".join(wordle.guess(w) for w in guesses)

    if guesses[-1] == wordle.solution:
      res += f"\n\nCongratulations, you found the word of the day with {len(guesses)}/{wordle.nb_trials} trials!\nYou earnt {current_event.reward}{Constants.PIFLOUZ_EMOJI}"
      piflouz_handlers.update_piflouz(user_id, current_event.reward, check_cooldown=False)
    elif len(guesses) == wordle.nb_trials:
      res += f"\n\nOuch, you failed :(\nThe answer was: **{wordle.solution}**"

    await ctx.send(res, ephemeral=True)      


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
    img_path = "wordle_tmp.png"
    wordle.generate_image(guesses, img_path)
    res = "\n".join(wordle.guess(w) for w in guesses)
    res += f"\n{len(guesses)}/{wordle.nb_trials}"

    if guesses != [] and guesses[-1] == wordle.solution:
      res += "\nYou won!"
    elif len(guesses) == wordle.nb_trials:
      res += f"You lost :( The correct word was {wordle.solution}"

    await ctx.send(res, ephemeral=True)
    

def setup(bot):
  Cog_event(bot)