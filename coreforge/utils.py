from typing import List, TypeVar

T = TypeVar('T')
def cartesian_to_ring(layout: List[List[T]], orientation : str='y') -> List[List[T]]:
    """ Function for converting cartesian layouts to hexagonal rings

    Convert a Cartesian representation of a hexagonal lattice into a ring-based representation.

    This helper function is useful for converting a visually intuitive Cartesian layout
    of a 2D hexagonal lattice into the ring-based representation used by HexLattice.
    For the resulting ring-based respresentation with the first dimension corresponding to
    rings (outer-to-inner) and the second dimension corresponding to the individual elements
    of each ring, ordered from the “top point” for y-oriented lattices, or the “east point”
    for x-oriented lattices and proceed in a clockwise fashion.

    Parameters
    ----------
    layout : List[List[T]]
        The Cartesian layout of the hexagonal lattice.
    orientation : str, default='y'
        Specifies the orientation of the hexagon:
        - 'x', 'X': Two sides are parallel with the x-axis.
        - 'y', 'Y': Two sides are parallel with the y-axis.

    Returns
    -------
    List[List[T]]
        The ring-based representation of the hexagonal lattice.

    Examples
    --------
    Y-oriented:
               [[         T,         ],
                [     T,      T,     ],
                [ T,      T,      T, ],
                [     T,      T,     ],
                [ T,      T,      T, ],
                [     T,      T,     ],
                [ T,      T,      T, ],
                [     T,      T,     ],
                [         T,         ]]

    X-oriented:
               [[     T,  T,  T,     ],

                [   T,  T,  T,  T,   ],

                [ T,  T,  T,  T,  T, ],

                [   T,  T,  T,  T,   ],

                [     T,  T,  T,     ]]

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
