import openmc

from coreforge.materials.material import Material, ROOM_TEMPERATURE


class Pb(Material):
    """Factory for creating natural lead materials.

    Parameters
    ----------
    name : str
        The name for the material.
    temperature : float
        The temperature of the material [K].
    density : float
        The density of the material [g/cm3].

    References
    ----------
    .. [1] C. C. Hudson, "Development of a Radioisotope Production Facility
           Using a Cryogenic Cooling System", Ph.D. dissertation, The
           University of Texas at Austin, December 2025. Composition from
           page 270 and density from page 187.
    """

    def __init__(self,
                 name: str = "Pb",
                 temperature: float = ROOM_TEMPERATURE,
                 density: float = 11.35):

        assert temperature >= 0.0, "Temperature must be positive in Kelvin."
        assert density > 0.0, f"density = {density}"

        openmc_material = openmc.Material(name=name)
        openmc_material.temperature = temperature
        openmc_material.set_density("g/cm3", density)
        openmc_material.add_element("Pb", 1.0, percent_type="ao")

        super().__init__(openmc_material)
