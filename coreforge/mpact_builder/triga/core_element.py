from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple, TypeVar

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.mpact_builder.builder import Builder
from coreforge.mpact_builder.stack import Stack
import coreforge.geometry_elements as geometry_elements

TCoreElement = TypeVar("TCoreElement", bound=GeometryElement)


class CoreElement(Builder[TCoreElement], ABC):
    """Base builder for TRIGA core elements.
    """

    @abstractmethod
    def build_stack_and_specs(
        self,
        element: TCoreElement,
    ) -> Tuple[geometry_elements.Stack, Stack.Specs]:
        """Build the element stack and corresponding stack specs.

        Parameters
        ----------
        element : GeometryElement
            The geometry element to be built into a stack.

        Returns
        -------
        Tuple[geometry_elements.Stack, Stack.Specs]
            The stack representation of the element and corresponding stack specs.
        """
        raise NotImplementedError
