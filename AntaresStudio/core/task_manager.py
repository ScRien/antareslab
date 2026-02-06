from __future__ import annotations

import traceback
import threading
from dataclasses import dataclass
from typing import Any, Callable, Optional

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    started = pyqtSignal(str)
    progress = pyqtSignal(str, int)          # task_id, percent
    message = pyqtSignal(str, str)           # task_id, message
    result = pyqtSignal(str, object)         # task_id, payload
    error = pyqtSignal(str, str, str)        # task_id, short, details
    finished = pyqtSignal(str)               # task_id


@dataclass(frozen=True)
class TaskHandle:
    task_id: str
    cancel_event: threading.Event


class TaskRunnable(QRunnable):
    def __init__(
        self,
        task_id: str,
        fn: Callable[..., Any],
        *,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        signals: Optional[WorkerSignals] = None,
        cancel_event: Optional[threading.Event] = None,
    ):
        super().__init__()
        self.task_id = task_id
        self.fn = fn
        self.args = args
        self.kwargs = kwargs or {}
        self.signals = signals or WorkerSignals()
        self.cancel_event = cancel_event or threading.Event()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        self.signals.started.emit(self.task_id)
        try:
            # Fonksiyona cancel_event / progress callback enjekte edelim (opsiyonel)
            if "cancel_event" in self.fn.__code__.co_varnames:
                self.kwargs["cancel_event"] = self.cancel_event
            if "progress_cb" in self.fn.__code__.co_varnames:
                self.kwargs["progress_cb"] = lambda p: self.signals.progress.emit(self.task_id, int(p))
            if "message_cb" in self.fn.__code__.co_varnames:
                self.kwargs["message_cb"] = lambda m: self.signals.message.emit(self.task_id, str(m))

            out = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(self.task_id, out)
        except Exception as e:
            short = f"{type(e).__name__}: {e}"
            details = traceback.format_exc()
            self.signals.error.emit(self.task_id, short, details)
        finally:
            self.signals.finished.emit(self.task_id)


class TaskManager(QObject):
    """
    UI tarafında tek noktadan task başlat / iptal et / sinyalleri bağla.
    """
    def __init__(self, max_threads: Optional[int] = None):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        if max_threads:
            self.pool.setMaxThreadCount(max_threads)
        self._active: dict[str, TaskHandle] = {}

    def submit(self, task_id: str, fn: Callable[..., Any], *, args=(), kwargs=None, signals=None) -> TaskHandle:
        cancel_event = threading.Event()
        handle = TaskHandle(task_id=task_id, cancel_event=cancel_event)
        self._active[task_id] = handle

        runnable = TaskRunnable(
            task_id=task_id,
            fn=fn,
            args=args,
            kwargs=kwargs,
            signals=signals,
            cancel_event=cancel_event,
        )
        self.pool.start(runnable)
        return handle

    def cancel(self, task_id: str) -> None:
        h = self._active.get(task_id)
        if h:
            h.cancel_event.set()

    def is_cancelled(self, task_id: str) -> bool:
        h = self._active.get(task_id)
        return bool(h and h.cancel_event.is_set())

    def forget(self, task_id: str) -> None:
        self._active.pop(task_id, None)
