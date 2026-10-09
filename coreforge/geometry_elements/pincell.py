from __future__ import annotations
from copy import deepcopy
from typing import List, Any, Generic, Sequence, TypeVar
from math import isclose

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.shapes import Shape_2D
from coreforge.materials import Material, unique_materials
from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.infinite_medium import InfiniteMedium
from coreforge.geometry_elements.overlay import register_overlay

TPinCell = TypeVar("TPinCell", bound="PinCell")

class PinCell(GeometryElement):
    """ A class for the reactor concentric "pincells"

    In traditional LWRs, pincells are simply concentric cylinders. However,
    this pincell class pertains to any concentric shapes that are of such
    dimensions such that the outer radius of a inner shape does not exceeed
    the inner radius of the next outer shape.

    Attributes
    ----------
    zones : List[Zone]
        The collection of zones that define the pincell, listed in order of
        the inner-most zone to the outer-most zone.  Each zone's outer-radius
        may not exceed the next zone's inner-radius.
    x0 : float
        The x-coordinate of the origin of the "pin" within the pincell
    y0 : float
        The y-coordinate of the origin of the "pin" within the pincell
    outer_material : Material
        The material that radially surrounds the concentric shapes
    """

    class Zone():
        """ A shape-material pair used for representing the different "zones" of a pincell

        Attributes
        ----------
        name : str
            A name for the zone
        shape : Shape_2D
            The shape of this pincell zone
        material : Material
            The material which fills this pincell zone
        rotation : float
            The rotation of the shape about its origin (degrees)
        """

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, name: str) -> None:
            self._name = name

        @property
        def shape(self) -> Shape_2D:
            return self._shape

        @shape.setter
        def shape(self, shape: Shape_2D) -> None:
            self._shape = shape

        @property
        def material(self) -> Material:
            return self._material

        @material.setter
        def material(self, material: Material) -> None:
            self._material = material

        @property
        def rotation(self) -> float:
            return self._rotation

        @rotation.setter
        def rotation(self, rotation: float) -> None:
            self._rotation = rotation

        def __init__(self, shape: Shape_2D, material: Material, name: str = 'zone', rotation: float=0.):
            self.name     = name
            self.shape    = shape
            self.material = material
            self.rotation = rotation

        def __eq__(self, other: Any) -> bool:
            if self is other:
                return True
            return (isinstance(other, PinCell.Zone) and
                    self.shape == other.shape       and
                    self.material == other.material and
                    isclose(self.rotation, other.rotation, rel_tol=TOL)
                   )

        def __hash__(self) -> int:
            return hash((self.shape,
                         self.material,
                         relative_round(self.rotation, TOL)))


    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @outer_material.setter
    def outer_material(self, outer_material: Material) -> None:
        self._outer_material = outer_material

    @property
    def zones(self) -> List[Zone]:
        return self._zones

    @zones.setter
    def zones(self, zones: List[Zone]) -> None:
        self._zones = None
        self._set_zones(zones=zones)

    def _set_zones(self, zones: List[Zone]) -> None:
        """ A zone setter method which captures the basic assertion logic

        This is being created to allow for child classes to wrap additional assertion logic
        around the base assertion logic

        Parameters
        ----------
        zones : List[Zone]
            The collection of zones to assign to the pincell
        """
        assert len(zones) > 0, f"len(zones) = {len(zones)}"
        assert all(zones[i-1].shape.outer_radius <= zones[i].shape.inner_radius
                   for i in range(1,len(zones))), \
            "Each zone's outer radius must not exceed the next zone's inner radius."
        self._zones = zones

    @property
    def x0(self) -> float:
        return self._x0

    @x0.setter
    def x0(self, x0: float) -> None:
        self._x0 = x0

    @property
    def y0(self) -> float:
        return self._y0

    @y0.setter
    def y0(self, y0: float) -> None:
        self._y0 = y0

    def __init__(self, zones: List[Zone], outer_material: Material,
                name: str = 'pincell', x0: float = 0.0, y0: float = 0.0):

        super().__init__(name)
        self.zones          = zones
        self.outer_material = outer_material
        self.x0             = x0
        self.y0             = y0

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return (isinstance(other, PinCell)                            and
                self.outer_material == other.outer_material           and
                isclose(self.x0, other.x0, rel_tol=TOL)               and
                isclose(self.y0, other.y0, rel_tol=TOL)               and
                len(self.zones) == len(other.zones)                   and
                all(self.zones[i] == other.zones[i] for i in range(len(self.zones)))
               )

    def __hash__(self) -> int:
        return hash((self.outer_material,
                     relative_round(self.x0, TOL),
                     relative_round(self.y0, TOL),
                     tuple(self.zones)))

    def get_materials(self) -> List[Material]:
        materials = [zone.material for zone in self.zones]
        materials.append(self.outer_material)
        return unique_materials(materials)

    def translate(self: TPinCell, dx: float = 0.0, dy: float = 0.0) -> TPinCell:
        """Return a radially translated copy of this pin cell.

        Offsets are added to the existing center without modifying the original
        pin cell. The concrete type is retained, and zones, shapes, and
        materials are deep-copied.

        Parameters
        ----------
        dx : float
            Translation along the x-axis [cm].
        dy : float
            Translation along the y-axis [cm].

        Returns
        -------
        PinCell
            A deep copy of this pin cell with the translated center.
        """
        translated = deepcopy(self)
        translated.x0 += dx
        translated.y0 += dy
        return translated


class PinCells(GeometryElement, Generic[TPinCell]):
    """An ordered collection of layered pin cells.

    Only finite pin regions are layered. Where they overlap, later pin cells
    cover earlier pin cells. The common outer material fills the space outside
    all finite pin regions.

    Parameters
    ----------
    pincells : List[PinCell]
        Nonempty list of pin cells in layer order. All pin cells must share
        the same outer material.
    name : str
        A name for the geometry element.

    Attributes
    ----------
    pincells : List[PinCell]
        The pin cells, ordered from earliest to latest layer.
    outer_material : Material
        The common background material of the pin cells.
    """

    @property
    def pincells(self) -> List[TPinCell]:
        return self._pincells

    @pincells.setter
    def pincells(self, pincells: List[TPinCell]) -> None:
        self._set_pincells(pincells)

    def _set_pincells(self, pincells: List[TPinCell]) -> None:
        assert len(pincells) > 0, "PinCells must contain at least one pin cell."
        assert all(isinstance(pincell, PinCell) for pincell in pincells), \
            "All layers must be PinCell objects."
        assert all(pincell.outer_material == pincells[0].outer_material for pincell in pincells), \
            "PinCells must share a common outer material."
        self._pincells = list(pincells)

    @property
    def outer_material(self) -> Material:
        return self.pincells[0].outer_material

    def __init__(self, pincells: List[TPinCell], name: str = 'pincells'):
        super().__init__(name)
        self.pincells = pincells

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        return isinstance(other, PinCells) and self.pincells == other.pincells

    def __hash__(self) -> int:
        return hash(tuple(self.pincells))

    def get_materials(self) -> List[Material]:
        """Return the unique materials referenced by the pin-cell layers.

        Returns
        -------
        List[Material]
            Unique layer materials, including the common outer material.
        """
        return unique_materials([material for pincell in self.pincells
                                 for material in pincell.get_materials()])

    def translate(self, dx: Sequence[float], dy: Sequence[float]) -> PinCells[TPinCell]:
        """Return a copy with each pin-cell layer translated independently.

        Offsets are added to the existing pin-cell centers without modifying
        this collection or its pin cells. Each pin cell, including its zones,
        shapes, and materials, is deep-copied.

        Parameters
        ----------
        dx : Sequence[float]
            Per-pin translations along the x-axis [cm], in layer order.
            Must contain one offset for every pin cell.
        dy : Sequence[float]
            Per-pin translations along the y-axis [cm], in layer order.
            Must contain one offset for every pin cell.

        Returns
        -------
        PinCells
            A new collection containing the translated pin-cell copies.
        """
        assert len(dx) == len(dy) == len(self.pincells), \
            "Translation offsets must contain one dx and dy for each pin cell."
        return type(self)(
            pincells=[pincell.translate(dx=pin_dx, dy=pin_dy)
                      for pincell, pin_dx, pin_dy in zip(self.pincells, dx, dy)],
            name=self.name,
        )


@register_overlay(PinCell, PinCell)
@register_overlay(PinCell, PinCells)
@register_overlay(PinCells, PinCell)
@register_overlay(PinCells, PinCells)
def _overlay_pincells(lower: PinCell | PinCells,
                      upper: PinCell | PinCells) -> PinCells:
    """Combine pin-cell layers with upper layers following lower layers.

    Parameters
    ----------
    lower : PinCell | PinCells
        Lower-priority layers, deep-copied by the overlay dispatcher.
    upper : PinCell | PinCells
        Higher-priority layers, deep-copied by the overlay dispatcher.

    Returns
    -------
    PinCells
        Flattened generic collection in overlay order.

    Raises
    ------
    AssertionError
        If the pin cells do not share a common outer material.
    """
    lower_pins = lower.pincells if isinstance(lower, PinCells) else [lower]
    upper_pins = upper.pincells if isinstance(upper, PinCells) else [upper]
    return PinCells(pincells=lower_pins + upper_pins, name=lower.name)


@register_overlay(InfiniteMedium, PinCell)
@register_overlay(InfiniteMedium, PinCells)
def _overlay_pincells_on_infinite_medium(lower: InfiniteMedium,
                                        upper: PinCell | PinCells) -> PinCell | PinCells:
    """Overlay pin geometry onto a matching infinite-medium background.

    Parameters
    ----------
    lower : InfiniteMedium
        Lower-priority medium, deep-copied by the overlay dispatcher.
    upper : PinCell | PinCells
        Higher-priority pin geometry, deep-copied by the overlay dispatcher.

    Returns
    -------
    PinCell | PinCells
        The upper pin geometry with its concrete type, finite regions, and
        existing outer materials preserved.

    Raises
    ------
    AssertionError
        If any pin cell's outer material differs from the medium's material.
    """
    pincells = upper.pincells if isinstance(upper, PinCells) else [upper]
    assert all(pin.outer_material == lower.material for pin in pincells), \
        "Pin-cell outer materials must match the underlying InfiniteMedium material."
    return upper
