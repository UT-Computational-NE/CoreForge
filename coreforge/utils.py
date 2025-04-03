from typing import List, TypeVar

import numpy as np

T = TypeVar('T')
def remove_none_2D(map_2D: List[List[T]]) -> List[List[T]]:
    """ Helper function for pruning those rows and columns of the 2D Map that are all None values

    Parameters
    ----------
    map_2D : List[List[T]]
        The 2D map which is to be pruned

    Returns
    ------
    List[List[T]]
        The resulting pruned 2D map
    """
    array = np.array(map_2D, dtype=object)
    return array[~np.all(np.equal(array, None), axis=1)][:, ~np.all(np.equal(array, None), axis=0)].tolist()
