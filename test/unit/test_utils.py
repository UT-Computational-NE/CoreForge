import pytest

from coreforge.utils import remove_none_2D, offset_to_ring

def test_remove_none_2D():
    input_map = [[None, None, None, None],
                 [None, 'A', None, 'B'  ],
                 [None, None, None, None],
                 [None, 'C', None, 'D'  ]]

    expected = [['A', 'B'],
                ['C', 'D']]

    assert remove_none_2D(input_map) == expected


def test_offset_to_ring():

    ring_map = [[1,2,3,4,5,6,7,8,9,10,11,12],
                [13,14,15,16,17,18],
                [19]]

    cartesian_map = [[     9, 10, 11,     ],

                     [   8, 17, 18, 12,   ],

                     [ 7, 16, 19, 13,  1, ],

                     [   6, 15, 14,  2,   ],

                     [     5,  4,  3,     ]]

    assert offset_to_ring(layout = cartesian_map, orientation = "x") == ring_map

    cartesian_map = [[         1,         ],
                     [    12,      2,     ],
                     [11,     13,      3, ],
                     [    18,     14,     ],
                     [10,     19,      4, ],
                     [    17,     15,     ],
                     [ 9,     16,      5, ],
                     [     8,      6,     ],
                     [         7,         ]]

    assert offset_to_ring(layout = cartesian_map, orientation = "y") == ring_map
