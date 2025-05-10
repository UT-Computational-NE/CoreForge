from abc import ABC
from dataclasses import dataclass


@dataclass
class BuilderSpecs(ABC):
    """ Abstract Class for Building specifications for Geometry Elements
    """
