from interactions import Extension, listen


listeners = dict()  # Associates an event name to a list of classes that listen to it


class Achievement_handler_ext(Extension):
    """
    Intermediate for event dispatching and achievement checking
    """

    def __init__(self, bot) :
        self.bot = bot
    

    @listen()
    async def on_component_completion(self, event):
        """
        Listener that is called when a component callback has finished
        --
        input:
            event: interactions.ComponentCompletion
        """
        ctx = event.ctx
        await dispatch_to_achievements(ctx.custom_id, int(ctx.author.id), ctx)


    @listen()
    async def on_command_completion(self, event):
        """
        Listener that is called when a command callback has finished
        --
        input:
            event: interactions.CommandCompletion
        """
        ctx = event.ctx
        await dispatch_to_achievements(ctx.command.name.default, int(ctx.author.id), ctx)


    def add_custom_listener_for_achievements(bot, event_name):
        """
        Adds a new listener to the bot
        When the event is dispached, it will be sent to the achievements listening to it to check if they are validated
        --
        input:
            bot: interactions.Client
            event_name: str
        """
        @listen(event_name)
        async def custom_event_listener(event, user_id, *args, **kwargs):
            await dispatch_to_achievements(event_name, user_id, *args, **kwargs)

        bot.add_listener(custom_event_listener)


def setup(bot):
    Achievement_handler_ext(bot)


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


async def dispatch_to_achievements(event_name, user_id, *args, **kwargs):
    """
    Sends informations to the appropriate achievements to validate it(or not)
    --
    input:
        event_name: str -> the name of the event
        user_id: int -> id of the user who triggered the event
    """
    if event_name in listeners.keys():
        for cls in listeners[event_name]:
            event_obj = cls()
            try:
                assert not event_obj.is_validated(user_id), "achievement already validated"
                await event_obj.check(user_id, *args, **kwargs)
            except:
                pass


def get_achievements_list():
    """
    Returns the list of all current achievements
    --
    output:
        res: Achievement list
    """
    return [cls() for l in listeners.values() for cls in l]