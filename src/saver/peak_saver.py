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
        self.length: np.ndarray 

    def add_peak(self, peaks: np.ndarray, peak_name: str, length: np.ndarray) -> None:
        self.peaks.append(peaks)
        self.peaks_names.append(peak_name)
        self.length = length

    def _find_max_len_peak(self) -> int:
        return max(peak.size for peak in self.peaks) + 1

    def save_file(self):
        data = np.zeros((self._find_max_len_peak(), len(self.peaks) + 1), dtype=object)
        data[0, 1:] = self.peaks_names
        data[0, 0] = "Длина"

        
        data[1: self.length.size + 1, 0] = self.length

        for i, peak in enumerate(self.peaks):
            data[1: peak.size + 1, i + 1] = peak
            
        self.output_dir.mkdir(exist_ok=True)
        np.savetxt(self.output_dir / self.fname, data, fmt= "%s", delimiter = ";")
