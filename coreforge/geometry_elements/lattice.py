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

    def cells_intersecting(self,
                           shape: Shape_2D,
                           center: Tuple[float, float] = (0.0, 0.0)) -> List[Tuple[int, int]]:
        """Find lattice cell indices whose footprints intersect a shape.

        Parameters
        ----------
        shape : Shape_2D
            Shape to intersect with the cell footprints.
        center : Tuple[float, float], optional
            Shape-center coordinates [cm] relative to the lattice origin.

        Returns
        -------
        List[Tuple[int, int]]
            ``(outer_index, inner_index)`` pairs indexing ``elements``, in
            their stored order. Only indices are returned, not cell elements.
            Portions of the shape outside the lattice are not represented.

        Raises
        ------
        NotImplementedError
            If a cell shape has no intersection rule for the supplied shape.
        """
        indices = []
        for i, (centers, shapes) in enumerate(zip(self.cell_centers, self.cell_shapes)):
            for j, (cell_center, cell_shape) in enumerate(zip(centers, shapes)):
                if cell_shape.intersects(shape, self_center=cell_center, other_center=center):
                    indices.append((i, j))
        return indices

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
    for i, j in lower.cells_intersecting(outcircle, center=(upper.x0, upper.y0)):
        element = lower.elements[i][j]
        center = lower.cell_centers[i][j]
        background = element if element is not None else InfiniteMedium(lower.outer_material)
        lower.elements[i][j] = background.overlay(upper.translate(dx=-center[0], dy=-center[1]))
    return lower
