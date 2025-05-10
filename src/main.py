from time import sleep
from pathlib import Path

from src.observer.observer import AsyncFileHandler, Watcher
from src.processing.precessor import Processor
from src.initializer.initializer import Reader
from src.initializer.argparser import CommandLineParser

def main():
    parser = CommandLineParser()
    args = parser.parse()

    if args.params:
        params = Reader(Path(args.params)).read_init_file()
    else:
        params = Reader(Path(args.path) / "params.yaml").write_default_init_file()
    

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
        watch_path=Path(args.path),
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
