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
      super().dispatch(My_Event(event, self), *args, **kwargs)
  

class My_Event(BaseEvent):
  """
  A custom event
  """
  def __init__(self, name, bot):
    self.override_name = name
    self.bot = bot
