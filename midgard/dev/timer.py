"""Class for timing the running time of functions and code blocks

Description:
------------

The `dev.timer` can be used to log the running time of functions and general
code blocks. Typically, you will import the `Timer`-class from within the
module:

    from midgard.dev.timer import Timer

The Timer can then be used in three different ways:

1. As a decorator to time one function:

        @Timer('The time to execute some_function was')
        def some_function(some_argument, some_other_argument=some_value):
            pass

2. As a context manager together with `with` to time a code block:

        with Timer('Finish doing stuff in', logger=logger.debug) as t:
            do_something()
            do_something_else()

3. With explicit `start`- and `end`-statements:

        t = Timer()
        t.start()
        do_something()
        do_something_else()
        t.end()

As can be seen in the examples above, `Timer()` may be called with several
optional parameters, including the text to report when the timer ends and which
logger is used to report the timing. See `Timer.__init__` for more details.
"""

# Standard library imports
from contextlib import ContextDecorator
import time
from typing import Any, Callable, Optional

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import log


class Timer(ContextDecorator):
    """Class for timing running time of functions and code blocks.
    """

    def __init__(
        self, text: str = "Elapsed time:", fmt: str = ".4f", logger: Optional[Callable[[str], None]] = log.info
    ) -> None:
        """Set up a new timer

        The text to be shown when logging the timer can be customized.
        Typically, the value of the timer will be added at the end of the
        string (e.g. 'Elapsed time: 0.1234 seconds'). However, this can be
        customized by adding a '{}' to the text. For example `text='Used {} to
        run the code'` will produce something like 'Used 0.1234 seconds to run
        the code'.

        Args:
            text:    Text used when logging the timer (see above).
            fmt:     Format used when formatting the time (default 4 decimals).
            logger:  Function used to do the logging.
        """
        super().__init__()
        self._start: Optional[float] = None
        self._end: Optional[float] = None
        self.text = text if (text is None or "{}" in text) else (text + " {}").strip()
        self.fmt = fmt
        self.logger = (lambda _: None) if logger is None else logger

    @staticmethod
    def timer() -> float:
        """Get current value of timer

        Using the built-in `time.perf_counter` to do the timing.

        Returns:
            Current value of timer.
        """
        return time.perf_counter()

    def start(self) -> None:
        """Start the timer
        """
        self._start = self.timer()
        self._end = None

    def pause(self) -> float:
        """Pause the timer without logging. Use .start() to restart the timer
        """
        self._end = self.timer()
        time_elapsed = self.elapsed()
        self._start = None

        return time_elapsed

    def end(self) -> float:
        """End the timer and log the time elapsed

        Returns:
            The time elapsed in seconds.
        """
        time_elapsed = self.pause()
        self._log(time_elapsed)

        return time_elapsed

    def elapsed(self) -> float:
        """Log the time elapsed

        Can be used explicitly to log the time since a timer started without
        ending the timer.

        Returns:
            The time elapsed in seconds.
        """
        if self._start is None:
            raise exceptions.TimerNotRunning(
                f"The timer is not running. See `help({self.__module__})` for information on how to start one."
            )

        timer_end = self.timer() if self._end is None else self._end
        time_elapsed = 0 if self._start is None else timer_end - self._start

        return time_elapsed

    def _log(self, time_elapsed: float) -> None:
        """Do the actual logging of elapsed time

        Args:
            The time elapsed in seconds.
        """
        time_text = f"{time_elapsed:{self.fmt}} seconds"
        if self.text:
            self.logger(self.text.format(time_text))

    def __enter__(self) -> "Timer":
        """Start the timer as a context manager
        """
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        """End the timer and log the time elapsed as a context manager
        """
        self.end()


class AccumulatedTimer(Timer):
    def __init__(
        self, text: str = "Elapsed time:", fmt: str = ".4f", logger: Optional[Callable[[str], None]] = log.info
    ) -> None:
        super().__init__(text, fmt, logger)
        self.accumulated = 0.0

    def reset(self) -> None:
        """Reset the timer back to 0
        """
        if self._end is None:
            raise exceptions.TimerRunning(f"The timer is running and cannot be reset")

        self.accumulated = 0.0

    def end(self) -> float:
        """End the timer and log the time elapsed

        Returns:
            The time elapsed in seconds.
        """
        super().end()
        return self.accumulated

    def elapsed(self) -> float:
        """Log the time elapsed

        Can be used explicitly to log the time since a timer started without
        ending the timer.

        Returns:
            The time elapsed in seconds.
        """
        try:
            time_elapsed = super().elapsed()
        except exceptions.TimerNotRunning:
            time_elapsed = 0

        self.accumulated += time_elapsed
        return time_elapsed

    def _log(self, time_elapsed: float) -> None:
        """Do the actual logging of elapsed time

        Args:
            The time elapsed in seconds.
        """
        time_text = f"{time_elapsed:{self.fmt}}/{self.accumulated:{self.fmt}} seconds"
        if self.text:
            self.logger(self.text.format(time_text))
