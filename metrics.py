from typing import List

import numpy as np

from vectorization import Vector
import scipy


def euclidean(vec_list: List[Vector], point: Vector) -> np.ndarray[np.float32]:
    return scipy.spatial.distance.cdist(np.array(vec_list), np.array([point]))