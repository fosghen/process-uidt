from pathlib import Path
from datetime import datetime

import numpy as np

class PeakSaver:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

        # Возможно, лучше поставить время окончания эсперимента
        self.fname = (datetime.now().strftime("%Y_%m_%d__%H_%M_%S.%f") + ".csv")
        self.peaks: list[np.ndarray] = []
        self.peaks_names: list[str] = []

    def add_peak(self, peaks: np.ndarray, peak_name: str) -> None:
        self.peaks.append(peaks)
        self.peaks_names.append(peak_name)

    def _find_max_len_peak(self) -> int:
        return max(peak.size for peak in self.peaks) + 1

    def save_file(self):
        data = np.zeros((self._find_max_len_peak(), len(self.peaks)), dtype=object)
        data[0] = self.peaks_names

        for i, peak in enumerate(self.peaks):
            data[1: peak.size + 1, i] = peak
            
        self.output_dir.mkdir(exist_ok=True)
        np.savetxt(self.output_dir / self.fname, data, fmt= "%s", delimiter = ";")
