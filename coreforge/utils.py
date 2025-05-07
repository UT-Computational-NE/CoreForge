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

  
def offset_to_ring(layout: List[List[T]], orientation : str='y') -> List[List[T]]:
    """ Convert a visually structured offset-style hexagonal layout into a ring-based representation.

    This function transforms a 2D array representation of a hexagonal lattice (commonly used
    for human-readable input) into the ring-based format. The input layout mimics an offset
    coordinate system, where hex cells are arranged in staggered rows (for 'y' orientation)
    or columns (for 'x' orientation), similar to offset coordinate grids used in hex grid algorithms.

    The returned format organizes elements by concentric rings, from outermost to innermost.
    Within each ring, elements are ordered clockwise starting from the "top" (for 'y'-oriented
    lattices) or "east" (for 'x'-oriented lattices), matching the ordering expectations of the
    `HexLattice` class.

    This conversion is especially useful when users define lattice content via a 2D Python list
    that visually resembles the hex layout (e.g., using offset rows in ASCII-style diagrams).

    see: https://www.redblobgames.com/grids/hexagons/#coordinates-offset

    Parameters
    ----------
    layout : List[List[T]]
        A 2D list representing a hexagonal lattice in offset-style layout.
        Each sublist corresponds to a row (or column) depending on orientation.
    orientation : str, default='y'
        The orientation of the hexagons:
        - 'x' or 'X': flat-top hexagons, with horizontal columns offset
        - 'y' or 'Y': pointy-top hexagons, with vertical rows offset

    Returns
    -------
    List[List[T]]
        The ring-based representation of the hexagonal lattice.

    Examples
    --------
    Y-oriented
               [[         1,         ],
                [    12,      2,     ],
                [11,     13,      3, ],
                [    18,     14,     ],
                [10,     19,      4, ],
                [    17,     15,     ],
                [ 9,     16,      5, ],
                [     8,      6,     ],
                [         7,         ]]

    X-oriented
               [[     9, 10, 11,     ],

                [   8, 17, 18, 12,   ],

                [ 7, 16, 19, 13,  1, ],

                [   6, 15, 14,  2,   ],

                [     5,  4,  3,     ]]
    """

    def _convert_y_oriented(layout: List[List[T]]) -> List[List[T]]:
        assert len(layout) % 4 == 1, "Y-oriented layout must have (4*(num_rings-1) + 1) rows"

        num_rings = (len(layout) + 1) // 4 + 1
        rings     = []
        for i in range(num_rings-1):
            rings.append([])
            ring              = rings[-1]
            num_face_elements = num_rings-1-i
            row               = i*2                 # Starting Row
            col               = len(layout[row])//2 # Starting Column

            face_steps = [( 1,  1), # NE Face
                          ( 2,  0), #  E Face
                          ( 1, -1), # SE Face
                          (-1, -1), # SW Face
                          (-2,  0), #  W Face
                          (-1,  1)] # NW Face

            for drow, dcol in face_steps:
                for _ in range(num_face_elements):
                    ring.append(layout[row][col])
                    row += drow
                    col += (dcol if dcol > 0 and len(layout[row]) > len(layout[row-drow]) else
                            dcol if dcol < 0 and len(layout[row]) < len(layout[row-drow]) else 0)

        row            = (num_rings - 1) * 2
        col            = len(layout[row]) // 2
        center_element = layout[row][col]
        rings.append([center_element])

        return rings


    def _convert_x_oriented(layout: List[List[T]]) -> List[List[T]]:
        assert len(layout) % 2 == 1, "X-oriented layout must have (2*(num_rings-1) + 1) rows"

        num_rings = (len(layout) + 1) // 2
        rings     = []
        for i in range(num_rings-1):
            rings.append([])
            ring              = rings[-1]
            num_face_elements = num_rings-1-i
            row               = num_rings-1          # Starting Row
            col               = len(layout[row])-1-i # Starting Column

            face_steps = [( 1, -1), # SE Face
                          ( 0, -1), #  S Face
                          (-1,  0), # SW Face
                          (-1,  0), # NW Face
                          ( 0,  1), #  N Face
                          ( 1,  1)] # NE Face

            for drow, dcol in face_steps:
                for _ in range(num_face_elements):
                    ring.append(layout[row][col])
                    row += drow
                    col += dcol

        row            = num_rings - 1
        col            = len(layout[row]) - 1 - (num_rings-1)
        center_element = layout[row][col]
        rings.append([center_element])

        return rings

    assert orientation in ("x", "X", "y", "Y"), "Orientation must be 'x' or 'y'"
    orientation = 'x' if orientation == 'X' else orientation
    orientation = 'y' if orientation == 'Y' else orientation

    return _convert_y_oriented(layout) if orientation == "y" else _convert_x_oriented(layout)
