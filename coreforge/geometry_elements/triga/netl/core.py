from typing import TypeAlias

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.triga import FuelElement, GraphiteElement
from coreforge.geometry_elements.triga.netl import (
    FuelFollowerControlRod,
    TransientRod,
    CentralThimble,
    SourceHolder,
)

class Core(GeometryElement):
    """TRIGA NETL Core definition.

    Parameters
    ----------
    pitch : float
        The hexagonal lattice pitch of the core [cm].
    """

    # Type aliases for core elements
    Loadable: TypeAlias = FuelElement | GraphiteElement | SourceHolder
    Fixture: TypeAlias = CentralThimble | TransientRod | FuelFollowerControlRod
    Element: TypeAlias = FuelElement | GraphiteElement | SourceHolder | CentralThimble | TransientRod | FuelFollowerControlRod

    @property
    def pitch(self) -> float:
        return self._pitch

    def __init__(self, pitch: float):
        self._pitch = pitch