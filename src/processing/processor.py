from pathlib import Path
from time import sleep
import numpy as np
import polars as pl

from src.saver.peak_saver import PeakSaver
from src.saver.plotter import Plotter
from src.processing.peak_finder import PeakFinder

class Processor:
    def __init__(self, num_pts_norm: int, point_cut: float,
                 point_start: float, point_end: float, freq_cut: int,
                 data_type: str, transparency: float, inv: str="auto"):
        self.inv = inv    
        self.num_pts_norm = num_pts_norm

        self.point_cut = point_cut
        self.point_start = point_start
        self.point_end = point_end
        self.freq_cut = freq_cut

        self.transparency = transparency

        self.data_type = data_type

        self.dx = 1

        self.plotter = Plotter(self.freq_cut, self.point_cut, self.point_start,
                 self.point_end, self.dx, Path("Figures"), self.transparency)
        self.finder = PeakFinder(self.data_type)
        self.saver = PeakSaver(Path("Peaks"))

    def _define_rowskip(self, fname: Path) -> tuple[int, list[str]]:
        with fname.open() as f:
            for i, line in enumerate(f):
                if line.split(";")[0] == "Length:":
                    freqs = line.strip().split(";f(MHz)=")[1:]
                    return i, freqs
        raise ValueError("Header not found in file.")

    def _get_length(self, fname: Path) -> np.ndarray:
        with fname.open() as f:
            for line in f:
                if line.startswith("Point"):
                    return np.array(line.strip().split(";")[1:], dtype=float)
        raise ValueError("Length info not found.")

    def _make_inv(self, data: np.ndarray) -> int:
        coef = 1
        if self.inv == "auto":
            ref = data[int(self.point_cut / self.dx)]
            coef = -1 if (ref.mean() - ref.min()) > (ref.max() - ref.mean()) else 1
        elif self.inv:
            coef = -1
        return coef
    
    def _read_file(self, path: Path) -> tuple[np.ndarray, np.ndarray]:
        skip_rows, freqs = self._define_rowskip(path)
        
        data = pl.read_csv(path, separator=";", skip_rows=skip_rows, columns=range(1, len(freqs) + 1)).to_numpy()
        length = self._get_length(path)
        self.dx = abs(length[1] - length[0])

        return data, np.array(freqs, dtype=np.float32)

    def _define_num_phase(self, fname: Path) -> int:
        with fname.open() as f:
            f.readline()
            return int(f.readline().split(";")[3].split("=")[1])

    def _norm_data_by_ballast(self, data: np.ndarray, num_phase_shift: int) -> np.ndarray:
        reshaped = data.reshape((-1, num_phase_shift, data.shape[1]))
        baseline = reshaped[:self.num_pts_norm].mean(axis=0)
        return (reshaped - baseline).reshape((-1, data.shape[1]))
    
    def _norm_data_by_max(self, data: np.ndarray) -> np.ndarray:
        data = data.T
        data -= data.min(axis=0)
        return data / data.max(axis=0)

    def _get_index(self, length: float) -> int:
        return int(length / self.dx)

    def _data_prepare(self, path: Path) -> tuple[np.ndarray, np.ndarray]:
        data, freqs = self._read_file(path)
        data_norm = self._norm_data_by_ballast(data, self._define_num_phase(path))
        return data_norm * self._make_inv(data_norm), freqs


    def process_file(self, path: Path) -> None:
        sleep(0.5)
        print(f"Начали обрабатывать {path}")
        
        data_norm, freqs = self._data_prepare(path)
        length = self._get_length(path)
        
        self.plotter.output_dir = path.parent / "Figures"
        self.plotter.dx = abs(length[1] - length[0])

        self.saver.output_dir = path.parent / "Peaks"

        f0 = self.finder.find_peak(freqs,
                                self._norm_data_by_max(data_norm).T[self._get_index(self.point_start):
                                                                    self._get_index(self.point_end)])
        self.plotter.create_plot(data_norm,
                            freqs,
                            length[self._get_index(self.point_start):
                                   self._get_index(self.point_end)],
                            f0,
                            path)
        self.saver.add_peak(f0, path.stem)
        print(f"Закончили обрабатывать {path}")