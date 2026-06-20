"""User-facing 'working...' feedback during slow operations.

This is the seam between the program and whatever the device can show. Today
that's a terminal spinner; on the physical unit it'll be a screen. Callers only
depend on the ``Status.working`` context manager, so swapping the
implementation doesn't touch the rest of the program.
"""

import contextlib
import itertools
import sys
import threading


class Status:
    """Base indicator. The default does nothing, which is a safe no-op."""

    @contextlib.contextmanager
    def working(self, message):
        yield


class TerminalSpinner(Status):
    """Animates a spinner on stderr while the wrapped block runs.

    The animation lives in a background thread so a blocking call (e.g. an LLM
    request) keeps the line moving. The line is cleared on exit, whether the
    block returns normally or raises.
    """

    @contextlib.contextmanager
    def working(self, message):
        done = threading.Event()

        def spin():
            for frame in itertools.cycle("|/-\\"):
                if done.is_set():
                    break
                sys.stderr.write(f"\r{frame} {message}")
                sys.stderr.flush()
                done.wait(0.1)

        thread = threading.Thread(target=spin)
        thread.start()
        try:
            yield
        finally:
            done.set()
            thread.join()
            sys.stderr.write("\r\033[K")
            sys.stderr.flush()
