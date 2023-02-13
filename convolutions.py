import scipy
import numpy as np
from numba import jit


def get_gaussian_curve(length: int, sigma=1) -> np.ndarray[np.float32]:
    """
    Returns array with values of gaussian curve, with mean in middle of array.

    :param length: Length of array.
    :param sigma: Standard deviation of distribution.
    :return: Array with values of gaussian curve.
    """

    x = np.arange(-length / 2 + 0.5, length / 2 + 1)
    y = scipy.stats.norm.pdf(x, scale=sigma)
    return y / np.max(y)


def gen_convolve(x: np.ndarray, y: np.ndarray, op, zipper) -> np.ndarray:
    """
    Generalized convolution operation.
    :param x: First vector.
    :param y: Second vector.
    :param op: Function of two elements of each vector.
    :param zipper: Function combining results in single position.
    :return: Convoluted vector.
    """

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
    """
    Performs convolution of two vectors but with addition replaced by maximum operation.
    """

    x_size = x.shape[0]
    y_size = y.shape[0]
    res = np.zeros(x_size)
    for i in range(y_size // 2, x_size + y_size // 2):
        offset = max(0, i - x_size + 1)
        x_pos = i - offset - 1
        y_pos = offset + 1
        tmp = x[x_pos + 1] * y[y_pos - 1]
        while x_pos >= 0 and y_pos < y_size:
            tmp = max(tmp, x[x_pos] * y[y_pos])
            x_pos -= 1
            y_pos += 1
        res[i - y_size // 2] = tmp
    return res
