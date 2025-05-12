from time import sleep
from pathlib import Path

from src.observer.observer import AsyncFileHandler, Watcher, OnceFileHandler
from src.processing.processor import Processor
from src.initializer.initializer import Reader
from src.initializer.argparser import CommandLineParser

def main():
    parser = CommandLineParser()
    args = parser.parse()

    if (Path(args.path) / args.params).is_file():
        params = Reader(Path(args.path) / args.params).read_init_file()
    else:
        params = Reader(Path(args.path) / "params.yaml").write_default_init_file()
    
    processor = Processor(num_pts_norm=params.num_pts_norm, 
                          point_cut=params.point_cut,
                          point_start=params.point_start,
                          point_end=params.point_end,
                          freq_cut=params.freq_cut,
                          transparency=params.transparency,
                          data_type=params.data_type)

    if not args.monitor:
        OnceFileHandler(processor.process_file).process_directory(Path(args.path))
        processor.saver.save_file()
        return

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
            sleep(1)
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
        processor.saver.save_file()
        watcher.stop()
        async_handler.stop()

if __name__ == "__main__":
    main()
