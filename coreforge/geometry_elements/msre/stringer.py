from typing import Optional, Any
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.stack import Stack
from coreforge.geometry_elements.msre.block import Block



class Stringer(GeometryElement):
    """ A class for MSRE-like stringers

    Parameters
    ----------
    block : Block
        The block that represents the stringer's 2D radial footprint
    length : float
        The length of the stringer

    Attributes
    ----------
    block : Block
        The block that represents the stringer's 2D radial footprint
    length : float
        The length of the stringer
    """


    @property
    def block(self) -> Block:
        return self._block

    @property
    def length(self) -> float:
        return self._length


    def __init__(self, block: Block, length: float, name: str = 'stringer'):

        assert length > 0., f"length = {length}"

        self._block = block if block is not None else Block()
        self._length = length
        super().__init__(name)


    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, Stringer) and
                self.block == other.block   and
                isclose(self.length, other.length)
               )

    def __hash__(self) -> int:
        return hash((self.block,
                     relative_round(self.length, TOL)))


    def as_stack(self, bottom_pos: float = 0.0) -> Stack:
        """ A method for getting a copy of the Stringer as a Stack

        Parameters
        ----------
        bottom_pos : float
            The axial position of the bottom of the stack (cm)

        Returns
        -------
        Stack
            The Stringer as a Stack
        """

        return Stack(segments   = [Stack.Segment(self.block, self.length)],
                      name       = self.name,
                      bottom_pos = bottom_pos)