from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import Optional

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Air, Al6061T6, Material


class RSRCavity(GeometryElement):
    """TRIGA NETL rotary specimen rack (RSR) cavity.

    Parameters
    ----------
    outer_radius : float
        Outer radius of the RSR [cm].
    height : float
        Height of the RSR [cm].
    number_of_tubes : int
        Number of specimen tubes around the circumference.
    tube_to_center_distance : float
        Radial distance from rack center to tube centerlines [cm].
    tube_specs : RSRCavity.SpecimenTube
        Specimen tube specification.
    material : Material, optional
        Fill material inside the rack (defaults to ``Air``).
    name : str, optional
        Name for this RSR cavity.
    """

    @dataclass(frozen=True)
    class SpecimenTube:
        """Dataclass for specimen tubes.

        Attributes
        ----------
        outer_radius : float
            Outer radius of the specimen tube [cm].
        thickness : float
            Thickness of the specimen tube wall [cm].
        material : openmc.Material
            Cladding material of the specimen tube (defaults to ``Al6061T6``).
        """

        outer_radius: float
        thickness:    float
        material:     Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.outer_radius > 0.0, "Specimen Tube outer radius must be positive."
            assert self.thickness > 0.0, "Specimen Tube thickness must be positive."

        def __eq__(self, other: object) -> bool:
            if self is other:
                return True
            return (
                isinstance(other, RSRCavity.SpecimenTube)
                and isclose(self.outer_radius, other.outer_radius, rel_tol=TOL)
                and isclose(self.thickness, other.thickness, rel_tol=TOL)
                and self.material == other.material
            )

        def __hash__(self) -> int:
            return hash((
                relative_round(self.outer_radius, TOL),
                relative_round(self.thickness, TOL),
                self.material,
            ))

    @property
    def outer_radius(self) -> float:
        return self._outer_radius

    @property
    def height(self) -> float:
        return self._height

    @property
    def number_of_tubes(self) -> int:
        return self._number_of_tubes

    @property
    def tube_to_center_distance(self) -> float:
        return self._tube_to_center_distance

    @property
    def tube_specs(self) -> SpecimenTube:
        return self._tube_specs

    @property
    def material(self) -> Material:
        return self._material

    def __init__(self,
                 outer_radius:            float,
                 height:                  float,
                 number_of_tubes:         int,
                 tube_to_center_distance: float,
                 tube_specs:              SpecimenTube,
                 material:                Optional[Material] = None,
                 name:                    str = "rsr_cavity") -> None:
        super().__init__(name)
        assert outer_radius > 0.0, "RSR cavity outer radius must be positive."
        assert height > 0.0, "RSR cavity height must be positive."
        assert number_of_tubes > 0, "RSR cavity number of tubes must be positive."
        assert tube_to_center_distance > 0.0, "RSR cavity tube-to-center distance must be positive."

        self._outer_radius            = outer_radius
        self._height                  = height
        self._number_of_tubes         = number_of_tubes
        self._tube_to_center_distance = tube_to_center_distance
        self._tube_specs              = tube_specs
        self._material                = material or Air()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, RSRCavity)
            and isclose(self.outer_radius, other.outer_radius, rel_tol=TOL)
            and isclose(self.height, other.height, rel_tol=TOL)
            and self.number_of_tubes == other.number_of_tubes
            and isclose(self.tube_to_center_distance, other.tube_to_center_distance, rel_tol=TOL)
            and self.tube_specs == other.tube_specs
            and self.material == other.material
        )

    def __hash__(self) -> int:
        return hash((
            relative_round(self.outer_radius, TOL),
            relative_round(self.height, TOL),
            self.number_of_tubes,
            relative_round(self.tube_to_center_distance, TOL),
            self.tube_specs,
            self.material,
        ))
