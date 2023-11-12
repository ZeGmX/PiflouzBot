from interactions import Task, IntervalTrigger, OrTrigger, TimeTrigger
from datetime import datetime, timezone


class TaskCustom(Task):
  """
  A Task class that allows to execute a function at the start of the task
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._first_fire = False


  def start(self, *args, **kwargs):
    self._check_first_start(self.trigger, *args, **kwargs)
    super().start(*args, **kwargs)
  

  def _check_first_start(self, trigger, *args, **kwargs):
    """
    If the task contains an IntervalTrigger, this function will execute the task once at the start
    --
    input:
      trigger: interactions.Trigger
    """
    if self._first_fire: return

    if isinstance(trigger, IntervalTrigger):
      self._fire(datetime.now(tz=timezone.utc), *args, **kwargs)
      self._first_fire = True
    
    elif isinstance(trigger, OrTrigger):
      for t in trigger.triggers:
        self._check_first_start(t, *args, **kwargs)

  
  def on_error(self, error: Exception):
    print(f"Error in task {self.callback.__name__}: {error}")



class TimeTriggerDT(TimeTrigger):
  """
  A TimeTrigger class that can be initialized with a datetime object
  """

  def __init__(self, datetime: datetime):
    super().__init__(datetime.hour, datetime.minute, datetime.second)