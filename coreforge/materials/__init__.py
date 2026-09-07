from coreforge.serialization import register_serializable as _register

from .material import Material, unique_materials
from .graphite import Graphite
from .inconel import Inconel
from .air import Air
from .ss304 import SS304
from .ss316h import SS316H
from .water import Water
from .helium import Helium
from .inor8 import INOR8
from .b4c import B4C
from .uzrh import UZrH
from .zr import Zr
from .mo import Mo
from .al_6061_t6 import Al6061T6

__all__ = [
    "Material",
    "unique_materials",
    "Graphite",
    "Inconel",
    "Air",
    "SS304",
    "SS316H",
    "Water",
    "Helium",
    "INOR8",
    "B4C",
    "UZrH",
    "Zr",
    "Mo",
    "Al6061T6"
]


# Registered here rather than by decorating each class, so the set of
# serializable materials is visible in one place.
for _material_cls in (Graphite, Inconel, Air, SS304, SS316H, Water, Helium,
                      INOR8, B4C, UZrH, Zr, Mo, Al6061T6):
    _register(_material_cls)
