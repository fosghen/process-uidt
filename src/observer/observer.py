from typing import Callable
from pathlib import Path

import queue
import threading
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from os import listdir

class AsyncFileHandler:
    # TODO: сделать сверку файлов в Figures и целевой папке. Недостающие закинуть в очередь. Можно и в основном потоке
    def __init__(self, callback: Callable, max_workers: int=1) -> None:
        self.file_queue: queue.Queue[Path] = queue.Queue()
        self.callback = callback
        self._stop_event = threading.Event()
        
        self.workers = [
            threading.Thread(
                target=self._process_files,
                daemon=True,
                name=f"FileWorker-{i}"
            ) for i in range(max_workers)
        ]
        for w in self.workers:
            w.start()

    def add_file(self, file_path: Path) -> None:
        """Добавление файла в очередь обработки"""
        self.file_queue.put(file_path)

    def _process_files(self) -> None:
        """Внутренний обработчик (работает в отдельных потоках)"""
        while not self._stop_event.is_set():
            try:
                file_path = self.file_queue.get(timeout=1)
                try:
                    self.callback(file_path)
                except Exception as e:
                    print(f"Ошибка обработки {file_path}: {str(e)}")
                finally:
                    self.file_queue.task_done()
            except queue.Empty:
                continue

    def stop(self) -> None:
        """Корректная остановка обработчиков"""
        self._stop_event.set()
        for w in self.workers:
            w.join(timeout=5)

class OnceFileHandler:
    def __init__(self, callback: Callable) -> None:
        self.callback = callback
    
    @staticmethod
    def _get_fnames(path: Path) -> list:
        fnames_all = listdir(path)
        fnames = []
        for fname in fnames_all:
            if fname.split(".")[-1] == "csv":
                fnames.append(path / fname)
        return fnames

    def process_directory(self, path: Path) -> None:
        fnames = OnceFileHandler._get_fnames(path)
        for fname in fnames:
            self.callback(fname)
        

class Watcher:
    def __init__(self, watch_path, callback):
        self.observer = Observer()
        handler = self._create_handler(callback)
        self.observer.schedule(handler, watch_path, recursive=True)

    def _create_handler(self, callback):
        class Handler(PatternMatchingEventHandler):
            def __init__(self):
                super().__init__(
                    patterns=["*.csv"],
                    ignore_directories=True,
                    case_sensitive=False,
                )
            
            def on_created(self, event):
                if not event.is_directory:
                    callback(Path(event.src_path)) # type: ignore
        return Handler()

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
