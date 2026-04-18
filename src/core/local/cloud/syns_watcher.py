# src/core/local/cloud/sync_watcher.py
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CloudSyncHandler(FileSystemEventHandler):
    def __init__(self, cloud_bridge, debounce_sec: float = 1.0):
        self.cloud_bridge = cloud_bridge
        self.debounce_sec = debounce_sec

    def _handle_change(self, path: str):
        time.sleep(self.debounce_sec)
        file_path = Path(path)
        if not file_path.exists():
            return
        try:
            rel_path = file_path.relative_to(self.cloud_bridge.local_path)
            remote_path = "/" + str(rel_path)
            if file_path.is_file():
                print(f"Syncing: {file_path.name}")
                self.cloud_bridge.upload_file(file_path, remote_path)
        except ValueError:
            pass

    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle_change, args=(event.src_path,)).start()

    def on_modified(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle_change, args=(event.src_path,)).start()


class SyncWatcher:
    def __init__(self, cloud_bridge, local_path: Path):
        self.cloud_bridge = cloud_bridge
        self.local_path = local_path
        self.observer = None
        self.running = False
        self.cloud_thread = None
        self._stop_event = threading.Event()

    def _check_cloud_loop(self):
        while not self._stop_event.is_set():
            time.sleep(2)
            if self.cloud_bridge.has_token():
                try:
                    remote_items = self.cloud_bridge.provider.list_files("/")
                    remote_files = [item for item in remote_items if not item.is_dir]
                    for item in remote_files:
                        local_file = self.cloud_bridge.local_path / item.path.lstrip('/')
                        if not local_file.exists():
                            print(f"Downloading: {item.name}")
                            self.cloud_bridge.download_file(item.path, local_file)
                except Exception:
                    pass

    def start_background(self):
        if self.running:
            return
        self.running = True
        self._stop_event.clear()
        self.handler = CloudSyncHandler(self.cloud_bridge)
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.local_path), recursive=True)
        self.observer.start()
        self.cloud_thread = threading.Thread(target=self._check_cloud_loop, daemon=True)
        self.cloud_thread.start()
        print("Background sync started")

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self.observer:
            self.observer.stop()
            self.observer.join()
        print("Background sync stopped")