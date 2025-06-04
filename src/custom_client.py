from interactions import Client
from interactions.api.events import BaseEvent


class Client(Client):
    """
    A custom bot client to simplify some function calls
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dispatch(self, event, *args, **kwargs):
        """
        Dispatches an event with the arguments
        The first argument should be a string corresponding to the event name
        """
        if isinstance(event, BaseEvent):
            super().dispatch(event, *args, **kwargs)
        else:
            super().dispatch(MyEvent(event, self), *args, **kwargs)

    async def set_profile_picture(self, path):
        """
        Sets the profile picture of the bot

        Parameters
        ----------
        path (str): The path to the image file
        """
        await self.user.edit(avatar=path)


class MyEvent(BaseEvent):
    """
    A custom event
    """

    def __init__(self, name, bot):
        self.override_name = name
        self.bot = bot
