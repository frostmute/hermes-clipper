import os
import threading
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .main import setup_vault_index

class VaultEventHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, debounce: float = 2.0):
        self.vault_path = vault_path
        self.debounce = debounce
        self.timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            self._trigger_sync()

    def _trigger_sync(self):
        with self._lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(self.debounce, self._sync)
            self.timer.daemon = True
            self.timer.start()

    def _sync(self):
        try:
            setup_vault_index(self.vault_path)
        except Exception as e:
            logging.error(f"Vault sync failed: {e}")

class VaultWatcher:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.observer = Observer()
        self.handler = VaultEventHandler(vault_path)

    def start(self):
        if not os.path.exists(self.vault_path):
            return
        self.observer.schedule(self.handler, self.vault_path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
        if self.handler.timer:
            self.handler.timer.cancel()
