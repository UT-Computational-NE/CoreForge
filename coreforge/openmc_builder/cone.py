import openmc

from coreforge.openmc_builder.openmc_builder import register_builder
from coreforge import geometry_elements


@register_builder(geometry_elements.OneSidedCone)
class OneSidedCone:
	""" An OpenMC geometry builder class for OneSidedCone
	"""

	def __init__(self):
		pass

	def build(self, element: geometry_elements.OneSidedCone) -> openmc.Universe:
		""" Method for building an OpenMC geometry of a OneSidedCone

		Parameters
		----------
		element: OneSidedCone
			The geometry element to be built

		Returns
		-------
		openmc.Universe
			A new OpenMC geometry based on this geometry element
		"""

		cone_region = element.shape.make_region()
		cone_cell = openmc.Cell(name   = f"{element.name}_cone",
			                    fill   = element.fill_material.openmc_material,
			                    region = -cone_region)
		outer_cell = openmc.Cell(name   = f"{element.name}_outer",
			                     fill   = element.outer_material.openmc_material,
			                     region = +cone_region)

		universe = openmc.Universe(name=element.name)
		universe.add_cells([cone_cell, outer_cell])
		return universe
