import pytest

from coreforge.utils import remove_none_2D

def test_remove_none_2D():
    input_map = [[None, None, None, None],
                 [None, 'A', None, 'B'  ],
                 [None, None, None, None],
                 [None, 'C', None, 'D'  ]]

    expected = [['A', 'B'],
                ['C', 'D']]

    assert remove_none_2D(input_map) == expected