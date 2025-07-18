from typing import Callable
from joblib import Parallel, delayed
import numpy as np
from scipy.signal import medfilt, find_peaks
from scipy.ndimage import convolve1d
from scipy.optimize import curve_fit

class PeakFinder:
    def __init__(self, data_type: str, ) -> None:
        self.data_type = data_type

    @staticmethod
    def _laplace_func(x: np.ndarray, mu: float, b: float, a: float) -> np.ndarray:
        return a * np.exp(-abs(x - mu) / b)
    
    @staticmethod
    def _get_peaks(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        image = data.T
        kernel = PeakFinder._laplace_func(np.arange(10), 5, 5, 1)
        # "Сглаживаем" сигнал с помощью функции Лапласа
        result = convolve1d(image, kernel, axis=0, mode='constant')
        
        # Подготавливаем массивы, чтобы получить пики
        low_peaks = np.zeros(result.shape[1], dtype = int)
        hi_peaks = np.zeros((result.shape[1], 2), dtype = int)
        for i in range(result.shape[1]):
            # Ищем положительные пики, расстояние между которыми больше 15 отсчётов
            peaks_hi = find_peaks(result[:, i], distance=15)[0]
            # Выбираем два наиболее амлитудных
            hi_peak = peaks_hi[np.argsort(result[peaks_hi, i])[-2:]]
            # Берём сигнал от левого пика до правого и в нём находим минимум
            try:
                low_peak = np.argmin(result[min(hi_peak): max(hi_peak), i]) + min(hi_peak)
            except ValueError:
                low_peak = int(data.shape[0] // 2)
            low_peaks[i] = low_peak
            hi_peaks[i] = hi_peak
        return (low_peaks, hi_peaks)

    @staticmethod
    def _process_row_analyze(freq: np.ndarray, data_row: np.ndarray, *args) -> float:
        try:
            # ищем точку в которой пик похож на тот, что мы ожидаем
            index_max = np.argmax(np.correlate(data_row, PeakFinder._laplace_func(np.arange(10), 5, 5, 1), mode='full')) - 5
            # сглаживаем 
            y_smooth = medfilt(data_row, kernel_size=5)
            params, _ = curve_fit(PeakFinder._laplace_func,
                                  freq,
                                  y_smooth,
                                  p0=[freq[index_max], 10, 1],
                                  maxfev=1000,
                                  bounds=([freq[0],     1,  0.5],
                                          [freq[-1],    100, 1.5]),
                                          )
            return params[0]
        except Exception:
            return freq[0]

    @staticmethod
    def _process_row_reflectometer(freq: np.ndarray, data_row: np.ndarray,
                                   i: int, lo_peaks: np.ndarray, hi_peaks: np.ndarray) -> float:
        try:
            # аппроксимация левого пика
            params0, _ = curve_fit(PeakFinder._laplace_func, 
                                freq[:lo_peaks[i]], 
                                data_row[:lo_peaks[i]], 
                                p0=[freq[min(hi_peaks[i])], 10, 1],
                                maxfev=100,
                                bounds=([freq[0],           1, 0.5],
                                        [freq[lo_peaks[i]], 100, 1.5]))
            # аппроксимация правого пика    
            params1, _ = curve_fit(PeakFinder._laplace_func,
                                freq[lo_peaks[i]:],
                                data_row[lo_peaks[i]:],
                                p0=[freq[max(hi_peaks[i])], 10, 1],
                                maxfev=100,
                                bounds=((freq[lo_peaks[i]], 1, 0.5),
                                        (freq[-1],          100, 1.5)))
            return (params0[0] + params1[0]) / 2
        except Exception:
            #Если что-то идёт не так, то берём среднее значение
            return float(freq[hi_peaks[i][0]] + freq[hi_peaks[i][1]]) / 2

    @staticmethod
    def _find_peak_parallel(freq: np.ndarray, process_row: Callable, data: np.ndarray, *args) -> np.ndarray:
        return np.array(Parallel(n_jobs=-1)(delayed(process_row)(freq, data[i], i, *args) for i in range(data.shape[0])))

    def find_peak(self, freq: np.ndarray, data: np.ndarray) -> np.ndarray:
        finder = PeakFinder._process_row_analyze
        args = ()
        if self.data_type == "refl":
            finder = PeakFinder._process_row_reflectometer
            lo_peaks, hi_peaks = PeakFinder._get_peaks(data)
            args = (lo_peaks, hi_peaks)
        return PeakFinder._find_peak_parallel(freq, finder, data, *args)
    
    def get_approx_laplace(self, freq: np.ndarray, data: np.ndarray) -> np.ndarray:
        """Функция, выдающая аппроксимирующие функции Лапласса для набора данных."""
        approx_laplace = np.zeros((3, freq.size))
        
        for i, data_row in enumerate(data):
            if self.data_type == "refl":
                # находим предположительные пики 
                lo_peaks, hi_peaks = PeakFinder._get_peaks(data)
                # аппроксимируем левый пик
                params0, _ = curve_fit(PeakFinder._laplace_func, 
                                    freq[:lo_peaks[i]], 
                                    data_row[:lo_peaks[i]], 
                                    p0=[freq[min(hi_peaks[i])], 10, 1],
                                    maxfev=100,
                                    bounds=([freq[0],           1, 0.5],
                                            [freq[lo_peaks[i]], 100, 1.5]))
                approx_laplace[i, :lo_peaks[i]] = PeakFinder._laplace_func(freq[:lo_peaks[i]], *params0)
                # аппроксимируем правый пик
                params1, _ = curve_fit(PeakFinder._laplace_func,
                                    freq[lo_peaks[i]:],
                                    data_row[lo_peaks[i]:],
                                    p0=[freq[max(hi_peaks[i])], 10, 1],
                                    maxfev=100,
                                    bounds=((freq[lo_peaks[i]], 1, 0.5),
                                            (freq[-1],         100, 1.5)))
                approx_laplace[i, lo_peaks[i]:] = PeakFinder._laplace_func(freq[lo_peaks[i]:], *params1)
                
            else:
                index_max = np.argmax(np.correlate(data_row, PeakFinder._laplace_func(np.arange(10), 5, 5, 1), mode='full')) - 5
                y_smooth = medfilt(data_row, kernel_size=5)
                params, _ = curve_fit(PeakFinder._laplace_func,
                                    freq,
                                    y_smooth,
                                    p0=[freq[index_max], 10, 1],
                                    maxfev=1000,
                                    bounds=([freq[0],     1, 0.5],
                                            [freq[-1],    100, 1.5]),
                                            )
                approx_laplace[i] = PeakFinder._laplace_func(freq, *params)

        return approx_laplace
    
