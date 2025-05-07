from time import sleep
from pathlib import Path

from observer.observer import AsyncFileHandler, Watcher
from processing.precessor import Processor
from initializer.initializer import Reader

def main():
    # TODO: сделать проверку на наличие файла, если нет, то создать стандартный
    params = Reader(Path("D:/process-uidt/test_path/params.yaml")).read_init_file()

    processor = Processor(num_pts_norm=params.num_pts_norm, 
                          point_cut=params.point_cut,
                          point_start=params.point_start,
                          point_end=params.point_end,
                          freq_cut=params.freq_cut,
                          transparency=params.transparency,
                          data_type=params.data_type)

    async_handler = AsyncFileHandler(
        callback=processor.process_file,
        max_workers=1
    )

    watcher = Watcher(
        watch_path=Path(r"D:/process-uidt/test_path"),
        callback=async_handler.add_file,
    )
    watcher.start()

    try:
        while True:
            print(f"\nАктивных задач: {async_handler.file_queue.qsize()}")
            sleep(0.1)
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
        watcher.stop()
        async_handler.stop()

if __name__ == "__main__":
    main()
