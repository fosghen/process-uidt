from time import sleep
from pathlib import Path

from observer.observer import AsyncFileHandler, Watcher
from processing.precessor import Processor

def custom_file_processor(file_path):
    """Ваш кастомный обработчик файлов"""
    print(f"\n[Обработка] Начало работы с {file_path}")
    sleep(2)  # Имитация долгой операции
    print(f"[Обработка] Завершено: {file_path}")

def main():
    processor = Processor(num_pts_norm=10, point_cut=1500, point_start=0, point_end=5000, freq_cut=10700, transparency=0.5)

    async_handler = AsyncFileHandler(
        callback=processor.process_file,
        max_workers=1
    )

    watcher = Watcher(
        watch_path=Path(r"D:/Process UIDT/test path"),
        callback=async_handler.add_file,
    )
    watcher.start()

    try:
        while True:
            print(f"\nАктивных задач: {async_handler.file_queue.qsize()}")
            sleep(5)
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
        watcher.stop()
        async_handler.stop()

if __name__ == "__main__":
    main()
