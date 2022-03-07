from interactions import InteractionType


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


async def on_interaction_create_listener(ctx):
  """
  Listener that is called when an interaction is created
  --
  input:
    ctx: interactions.MessageContext
  """
  if ctx.type == InteractionType.APPLICATION_COMMAND:
    await dispatch_to_achievements(ctx.data.name, int(ctx.author.id), ctx)
  elif ctx.type == InteractionType.MESSAGE_COMPONENT:
    await dispatch_to_achievements(ctx.custom_id, int(ctx.author.id), ctx)


def add_custom_listener_for_achievements(bot, event_name):
  """
  Adds a new listener to the bot which is used to check achievement progress
  --
  input:
    bot: interactions.Client
    event_name: str
  """
  async def custom_event_listener(user_id, *args, **kwargs):
    await dispatch_to_achievements(event_name, user_id, *args, **kwargs)

  bot.register_listener(custom_event_listener, name=event_name)


def get_achievements_list():
  """
  Returns the list of all current achievements
  --
  output:
    res: Achievement list
  """
  return [cls() for l in listeners.values() for cls in l]