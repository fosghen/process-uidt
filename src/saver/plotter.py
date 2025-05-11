import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

class Plotter:
    def __init__(self, freq_cut: int, point_cut: float, point_start: float,
                 point_end: float, dx: float, output_dir: Path,
                 transparency: float=0.5):
        self.output_dir = output_dir
        self.freq_cut = freq_cut
        self.point_cut = point_cut
        self.point_start = point_start
        self.point_end = point_end
        self.dx = dx
        self.transparency = transparency

    def create_plot(self, data: np.ndarray, freqs: np.ndarray, length: np.ndarray,
                    f0: np.ndarray, fname: Path):
            
        fig, ax = plt.subplots(2, 4, 
                              gridspec_kw={
                                  'width_ratios': [5, 1, 1, 1], 
                                  'height_ratios': [5, 1]
                              },
                              figsize=(12, 6))
        
        for i in range(1, 4): 
            fig.delaxes(ax[1, i])
        
        self._plot_reflectograms(ax[0, 0], data, freqs, length, f0)
        
        self._plot_additional_slices(ax, data, freqs, length)
        
        save_path = self.output_dir / f"{fname.stem}.png"

        self.output_dir.mkdir(exist_ok=True)

        plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
        plt.close()
        return save_path
    
    def _get_index(self, length: float) -> int:
        return int(length / self.dx)

    def _plot_reflectograms(self, ax: plt.Axes, data: np.ndarray, freqs: np.ndarray, # type: ignore
                            length: np.ndarray, peaks_freq: np.ndarray):  
        point_end = min(self.point_end, data.shape[0] * self.dx - self.dx)
        
        data_norm = data.T.copy()
        data_norm -= data_norm.min(axis=0)
        data_norm /= data_norm.max(axis=0)
        
        ax.imshow(
            data_norm[:, self._get_index(self.point_start): 
                      self._get_index(point_end)],
            aspect="auto",
            extent=(self.point_start,
                    point_end,
                    freqs.max(),
                    freqs.min()
                    )
                    )

        ax.plot(length,
                peaks_freq,
                alpha=self.transparency,
                c='k')
        
        ax.axhline(self.freq_cut, c="lightgreen", lw=1)

        for mark in [self.point_cut, self.point_start, point_end]:
            ax.axvline(length[self._get_index(mark)], color='r', lw=1)
            
        ax.set_ylabel("Частота, МГц")
    
    def _plot_additional_slices(self, ax, data, freqs, length):
        """Отрисовка дополнительных срезов"""
        labels = ["Начало", "Срез", "Конец"]

        point_end = min(self.point_end, data.shape[0] * self.dx - self.dx)

        ind_freq = int((self.freq_cut - freqs[0]) / abs(freqs[1] - freqs[0]))
        ax[1, 0].plot(length[self._get_index(self.point_start): self._get_index(point_end)],
                      data[self._get_index(self.point_start): self._get_index(point_end),
                        ind_freq])
        
        
        ax[1, 0].set_xlim(self.point_start, point_end)
        ax[1, 0].set_xlabel("Расстояние, м")

        data_norm = data.T
        data_norm -= data_norm.min(axis=0)
        data_norm /= data_norm.max(axis=0)

        for i, mark in enumerate([self.point_start, self.point_cut, point_end]):
            ax[0, i + 1].plot(data_norm.T[self._get_index(mark)], freqs)
            ax[0, i + 1].set_ylim(freqs.max(), freqs.min())
            ax[0, i + 1].set_xlabel(labels[i])
            ax[0, i + 1].tick_params(axis='y', left=False, labelleft=False)
            