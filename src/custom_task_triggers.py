from datetime import datetime, timedelta
from interactions import Task, IntervalTrigger, OrTrigger, TimeTrigger
import logging
from pytz import timezone
import traceback

from custom_exceptions import Custom_Task_Exception


logger = logging.getLogger("custom_log")


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
            self._fire(datetime.now(tz=timezone("UTC")), *args, **kwargs)
            self._first_fire = True
        
        elif isinstance(trigger, OrTrigger):
            for t in trigger.triggers:
                self._check_first_start(t, *args, **kwargs)

    
    def on_error(self, error: Exception):
        if not isinstance(error, Custom_Task_Exception):
            msg = f"Error in task {self.callback.__name__}: {error}"
            msg += "\n" + "".join(traceback.format_exception(error))
            print(f"\033[91m{msg}\033[0m")
            logger.error(msg)
        else:
            msg = f"Error in task {self.callback.__name__}: {error}"
            print(f"\033[93m{msg}\033[0m")
            logger.warning(msg)


class TimeTriggerDT(TimeTrigger):
    """
    A TimeTrigger class that can be initialized with a datetime.time object
    """

    def __init__(self, datetime: datetime):
        super().__init__(datetime.hour, datetime.minute, datetime.second)
    
    
    # override
    def next_fire(self) -> datetime | None:
        tz = timezone("Europe/Paris")
        t1 = datetime.now(tz=tz)
        t2 = t1.replace(hour=self.target_time[0], minute=self.target_time[1], second=self.target_time[2], microsecond=0)
        
        if t2 < t1:
            t2 += timedelta(days=1)

        t2 += timedelta(seconds=5)  # to avoid rounding errors where the next fire is actually at t2 - epsilon, so the task is called several times
        # Setting timezones make it independent of summer/winter time
        return t2