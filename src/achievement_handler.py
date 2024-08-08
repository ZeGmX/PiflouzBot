from interactions import Extension, listen


listeners = dict()  # Associates an event name to a list of classes that listen to it


class AchievementHandlerExt(Extension):
    """
    Intermediate for event dispatching and achievement checking
    """

    def __init__(self, bot):
        self.bot = bot

    @listen()
    async def on_component_completion(self, event):
        """
        Listener that is called when a component callback has finished

        Parameters
        ----------
        event (interactions.ComponentCompletion)
        """
        ctx = event.ctx
        await dispatch_to_achievements(ctx.custom_id, int(ctx.author.id), ctx)

    @listen()
    async def on_command_completion(self, event):
        """
        Listener that is called when a command callback has finished

        Parameters
        ----------
        event (interactions.CommandCompletion)
        """
        ctx = event.ctx
        await dispatch_to_achievements(ctx.command.name.default, int(ctx.author.id), ctx)

    @staticmethod
    def add_custom_listener_for_achievements(bot, event_name):
        """
        Adds a new listener to the bot
        When the event is dispached, it will be sent to the achievements listening to it to check if they are validated

        Parameters
        ----------
        bot (interactions.Client)
        event_name (str)
        """
        @listen(event_name)
        async def custom_event_listener(event, user_id, *args, **kwargs):
            await dispatch_to_achievements(event_name, user_id, *args, **kwargs)

        bot.add_listener(custom_event_listener)


def listen_to(*events):
    """
    Decorator to register the events that a class listens to

    Parameters
    ----------
    events (strings):
        the name of the events
    """
    def wrapper(cls):
        for e in events:
            if e not in listeners.keys():
                listeners[e] = []
            listeners[e].append(cls)
        return cls
    return wrapper


async def dispatch_to_achievements(event_name, user_id, *args, **kwargs):
    """
    Sends informations to the appropriate achievements to validate it(or not)

    Parameters
    ----------
    event_name (str):
        the name of the event
    user_id (int):
        id of the user who triggered the event
    """
    if event_name in listeners.keys():
        for cls in listeners[event_name]:
            event_obj = cls()
            try:
                assert not event_obj.is_validated(user_id), "achievement already validated"
                await event_obj.check(user_id, *args, **kwargs)
            except Exception:
                pass


def get_achievements_list():
    """
    Returns the list of all current achievements

    Returns
    -------
    res (Achievement list)
    """
    return [cls() for data in listeners.values() for cls in data]
