import scipy
import numpy as np
from numba import jit


def get_gaussian_convolution(length: int, sigma=1) -> np.ndarray[np.float32]:
    x = np.arange(-length / 2 + 0.5, length / 2 + 1)
    y = scipy.stats.norm.pdf(x, scale=sigma)
    return y / np.max(y)


def gen_convolve(x: np.ndarray, y: np.ndarray, op, zipper) -> np.ndarray:
    n = x.shape[0] + y.shape[0] - 1
    res = np.zeros(n)
    for i in range(n):
        offset = max(0, i - x.shape[0] + 1)
        x_pos = i - offset - 1
        y_pos = offset + 1
        tmp = op(x[x_pos + 1], y[y_pos - 1])
        while x_pos >= 0 and y_pos < y.shape[0]:
            tmp = zipper(tmp, op(x[x_pos], y[y_pos]))
            x_pos -= 1
            y_pos += 1
        res[i] = tmp
    return res


@jit(nopython=True)
def maxvolve(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = x.shape[0] + y.shape[0] - 1
    res = np.zeros(x.shape[0])
    for i in range(y.shape[0] // 2, x.shape[0] + y.shape[0] // 2):
        offset = max(0, i - x.shape[0] + 1)
        x_pos = i - offset - 1
        y_pos = offset + 1
        tmp = x[x_pos + 1] * y[y_pos - 1]
        while x_pos >= 0 and y_pos < y.shape[0]:
            tmp = max(tmp, x[x_pos] * y[y_pos])
            x_pos -= 1
            y_pos += 1
        res[i] = tmp
    return res