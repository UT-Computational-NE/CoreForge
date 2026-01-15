from abc import ABC
from dataclasses import dataclass
from typing import Dict, TypeAlias

import mpactpy

from coreforge.materials import Material
from coreforge import materials
from coreforge.materials import msre as materials_msre

MaterialSpecs: TypeAlias = Dict[Material, mpactpy.Material.MPACTSpecs]

DEFAULT_MPACT_SPECS: Dict[type[Material], mpactpy.Material.MPACTSpecs] = {
    materials.Air: mpactpy.Material.MPACTSpecs({}, False, False, False, False),
    materials.B4C: mpactpy.Material.MPACTSpecs({}, False, False, False, False),
    materials.Graphite: mpactpy.Material.MPACTSpecs({'C': "C_in_Graphite"}, False, False, False, False),
    materials.Helium: mpactpy.Material.MPACTSpecs({}, False, False, False, False),
    materials.Inconel: mpactpy.Material.MPACTSpecs({}, False, False, True, False),
    materials.INOR8: mpactpy.Material.MPACTSpecs({}, False, False, True, False),
    materials.SS304: mpactpy.Material.MPACTSpecs({}, False, False, True, False),
    materials.SS316H: mpactpy.Material.MPACTSpecs({}, False, False, True, False),
    materials.Water: mpactpy.Material.MPACTSpecs({'H': "H1"}, True, False, False, False),
    materials.UZrH: mpactpy.Material.MPACTSpecs({'Zr': "Zr_in_ZrH2", 'H': "H1_in_ZrH"}, False, True, True, True),
    materials.Zr: mpactpy.Material.MPACTSpecs({}, False, False, True, False),
    materials.Mo: mpactpy.Material.MPACTSpecs({'Mo92': "Mo", 'Mo94': "Mo", 'Mo95': "Mo", 'Mo96': "Mo",
                                               'Mo97': "Mo", 'Mo98': "Mo", 'Mo100': "Mo"},
                                               False, False, True, False),
    materials.Al6061T6: mpactpy.Material.MPACTSpecs({'Mg24': "Mg", 'Mg25': "Mg", 'Mg26': "Mg",
                                                     'Si28': "Si", 'Si29': "Si", 'Si30': "Si"},
                                                     False, False, True, False),
    materials_msre.ControlRodPoison: mpactpy.Material.MPACTSpecs({}, False, False, True, False),
    materials_msre.Insulation: mpactpy.Material.MPACTSpecs({}, False, False, False, False),
    materials_msre.Salt: mpactpy.Material.MPACTSpecs({}, True, True, True, True),
    materials_msre.ThimbleGas: mpactpy.Material.MPACTSpecs({}, False, False, False, False)
}


@dataclass
class BuilderSpecs(ABC):
    """ Abstract Class for Building specifications for Geometry Elements
    """
