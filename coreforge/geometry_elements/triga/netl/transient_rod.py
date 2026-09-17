from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import List, Optional, TypedDict

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.geometry_elements.cylindrical_pincell import CylindricalPinCell
from coreforge.geometry_elements.cylindrical_stack import CylindricalStack
from coreforge.geometry_elements.stack import Stack
from coreforge.materials import Air, Al6061T6, B4C, Material, Water, unique_materials
from coreforge.utils import TolerantEqualityMixin


# pylint: disable=too-many-public-methods
class TransientRod(GeometryElement):
    """TRIGA NETL transient rod definitions and pincell builders.

    Parameters
    ----------
    cladding : TransientRod.Cladding
        Cladding definition with thickness, outer radius, and material.
    absorber : TransientRod.Absorber
        Absorber definition with radius and material.
    fill_gas : Optional[Material]
        Material filling any gap between absorber and cladding (defaults to ``Air``).
    outer_material : Optional[Material]
        Coolant/exterior material outside the cladding (defaults to ``Water``).
    air_follower : TransientRod.AirFollower
        Air follower (axial metadata) specification.
    upper_element_plug : TransientRod.ElementPlug
        Upper element plug specification.
    upper_magneform_fitting : TransientRod.MagneformFitting
        Upper Magneform fitting specification.
    lower_magneform_fitting : TransientRod.MagneformFitting
        Lower Magneform fitting specification.
    lower_element_plug : TransientRod.ElementPlug
        Lower element plug specification.
    gap_tolerance : float, optional
        Minimum thickness to retain a radial zone; thinner gaps are removed. Defaults to ``None`` (no filtering).
    name : str, optional
        Name for the transient rod element.

    Attributes
    ----------
    length : float
        Length of the transient rod [cm].
    cladding : TransientRod.Cladding
        Cladding specification.
    absorber : TransientRod.Absorber
        Absorber specification.
    fill_gas : Material
        Gap fill material.
    outer_material : Material
        Coolant/exterior material.
    gap_tolerance : float, optional
        Minimum thickness to retain a radial zone (defaults to ``None`` for no filtering).
    air_follower : TransientRod.AirFollower
        Air follower (axial metadata).
    pincell : TransientRod.Pincell
        Pincells keyed by axial feature.
    """

    @dataclass(frozen=True, eq=False)
    class Cladding(TolerantEqualityMixin):
        """Transient rod cladding specification.

        Parameters
        ----------
        thickness : float
            Cladding thickness [cm].
        outer_radius : float
            Cladding outer radius [cm].
        material : Material, optional
            Cladding material (defaults to ``Al6061T6``).
        """
        thickness: float
        outer_radius: float
        inner_radius: float = field(init=False)
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Cladding thickness must be positive."
            assert self.outer_radius > self.thickness, (
                "Cladding outer radius must exceed thickness."
            )
            object.__setattr__(self, "inner_radius", self.outer_radius - self.thickness)

    @dataclass(frozen=True, eq=False)
    class Absorber(TolerantEqualityMixin):
        """Transient rod absorber specification.

        Parameters
        ----------
        radius : float
            Radius of the absorber [cm].
        length : float
            Length of the absorber [cm].
        material : Material, optional
            Absorber material (defaults to ``B4C``).
        """
        radius: float
        length: float
        material: Material = field(default_factory=B4C)

        def __post_init__(self) -> None:
            assert self.radius > 0.0, "Absorber radius must be positive."
            assert self.length > 0.0, "Absorber length must be positive."

    @dataclass(frozen=True, eq=False)
    class AirFollower(TolerantEqualityMixin):
        """Transient rod air follower (axial length metadata).

        Parameters
        ----------
        thickness : float
            Axial thickness of the air follower [cm].
        """
        thickness: float

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Air follower thickness must be positive."

    @dataclass(frozen=True, eq=False)
    class ElementPlug(TolerantEqualityMixin):
        """Transient rod element plug specification (axial metadata only).

        Parameters
        ----------
        thickness : float
            Axial thickness of the plug [cm].
        material : Material, optional
            Plug material (defaults to ``Al6061T6``).
        """
        thickness: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Element plug thickness must be positive."

    @dataclass(frozen=True, eq=False)
    class MagneformFitting(TolerantEqualityMixin):
        """Transient rod Magneform fitting specification (axial metadata only).

        Parameters
        ----------
        thickness : float
            Axial thickness of the fitting [cm].
        material : Material, optional
            Fitting material (defaults to ``Al6061T6``).
        """
        thickness: float
        material: Material = field(default_factory=Al6061T6)

        def __post_init__(self) -> None:
            assert self.thickness > 0.0, "Magneform fitting thickness must be positive."

    class Pincell(TypedDict):
        """Pincells used to construct the transient-rod axial stack."""

        absorber: CylindricalPinCell
        air_follower: CylindricalPinCell
        upper_element_plug: CylindricalPinCell
        lower_element_plug: CylindricalPinCell
        upper_magneform_fitting: CylindricalPinCell
        lower_magneform_fitting: CylindricalPinCell

    @property
    def length(self) -> float:
        return self._length

    @property
    def cladding(self) -> Cladding:
        return self._cladding

    @property
    def absorber(self) -> Absorber:
        return self._absorber

    @property
    def air_follower(self) -> AirFollower:
        return self._air_follower

    @property
    def upper_element_plug(self) -> ElementPlug:
        return self._upper_element_plug

    @property
    def upper_magneform_fitting(self) -> MagneformFitting:
        return self._upper_magneform_fitting

    @property
    def lower_magneform_fitting(self) -> MagneformFitting:
        return self._lower_magneform_fitting

    @property
    def lower_element_plug(self) -> ElementPlug:
        return self._lower_element_plug

    @property
    def fill_gas(self) -> Material:
        return self._fill_gas

    @property
    def outer_material(self) -> Material:
        return self._outer_material

    @property
    def gap_tolerance(self) -> Optional[float]:
        return self._gap_tolerance

    @property
    def pincell(self) -> Pincell:
        return self._pincell.copy()

    def __init__(self,
                 cladding:                Cladding,
                 absorber:                Absorber,
                 air_follower:            AirFollower,
                 upper_element_plug:      ElementPlug,
                 upper_magneform_fitting: MagneformFitting,
                 lower_magneform_fitting: MagneformFitting,
                 lower_element_plug:      ElementPlug,
                 fill_gas:                Optional[Material] = None,
                 outer_material:          Optional[Material] = None,
                 gap_tolerance:           Optional[float] = None,
                 name:                    str = "transient_rod"):
        super().__init__(name)
        self._cladding = cladding
        self._absorber = absorber
        self._air_follower = air_follower
        self._upper_element_plug = upper_element_plug
        self._upper_magneform_fitting = upper_magneform_fitting
        self._lower_magneform_fitting = lower_magneform_fitting
        self._lower_element_plug = lower_element_plug
        self._fill_gas = fill_gas or Air()
        self._outer_material = outer_material or Water()
        self._gap_tolerance = gap_tolerance

        self._length = (self.lower_element_plug.thickness +
                        self.air_follower.thickness +
                        self.lower_magneform_fitting.thickness +
                        self.absorber.length +
                        self.upper_magneform_fitting.thickness +
                        self.upper_element_plug.thickness)

        absorber_pincell = self.build_absorber_pincell(
            cladding=self.cladding,
            absorber=self.absorber,
            fill_gas=self.fill_gas,
            outer_material=self.outer_material,
            gap_tolerance=self.gap_tolerance,
            name=self.name + "_absorber_pincell",
        )

        air_follower_pincell = self.build_air_follower_pincell(
            cladding=self.cladding,
            fill_gas=self.fill_gas,
            outer_material=self.outer_material,
            name=self.name + "_air_follower_pincell",
        )
        upper_element_plug_pincell = self.build_element_plug_pincell(
            cladding=self.cladding,
            plug=self.upper_element_plug,
            outer_material=self.outer_material,
            name=self.name + "_upper_element_plug_pincell",
        )
        upper_magneform_fitting_pincell = self.build_magneform_fitting_pincell(
            cladding=self.cladding,
            fitting=self.upper_magneform_fitting,
            outer_material=self.outer_material,
            name=self.name + "_upper_magneform_fitting_pincell",
        )
        lower_element_plug_pincell = self.build_element_plug_pincell(
            cladding=self.cladding,
            plug=self.lower_element_plug,
            outer_material=self.outer_material,
            name=self.name + "_lower_element_plug_pincell",
        )
        lower_magneform_fitting_pincell = self.build_magneform_fitting_pincell(
            cladding=self.cladding,
            fitting=self.lower_magneform_fitting,
            outer_material=self.outer_material,
            name=self.name + "_lower_magneform_fitting_pincell",
        )
        self._pincell: TransientRod.Pincell = {
            "absorber": absorber_pincell,
            "air_follower": air_follower_pincell,
            "upper_element_plug": upper_element_plug_pincell,
            "lower_element_plug": lower_element_plug_pincell,
            "upper_magneform_fitting": upper_magneform_fitting_pincell,
            "lower_magneform_fitting": lower_magneform_fitting_pincell,
        }

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, TransientRod):
            return False
        return (
            self.cladding == other.cladding and
            self.absorber == other.absorber and
            self.air_follower == other.air_follower and
            self.upper_element_plug == other.upper_element_plug and
            self.upper_magneform_fitting == other.upper_magneform_fitting and
            self.lower_magneform_fitting == other.lower_magneform_fitting and
            self.lower_element_plug == other.lower_element_plug and
            self.fill_gas == other.fill_gas and
            self.outer_material == other.outer_material and
            ((self.gap_tolerance is None and other.gap_tolerance is None) or
             (self.gap_tolerance is not None and other.gap_tolerance is not None and
              isclose(self.gap_tolerance, other.gap_tolerance, rel_tol=TOL)))
        )

    def __hash__(self) -> int:
        return hash((
            self.cladding,
            self.absorber,
            self.air_follower,
            self.upper_element_plug,
            self.upper_magneform_fitting,
            self.lower_magneform_fitting,
            self.lower_element_plug,
            self.fill_gas,
            self.outer_material,
            None if self.gap_tolerance is None else relative_round(self.gap_tolerance, TOL),
        ))

    def get_materials(self) -> List[Material]:
        materials = [
            self.cladding.material,
            self.absorber.material,
            self.fill_gas,
            self.outer_material,
            self.upper_element_plug.material,
            self.lower_element_plug.material,
            self.upper_magneform_fitting.material,
            self.lower_magneform_fitting.material,
        ]
        return unique_materials(materials)

    def as_stack(self, bottom_pos: float = 0.0) -> CylindricalStack:
        """ A method for getting a copy of the Transient Rod as a Stack

        Parameters
        ----------
        bottom_pos : float
            The axial position of the bottom of the stack (cm)

        Returns
        -------
        CylindricalStack
            The Transient Rod as a Stack
        """

        pincell = self.pincell
        return CylindricalStack(
            segments   = [Stack.Segment(pincell["lower_element_plug"], self.lower_element_plug.thickness),
                          Stack.Segment(pincell["air_follower"], self.air_follower.thickness),
                          Stack.Segment(pincell["lower_magneform_fitting"], self.lower_magneform_fitting.thickness),
                          Stack.Segment(pincell["absorber"], self.absorber.length),
                          Stack.Segment(pincell["upper_magneform_fitting"], self.upper_magneform_fitting.thickness),
                          Stack.Segment(pincell["upper_element_plug"], self.upper_element_plug.thickness)],
            name       = self.name,
            bottom_pos = bottom_pos)

    @staticmethod
    def build_absorber_pincell(cladding:       Cladding,
                               absorber:       Absorber,
                               fill_gas:       Optional[Material] = None,
                               outer_material: Optional[Material] = None,
                               gap_tolerance:  Optional[float] = None,
                               name:           str = "transient_rod_absorber") -> CylindricalPinCell:
        """Build a pincell for the absorber region with concentric cladding.

        Parameters
        ----------
        cladding : TransientRod.Cladding
            Cladding definition with inner/outer radii and material.
        absorber : TransientRod.Absorber
            Absorber definition with radius and material.
        fill_gas : Material, optional
            Gap fill material between absorber and cladding (defaults to ``Air``).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        gap_tolerance : float, optional
            Minimum zone thickness to retain (defaults to ``None`` for no filtering).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the absorber stack.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        tol = gap_tolerance or 0.0
        assert absorber.radius <= cladding.inner_radius + tol, (
            "Absorber must be inside the cladding."
        )

        radii = [absorber.radius, cladding.inner_radius, cladding.outer_radius]
        materials = [absorber.material, fill_gas, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name,
                                  min_zone_thickness=gap_tolerance)

    @staticmethod
    def build_element_plug_pincell(cladding:       Cladding,
                                   plug:           ElementPlug,
                                   outer_material: Optional[Material] = None,
                                   name:           str = "transient_rod_element_plug") -> CylindricalPinCell:
        """Build a pincell for the element plug region (solid inside cladding).

        Parameters
        ----------
        cladding : TransientRod.Cladding
            Cladding definition with inner/outer radii and material.
        plug : TransientRod.ElementPlug
            Plug material and axial metadata.
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the plug region.
        """
        outer_material = outer_material or Water()

        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [plug.material, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name)

    @staticmethod
    def build_magneform_fitting_pincell(cladding:       Cladding,
                                        fitting:        MagneformFitting,
                                        outer_material: Optional[Material] = None,
                                        name:           str = "transient_rod_magneform_fitting") -> CylindricalPinCell:
        """Build a pincell for the Magneform fitting region (solid inside cladding).

        Parameters
        ----------
        cladding : TransientRod.Cladding
            Cladding definition with inner/outer radii and material.
        fitting : TransientRod.MagneformFitting
            Fitting material and axial metadata.
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the Magneform fitting region.
        """
        outer_material = outer_material or Water()

        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [fitting.material, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name)

    @staticmethod
    def build_air_follower_pincell(cladding:       Cladding,
                                   fill_gas:       Optional[Material] = None,
                                   outer_material: Optional[Material] = None,
                                   name:           str = "transient_rod_air_follower") -> CylindricalPinCell:
        """Build a pincell for the air-follower region using cladding inner radius.

        Parameters
        ----------
        cladding : TransientRod.Cladding
            Cladding definition with inner/outer radii and material.
        fill_gas : Material, optional
            Air-follower material (defaults to ``Air``).
        outer_material : Material, optional
            Exterior/coolant material (defaults to ``Water``).
        name : str, optional
            Name for the pincell.

        Returns
        -------
        CylindricalPinCell
            Concentric pincell representing the air-follower region.
        """
        fill_gas = fill_gas or Air()
        outer_material = outer_material or Water()

        assert cladding.inner_radius > 0.0, "Cladding inner radius must be positive."

        radii = [cladding.inner_radius, cladding.outer_radius]
        materials = [fill_gas, cladding.material, outer_material]

        return CylindricalPinCell(radii=radii, materials=materials, name=name)
