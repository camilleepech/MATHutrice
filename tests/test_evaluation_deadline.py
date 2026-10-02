"""An evaluation test ends within 5 min: Spec EPF-MDE/MATHutrice#85.

The deadline is passed the OpenAI client and the clock it reads by its caller.
The fake client below stands in for the LLM endpoint: it records the timeout
and retries each call was given, and never reaches the network.
"""

import openai
import pytest

from mathutrice.evaluation_deadline import DeadlineExceeded, EvaluationDeadline

# The number, from the Design Document EPF-MDE/MATHutrice#83.
FIVE_MINUTES = 300


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class FakeOpenAI:
    """Just enough of `openai.OpenAI` for one chat completion."""

    def __init__(self, error=None, timeout=None, max_retries=None, calls=None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.calls = [] if calls is None else calls
        self._error = error
        self.chat = self
        self.completions = self

    def with_options(self, *, timeout, max_retries):
        return FakeOpenAI(self._error, timeout, max_retries, self.calls)

    def create(self, **kwargs):
        self.calls.append((self.timeout, self.max_retries))
        if self._error:
            raise self._error
        return "answer"


def test_the_first_call_is_given_the_whole_five_minutes_and_no_retries():
    client, clock = FakeOpenAI(), FakeClock()
    deadline = EvaluationDeadline(client, clock=clock)

    assert deadline.create(model="m", messages=[]) == "answer"

    assert client.calls == [(FIVE_MINUTES, 0)]


def test_each_call_is_given_only_the_time_left():
    client, clock = FakeOpenAI(), FakeClock()
    deadline = EvaluationDeadline(client, clock=clock)

    clock.now += 120
    deadline.create(model="m", messages=[])

    assert client.calls == [(180, 0)]


def test_no_call_starts_once_the_deadline_has_passed():
    client, clock = FakeOpenAI(), FakeClock()
    deadline = EvaluationDeadline(client, clock=clock)

    clock.now += FIVE_MINUTES
    with pytest.raises(DeadlineExceeded):
        deadline.create(model="m", messages=[])

    assert client.calls == []


def test_a_call_that_times_out_reports_the_deadline_to_its_caller():
    client = FakeOpenAI(error=openai.APITimeoutError(request=None))
    deadline = EvaluationDeadline(client, clock=FakeClock())

    with pytest.raises(DeadlineExceeded):
        deadline.create(model="m", messages=[])
