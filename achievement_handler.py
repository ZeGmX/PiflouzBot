
listeners = dict()


def listen_to(*events):
  """
  Decorator to register the events that a class listens to
  --
  input:
    *events: strings -> the name of the events
  """
  def wrapper(cls):
    for e in events:
      if e not in listeners.keys():
        listeners[e] = []
      listeners[e].append(cls)
    return cls
  return wrapper


async def dispatch_to_achievements(event, user_id, *args, **kwargs):
  """
  Sends informations to the appropriate achievements to validate it(or not)
  --
  input:
    event: str -> the name of the event
  """
  if event in listeners.keys():
    for cls in listeners[event]:
      event_obj = cls()
      try:
        assert not event_obj.is_validated(user_id), "achievement already validated"
        await event_obj.check(user_id, *args, **kwargs)
      except:
        pass


async def on_slash_function_listener(ctx):
  """
  Listener that is called when a slash command interaction is created
  --
  input:
    ctx: discord_slash.context.SlashContext
  """
  await dispatch_to_achievements(ctx.name, ctx.author_id,ctx)


async def on_component_listener(ctx):
  """
  Listener that is called when a component interaction is created
  --
  input:
    ctx: discord_slash.context.ComponentContext
  """
  await dispatch_to_achievements(ctx.custom_id, ctx.author_id, ctx)


def add_custom_listener_for_achievements(bot, event_name):
  """
  Adds a new listener to the bot which is used to check achicvement progress
  --
  input:
    bot: discord.ext.commands.Bot
    event_name: str
  """
  async def custom_event_listener(user_id, *args, **kwargs):
    await dispatch_to_achievements(event_name, user_id, *args, **kwargs)
  
  bot.add_listener(custom_event_listener, name="on_" + event_name)


def get_achievements_list():
  """
  Returns the list of all current achievements
  --
  output:
    res: Achievement list
  """
  return [cls() for l in listeners.values() for cls in l]