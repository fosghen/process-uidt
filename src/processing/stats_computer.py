import numpy as np

from pathlib import Path

class StatsComputer:
    def __init__(self, count_points: int) -> None:
        self.count_points = count_points

    def compute_std(self, peaks: np.ndarray) -> np.ndarray:
        if (self.count_points % 2) == 0: 
            self.count_points += 1
        pad = self.count_points // 2
        x_pad = np.pad(peaks, pad_width=pad, mode='reflect')

        std = np.zeros_like(peaks)
        for i in range(peaks.size):
            std[i] = np.std(x_pad[i: i + self.count_points])
        
        return std
