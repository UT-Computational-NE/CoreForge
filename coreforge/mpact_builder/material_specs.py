from dataclasses import dataclass
from typing import Dict, Optional

import mpactpy

from coreforge.materials import Material
from coreforge import materials
from coreforge.materials import msre as materials_msre

@dataclass
class MaterialSpecs:
    """ Building specifications for Materials

    Attributes
    ----------
    material_specs : Dict[Material, mpactpy.Material.MPACTSpecs]
        Specifications for how materials should be treated in MPACT
    """

    material_specs: Optional[Dict[Material, mpactpy.Material.MPACTSpecs]] = None

    def __post_init__(self):
        self.material_specs = self.material_specs if self.material_specs else {}



DEFAULT_MPACT_SPECS ={
    materials.Air: mpactpy.Material.MPACTSpecs([], False, False, False, False),
    materials.B4C: mpactpy.Material.MPACTSpecs([], False, False, False, False),
    materials.Graphite: mpactpy.Material.MPACTSpecs(['C'], False, False, False, False),
    materials.Helium: mpactpy.Material.MPACTSpecs([], False, False, False, False),
    materials.Inconel: mpactpy.Material.MPACTSpecs([], False, False, True, False),
    materials.INOR8: mpactpy.Material.MPACTSpecs([], False, False, True, False),
    materials.SS304: mpactpy.Material.MPACTSpecs([], False, False, True, False),
    materials.SS316H: mpactpy.Material.MPACTSpecs([], False, False, True, False),
    materials.Water: mpactpy.Material.MPACTSpecs(['H'], True, False, False, False),
    materials_msre.ControlRodPoison: mpactpy.Material.MPACTSpecs([], False, False, True, False),
    materials_msre.Insulation: mpactpy.Material.MPACTSpecs([], False, False, False, False),
    materials_msre.Salt: mpactpy.Material.MPACTSpecs([], True, True, True, True),
    materials_msre.ThimbleGas: mpactpy.Material.MPACTSpecs([], False, False, False, False)
}
