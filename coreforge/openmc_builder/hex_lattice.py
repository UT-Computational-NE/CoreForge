import openmc

from coreforge.openmc_builder.registry import register_builder, build
from coreforge import geometry_elements

@register_builder(geometry_elements.HexLattice)
class HexLattice:
    """ An OpenMC geometry builder class for HexLattice
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.HexLattice) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a HexLattice

        Parameters
        ----------
        element: HexLattice
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        outer_universe = openmc.Universe(cells=[openmc.Cell(fill=element.outer_material.openmc_material)])

        universes = []
        for ring in element.elements:
            universes.append([])
            for entry in ring:
                universe = build(entry) if entry else outer_universe
                universes[-1].append(universe)

        lattice_universe             = openmc.HexLattice()
        lattice_universe.orientation = element.orientation
        lattice_universe.outer       = outer_universe
        lattice_universe.pitch       = [element.pitch]
        lattice_universe.center      = (0., 0.)
        lattice_universe.universes   = universes

        return lattice_universe
