from pathlib import Path
from time import sleep
import numpy as np
import polars as pl

from plotter.plotter import Plotter
from processing.peak_finder import PeakFinder

class Processor:
    def __init__(self, num_pts_norm, point_cut, point_start, point_end, freq_cut, data_type, transparency, inv: str="auto"):
        self.inv = inv    
        self.num_pts_norm = num_pts_norm

        self.point_cut = point_cut
        self.point_start = point_start
        self.point_end = point_end
        self.freq_cut = freq_cut

        self.transparency = transparency

        self.data_type = data_type

        self.dx = 1

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

    def process_file(self, path: Path) -> None:
        sleep(0.5)
        data, freqs = self._read_file(path)

        data_norm = self._norm_data_by_ballast(data, self._define_num_phase(path))
        data_norm = data_norm * self._make_inv(data_norm)
        plotter = Plotter(self.freq_cut, self.point_cut, self.point_start,
                 self.point_end, self.dx, self.transparency, "Figures")
        length = self._get_length(path)
        finder = PeakFinder(self.data_type)
 
        f0 = finder.find_peak(freqs, self._norm_data_by_max(data_norm).T[self._get_index(self.point_start): self._get_index(self.point_end)])
        plotter.create_plot(data_norm, freqs, length, f0, path)