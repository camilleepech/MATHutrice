"""
evaluation_deadline.py — Une échéance pour tout un test d'évaluation

Spec EPF-MDE/MATHutrice#85, Design Document EPF-MDE/MATHutrice#83 : un test
d'évaluation se termine dans les 5 min du clic de l'étudiant.

L'appelant passe le client OpenAI, jamais le `client` global. Chaque appel
reçoit seulement le temps restant, par le `timeout` du client et sans
nouvelle tentative, donc les 600 s × 3 par défaut de la bibliothèque ne
s'appliquent jamais. Une fois l'échéance passée, aucun appel ne démarre :
l'appelant reçoit `DeadlineExceeded`.
"""

import time

import openai

EVALUATION_DEADLINE_SECONDS = 300


class DeadlineExceeded(Exception):
    """L'échéance de ce test d'évaluation est passée : il n'a pas pu être construit."""


class EvaluationDeadline:
    def __init__(self, client, seconds=EVALUATION_DEADLINE_SECONDS, clock=time.monotonic):
        self._client = client
        self._clock = clock
        self._ends_at = clock() + seconds

    def create(self, **kwargs):
        """Un `chat.completions.create` qui ne dépasse jamais l'échéance."""
        left = self._ends_at - self._clock()
        if left <= 0:
            raise DeadlineExceeded("l'échéance du test d'évaluation est passée")
        client = self._client.with_options(timeout=left, max_retries=0)
        try:
            return client.chat.completions.create(**kwargs)
        except (openai.APITimeoutError, openai.RateLimitError) as error:
            raise DeadlineExceeded("l'échéance du test d'évaluation est passée") from error
