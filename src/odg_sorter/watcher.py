import threading
from collections.abc import Callable, Iterable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class Watcher:
    def __init__(
        self,
        watched_paths: Iterable[Path],
        on_landed: Callable[[Path], None],
        debounce_seconds: float = 2.0,
    ) -> None:
        self._paths = [Path(p) for p in watched_paths]
        self._on_landed = on_landed
        self._debounce = debounce_seconds
        self._observer = Observer()
        self._timers: dict[Path, threading.Timer] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        handler = _Handler(self._schedule)
        for p in self._paths:
            p.mkdir(parents=True, exist_ok=True)
            self._observer.schedule(handler, str(p), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5.0)
        with self._lock:
            for t in self._timers.values():
                t.cancel()

    def _schedule(self, path: Path) -> None:
        with self._lock:
            existing = self._timers.pop(path, None)
            if existing is not None:
                existing.cancel()
            t = threading.Timer(self._debounce, self._fire, args=(path,))
            self._timers[path] = t
            t.daemon = True
            t.start()

    def _fire(self, path: Path) -> None:
        with self._lock:
            self._timers.pop(path, None)
        if not path.exists():
            return
        if not _file_is_closed(path):
            self._schedule(path)
            return
        self._on_landed(path)


class _Handler(FileSystemEventHandler):
    def __init__(self, schedule: Callable[[Path], None]) -> None:
        self._schedule = schedule

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(Path(event.src_path))


def _file_is_closed(path: Path) -> bool:
    """On Windows, opening with mode 'rb' fails if another process holds the file open for write."""
    try:
        with path.open("rb"):
            pass
        return True
    except OSError:
        return False
