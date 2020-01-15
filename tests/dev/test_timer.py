"""Tests for the dev.timer-module

"""
# Standard library imports
import re

# Third party imports
import pytest

# Midgard imports
from midgard.dev import exceptions
from midgard.dev.timer import AccumulatedTimer, Timer


#
# Test functions
#
TIME_MESSAGE = "Wasted time:"
RE_TIME_MESSAGE = re.compile(TIME_MESSAGE + r" 0\.\d{4} seconds")


@Timer(TIME_MESSAGE, logger=print)
def timewaster(num):
    """Just waste a little bit of time"""
    sum(n ** 2 for n in range(num))


@AccumulatedTimer(TIME_MESSAGE, logger=print)
def accumulated_timewaste(num):
    """Just waste a little bit of time"""
    sum(n ** 2 for n in range(num))


class CustomLogger:
    """Simple class used to test custom logging capabilities in Timer"""

    def __init__(self):
        self.messages = ""

    def __call__(self, message):
        self.messages += message


#
# Tests
#
def test_timer_as_decorator(capsys):
    """Test that decorated function prints timing information"""
    timewaster(1000)
    stdout, stderr = capsys.readouterr()
    assert RE_TIME_MESSAGE.match(stdout)
    assert stdout.count("\n") == 1
    assert stderr == ""


def test_timer_as_context_manager(capsys):
    """Test that timed context prints timing information"""
    with Timer(TIME_MESSAGE, logger=print):
        sum(n ** 2 for n in range(1000))
    stdout, stderr = capsys.readouterr()
    assert RE_TIME_MESSAGE.match(stdout)
    assert stdout.count("\n") == 1
    assert stderr == ""


def test_explicit_timer(capsys):
    """Test that timed section prints timing information"""
    t = Timer(TIME_MESSAGE, logger=print)
    t.start()
    sum(n ** 2 for n in range(1000))
    t.end()
    stdout, stderr = capsys.readouterr()
    assert RE_TIME_MESSAGE.match(stdout)
    assert stdout.count("\n") == 1
    assert stderr == ""


def test_error_if_timer_not_running():
    """Test that timer raises error if it is stopped before started"""
    t = Timer(TIME_MESSAGE, logger=print)
    with pytest.raises(exceptions.TimerNotRunning):
        t.end()


def test_access_timer_object_in_context(capsys):
    """Test that we can access the timer object inside a context"""
    with Timer(TIME_MESSAGE, logger=print) as t:
        assert isinstance(t, Timer)
        assert t.text.startswith(TIME_MESSAGE)
    _, _ = capsys.readouterr()  # Do not print log message to standard out


def test_text_with_format(capsys):
    """Test that we can explicitly add point where time is inserted in text"""
    time_message = "Used {} to run the code"
    with Timer(time_message, logger=print):
        sum(n ** 2 for n in range(1000))
    stdout, stderr = capsys.readouterr()
    assert re.match(time_message.format(r"0\.\d{4} seconds"), stdout)
    assert stdout.count("\n") == 1
    assert stderr == ""


def test_format_of_time_elapsed(capsys):
    """Test that we can change the format of the time elapsed"""
    with Timer(TIME_MESSAGE, fmt=".8f", logger=print):
        sum(n ** 2 for n in range(1000))
    stdout, stderr = capsys.readouterr()
    assert re.match(TIME_MESSAGE + r" 0\.\d{8} seconds", stdout)
    assert stdout.count("\n") == 1
    assert stderr == ""


def test_custom_logger():
    """Test that we can use a custom logger"""
    logger = CustomLogger()
    with Timer(TIME_MESSAGE, logger=logger):
        sum(n ** 2 for n in range(1000))
    assert RE_TIME_MESSAGE.match(logger.messages)


def test_timer_without_text(capsys):
    """Test that timer with None text does not print anything"""
    with Timer(None, logger=print):
        sum(n ** 2 for n in range(1000))

    stdout, stderr = capsys.readouterr()
    assert stdout == ""
    assert stderr == ""


def test_accumulated_decorator(capsys):
    """Test that decorated timer can accumulate"""
    accumulated_timewaste(1000)
    accumulated_timewaste(1000)

    stdout, stderr = capsys.readouterr()
    lines = stdout.strip().split("\n")
    assert len(lines) == 2
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", lines[0])
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", lines[1])
    assert stderr == ""


def test_accumulated_context_manager(capsys):
    """Test that context manager timer can accumulate"""
    t = AccumulatedTimer(TIME_MESSAGE, logger=print)
    with t:
        sum(n ** 2 for n in range(1000))
    with t:
        sum(n ** 2 for n in range(1000))

    stdout, stderr = capsys.readouterr()
    lines = stdout.strip().split("\n")
    assert len(lines) == 2
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", lines[0])
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", lines[1])
    assert stderr == ""


def test_accumulated_explicit_timer(capsys):
    """Test that explicit timer can accumulate"""
    t = AccumulatedTimer(TIME_MESSAGE, logger=print)
    t.start()
    sum(n ** 2 for n in range(1000))
    t.end()
    t.start()
    sum(n ** 2 for n in range(1000))
    t.end()

    stdout, stderr = capsys.readouterr()
    lines = stdout.strip().split("\n")
    assert len(lines) == 2
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", lines[0])
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", lines[1])
    assert stderr == ""


def test_accumulated_explicit_timer_with_pause(capsys):
    """Test that explicit timer can be paused"""
    t = AccumulatedTimer(TIME_MESSAGE, logger=print)
    laps = list()
    for _ in range(3):
        t.start()
        sum(n ** 2 for n in range(1000))
        laps.append(t.pause())
    total = t.end()
    assert sum(laps) == total

    stdout, stderr = capsys.readouterr()
    assert re.match(TIME_MESSAGE + r" 0\.\d{4}/0\.\d{4} seconds", stdout)
    assert stdout.count("\n") == 1
    assert stderr == ""


def test_consecutive_pauses():
    """Test that consecutive pauses just returns 0"""
    t = AccumulatedTimer(TIME_MESSAGE)
    t.start()
    sum(n ** 2 for n in range(1000))
    t.pause()
    sum(n ** 2 for n in range(1000))
    assert t.pause() == 0


def test_resetting_timer():
    """Test that timer is reset to 0"""
    t = AccumulatedTimer(TIME_MESSAGE)
    t.start()
    sum(n ** 2 for n in range(1000))
    assert t.end() > 0

    t.reset()
    assert t.end() == 0


def test_error_if_resetting_running_timer():
    """Test that resetting a running timer raises an error"""
    t = AccumulatedTimer(TIME_MESSAGE)
    t.start()
    with pytest.raises(exceptions.TimerRunning):
        t.reset()
