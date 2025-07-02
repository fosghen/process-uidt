from pathlib import Path
from time import sleep
import numpy as np
import polars as pl

from src.saver.peak_saver import PeakSaver
from src.saver.plotter import Plotter, PlotterStats
from src.processing.peak_finder import PeakFinder
from src.processing.stats_computer import StatsComputer
from src.initializer.initializer import AppParams

class Processor:
    def __init__(self, params: AppParams):
        self.inv = params.inv    
        self.num_pts_norm = params.num_pts_norm

        self.point_cut = params.point_cut
        self.point_start = params.point_start
        self.point_end = params.point_end
        self.freq_cut = params.freq_cut

        self.transparency = params.transparency

        self.data_type = params.data_type

        self.dx = 1

        self.plotter = Plotter(self.freq_cut, self.point_cut, self.point_start,
                 self.point_end, self.dx, Path("Figures"), self.transparency)
        self.finder = PeakFinder(self.data_type)
        self.saver = PeakSaver(Path("Peaks"))
        self.stats_plotter = PlotterStats(Path("Figures"), max=params.max_std)
        self.stats_cumputer = StatsComputer(51)

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
    
    def _check_end_creating(self, path: Path) -> None:
        # Ждём, пока закончится запись файла
        file_size_prev = 0
        
        while (path.stat().st_size != file_size_prev):
            file_size_prev = path.stat().st_size
            sleep(0.5)

    def _read_file(self, path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self._check_end_creating(path)
        skip_rows, freqs = self._define_rowskip(path)
        
        data = pl.read_csv(
            path,
            separator=";",
            skip_rows=skip_rows,
            columns=range(0, len(freqs) + 1), 
            truncate_ragged_lines=True
            ).with_columns([pl.col("*").cast(pl.Float32)]).to_numpy()
        length = data[:, 0]
        self.dx = abs(length[1] - length[0])

        return data[:, 1:], np.array(freqs, dtype=np.float32), length

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

    def _data_prepare(self, path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        data, freqs, length = self._read_file(path)
        data_norm = self._norm_data_by_ballast(data, self._define_num_phase(path))
        return data_norm * self._make_inv(data_norm), freqs, length


    def process_file(self, path: Path) -> None:
        sleep(0.5)
        print(f"Начали обрабатывать {path}")
        
        data_norm, freqs, length = self._data_prepare(path)
        point_end = min(data_norm.shape[0] * self.dx - self.dx, self.point_end)
        
        self.plotter.output_dir = path.parent / "Figures"
        self.plotter.dx = abs(length[1] - length[0])
        self.plotter.point_end = point_end

        self.saver.output_dir = path.parent / "Peaks"
        self.stats_plotter.output_dir = path.parent / "Figures"

        f0 = self.finder.find_peak(freqs,
                                self._norm_data_by_max(data_norm).T[self._get_index(self.point_start):
                                                                    self._get_index(point_end)])
        
        approx_laplace = self.finder.get_approx_laplace(
            freqs, 
            self._norm_data_by_max(data_norm).T[[self._get_index(self.point_start), self._get_index(self.point_cut), self._get_index(point_end)]]
            )

        self.plotter.create_plot(data_norm,
                            freqs,
                            length,
                            f0,
                            path,
                            approx_laplace)
        
        self.stats_plotter.plot_std(
            self.stats_cumputer.compute_std(f0),
            length[self._get_index(self.point_start): self._get_index(point_end)], path)
        
        self.saver.add_peak(f0, path.stem, length[self._get_index(self.point_start): self._get_index(point_end)])
        print(f"Закончили обрабатывать {path}")