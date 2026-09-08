from coreforge.serialization import register_serializable as _register

from .geometry_element import GeometryElement
from .infinite_medium import InfiniteMedium
from .pincell import PinCell
from .cylindrical_pincell import CylindricalPinCell
from .block import Block
from .stack import Stack
from .cylindrical_stack import CylindricalStack
from .cone import OneSidedCone
from .rect_lattice import RectLattice
from .hex_lattice import HexLattice

__all__ = [
    "GeometryElement",
    "InfiniteMedium",
    "PinCell",
    "CylindricalPinCell",
    "Block",
    "Stack",
    "CylindricalStack",
    "OneSidedCone",
    "RectLattice",
    "HexLattice"
]


# Registered in one place so the set of serializable elements is visible.
# PinCell.Zone is nested and registered by its qualified simple name.
for _element_cls in (InfiniteMedium, PinCell, CylindricalPinCell, HexLattice):
    _register(_element_cls)
_register(PinCell.Zone)
