import argparse

class CommandLineParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="--path путь до папки с данными\n" \
        "--params путь до файла с параметрами")
        self._setup_arguments()

    def _str2bool(self, v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    def _setup_arguments(self):
        self.parser.add_argument('--path', type=str, required=False, default='.',
                                 help="Путь до папки с данными, если не указано, то папка откуда вызвана команда")
        self.parser.add_argument('--params', type=str, required=False,
                                help="Путь до файла с параметрами, если не указано," \
                                " то ищется в папке, где вызвано. При не нахождении создаёт шаблон")
        self.parser.add_argument("--monitor", type=self._str2bool, required=False,
                        help="Выполнять мониторинг папки. true - мониторим папку," \
                        " false - обрабатывает то, что уже есть.")

    def parse(self):
        return self.parser.parse_args()
    