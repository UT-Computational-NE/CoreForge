from coreforge.serialization import register_serializable as _register

from .salt import Salt
from .thimble_gas import ThimbleGas
from .insulation import Insulation
from .control_rod_poison import ControlRodPoison

__all__ = [
    "Salt",
    "ThimbleGas",
    "Insulation",
    "ControlRodPoison",
]


# ControlRodPoison, Insulation and ThimbleGas all take (name, temperature,
# density) and are handled by Material's base implementation. Salt overrides it
# in its own module.
for _material_cls in (Salt, ThimbleGas, Insulation, ControlRodPoison):
    _register(_material_cls)
