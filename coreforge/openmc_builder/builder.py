from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import openmc

from coreforge.geometry_elements.geometry_element import GeometryElement


T = TypeVar("T", bound=GeometryElement)


class Builder(ABC, Generic[T]):
    """Abstract base class for OpenMC geometry builders."""

    @abstractmethod
    def build(self, element: T) -> openmc.Universe:
        """ Method for building an OpenMC geometry of a GeometryElement

		Parameters
		----------
		element: GeometryElement
			The geometry element to be built

		Returns
		-------
		openmc.Universe
			A new OpenMC geometry based on this geometry element
		"""
        raise NotImplementedError
