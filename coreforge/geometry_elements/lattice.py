from abc import abstractmethod
from typing import List, Tuple

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.infinite_medium import InfiniteMedium
from coreforge.geometry_elements.overlay import register_overlay
from coreforge.geometry_elements.pincell import PinCell
from coreforge.geometry_elements.pincell_stack import PinCellStack
from coreforge.materials import Material, unique_materials
from coreforge.shapes import Circle, Shape_2D

class Lattice(GeometryElement):
    """ An abstract class for 2D Lattice of geometry elements

    Attributes
    ----------
    elements : List[List[GeometryElement]]
        The geometry elements which fill the lattice
    outer_material : Material
        The material which fills the region outside the lattice as well
        those cells of that lattice not specifically filled with a GeometryElement
    cell_centers : List[List[Tuple[float, float]]]
        Cell-center coordinates [cm] relative to the lattice origin, ordered
        to match ``elements``. Refreshed by the defining geometry setters.
    cell_shapes : List[List[Shape_2D]]
        Cell footprints centered at their local origins, ordered to match
        ``elements``. Refreshed by the defining geometry setters.
    """

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @outer_material.setter
    def outer_material(self, outer_material: Material) -> None:
        self._outer_material = outer_material

    @property
    def cell_centers(self) -> List[List[Tuple[float, float]]]:
        return self._cell_centers

    @property
    def cell_shapes(self) -> List[List[Shape_2D]]:
        return self._cell_shapes

    @property
    @abstractmethod
    def elements(self) -> List[List[GeometryElement]]:
        pass

    @elements.setter
    @abstractmethod
    def elements(self, elements: List[List[GeometryElement]]) -> None:
        pass

    @abstractmethod
    def _update_cell_geometry(self) -> None:
        """Refresh stored cell centers and shapes from the lattice geometry."""

    def __init__(self, name: str, outer_material: Material):
        self._cell_centers: List[List[Tuple[float, float]]] = []
        self._cell_shapes: List[List[Shape_2D]] = []
        self.outer_material = outer_material
        super().__init__(name)

    def get_materials(self) -> List[Material]:
        materials = [self.outer_material]
        for row in self.elements:
            for element in row:
                if element is not None:
                    materials.extend(element.get_materials())
        return unique_materials(materials)


@register_overlay(Lattice, PinCell)
@register_overlay(Lattice, PinCellStack)
def _overlay_pincell(lower: Lattice, upper: PinCell | PinCellStack) -> Lattice:
    """Distribute a pin or pin-cell stack across intersected lattice cells.

    Parameters
    ----------
    lower : Lattice
        Lattice to overlay.
    upper : PinCell | PinCellStack
        PinCell / PincellStack to overlay the Lattice with.
        Its radial center is expressed relative to the lattice origin.

    Returns
    -------
    Lattice
        The copied lattice with overlays translated into affected cells' local
        coordinates. The footprint's outcircle determines which cells get overlain.
    """

    footprint = upper.footprint if isinstance(upper, PinCellStack) else upper.zones[-1].shape
    outcircle = Circle(r=footprint.outer_radius)
    for row, centers, shapes in zip(lower.elements, lower.cell_centers, lower.cell_shapes):
        for i, (element, center, shape) in enumerate(zip(row, centers, shapes)):
            intersects = shape.intersects(outcircle, self_center=center,
                                          other_center=(upper.x0, upper.y0))
            if intersects is NotImplemented:
                raise NotImplementedError(
                    f"No Circle intersection rule for {type(shape).__name__}."
                )
            if intersects:
                background = element if element is not None else InfiniteMedium(lower.outer_material)
                row[i] = background.overlay(upper.translate(dx=-center[0], dy=-center[1]))
    return lower
