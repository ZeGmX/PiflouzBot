import interactions


class Client(interactions.Client):
  """
  A custom bot client to simplify some function calls
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)


  async def get_channel(self, channel_id):
    """
    Get a discord channel given its id
    --
    input:
      channel_id: int
    """
    data = await self._http.get_channel(channel_id)
    return interactions.Channel(_client=self._http, **data)


  def dispatch(self, *args, **kwargs):
    """
    Dispatches an event with the arguments
    The first argument should be a string corresponding to the event name
    """
    self._websocket._dispatch.dispatch(*args, **kwargs)


  def register_listener(self, *args, **kwargs):
    """
    registers a new listener
    The first argument should be the corresponding coroutine, and the "name" argument should be the name of the event
    """
    self._websocket._dispatch.register(*args, **kwargs)