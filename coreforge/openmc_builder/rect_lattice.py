import openmc

from coreforge.openmc_builder.openmc_builder import register_builder, build
from coreforge import geometry_elements

@register_builder(geometry_elements.RectLattice)
class RectLattice:
    """ An OpenMC geometry builder class for RectLattice
    """

    def __init__(self):
        pass

    def build(self, element: geometry_elements.RectLattice) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a RectLattice

        Parameters
        ----------
        element: RectLattice
            The geometry element to be built

        Returns
        -------
        openmc.Universe
            A new OpenMC geometry based on this geometry element
        """

        outer_universe = openmc.Universe(cells=[openmc.Cell(fill=element.outer_material.openmc_material)])

        universes = []
        for row in element.elements:
            universes.append([])
            for entry in row:
                universe = build(entry) if entry else outer_universe
                universes[-1].append(universe)

        lattice_universe            = openmc.RectLattice()
        lattice_universe.outer      = outer_universe
        lattice_universe.pitch      = element.pitch
        lattice_universe.lower_left = (-(element.pitch[0]*element.shape[1])/2.,
                                       -(element.pitch[1]*element.shape[0])/2.)
        lattice_universe.universes  = universes

        return lattice_universe
