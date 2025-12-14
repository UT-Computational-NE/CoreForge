from __future__ import annotations

from typing import ClassVar, Dict, List, TypeAlias

from coreforge.geometry_elements import GeometryElement, HexLattice
from coreforge.materials.material import Material
from coreforge.geometry_elements.triga import FuelElement, GraphiteElement
from coreforge.geometry_elements.triga.netl import (
    CentralThimble,
    FuelFollowerControlRod,
    SourceHolder,
    TransientRod,
)


class Core(GeometryElement):
    """TRIGA NETL core layout and reserved locations.

    Parameters
    ----------
    pitch : float
        Hexagonal lattice pitch [cm].
    central_thimble : CentralThimble
        Central thimble inserted at location A-01.
    transient_rod : TransientRod
        Transient control rod placed at C-01.
    regulating_rod : FuelFollowerControlRod
        Regulating rod placed at C-07.
    shim_1_rod : FuelFollowerControlRod
        Shim 1 rod placed at D-06.
    shim_2_rod : FuelFollowerControlRod
        Shim 2 rod placed at D-14.
    fill_material : Material
        Material to fill unoccupied core locations.
    loading : Dict[str, Loadable | None]
        Map of mutable locations to their contents; keys must be in ``RING_MAP``
        and not in the reserved locations (A-01, C-01, C-07, D-06, D-14,
        G-01, G-07, G-13, G-19, G-25, G-31). Any unspecified, non-reserved
        locations are set to ``None``.
    name : str, optional
        Name for this core element.

    Attributes
    ----------
    pitch : float
        Hexagonal lattice pitch [cm].
    central_thimble : CentralThimble
        Central thimble inserted at location A-01.
    transient_rod : TransientRod
        Transient control rod placed at C-01.
    regulating_rod : FuelFollowerControlRod
        Regulating rod placed at C-07.
    shim_1_rod : FuelFollowerControlRod
        Shim 1 rod placed at D-06.
    shim_2_rod : FuelFollowerControlRod
        Shim 2 rod placed at D-14.
    fill_material : Material
        Material to fill unoccupied core locations.
    loading : Dict[str, Loadable | None]
        Map of mutable locations to their contents
    full_map : Dict[str, Element | None]
        Full map of core locations to their contents.
    lattice : HexLattice
        CoreForge Hexagonal lattice representing the full core.

    Notes
    -----
    Reserved locations follow Ref. [1]_ Fig. 4.4 & pg. 4-9: C-01 (Transient),
    C-07 (Regulating), D-06 (Shim 1), D-14 (Shim 2), A-01 (Central thimble),
    and G-01/07/13/19/25/31 (water holes).

    References
    ----------
    .. [1] "University of Texas at Austin Nuclear Engineering Teaching Laboratory
           TRIGA Research Reactor", August 2023,
           https://www.nrc.gov/docs/ML2327/ML23279A146.pdf
    """

    RING_MAP: ClassVar[List[List[str]]] = [
        ["G-01", "G-02", "G-03", "G-04", "G-05", "G-06",
         "G-07", "G-08", "G-09", "G-10", "G-11", "G-12",
         "G-13", "G-14", "G-15", "G-16", "G-17", "G-18",
         "G-19", "G-20", "G-21", "G-22", "G-23", "G-24",
         "G-25", "G-26", "G-27", "G-28", "G-29", "G-30",
         "G-31", "G-32", "G-33", "G-34", "G-35", "G-36"],
        ["F-01", "F-02", "F-03", "F-04", "F-05", "F-06",
         "F-07", "F-08", "F-09", "F-10", "F-11", "F-12",
         "F-13", "F-14", "F-15", "F-16", "F-17", "F-18",
         "F-19", "F-20", "F-21", "F-22", "F-23", "F-24",
         "F-25", "F-26", "F-27", "F-28", "F-29", "F-30"],
        ["E-01", "E-02", "E-03", "E-04", "E-05", "E-06",
         "E-07", "E-08", "E-09", "E-10", "E-11", "E-12",
         "E-13", "E-14", "E-15", "E-16", "E-17", "E-18",
         "E-19", "E-20", "E-21", "E-22", "E-23", "E-24"],
        ["D-01", "D-02", "D-03", "D-04", "D-05", "D-06",
         "D-07", "D-08", "D-09", "D-10", "D-11", "D-12",
         "D-13", "D-14", "D-15", "D-16", "D-17", "D-18"],
        ["C-01", "C-02", "C-03", "C-04", "C-05", "C-06",
         "C-07", "C-08", "C-09", "C-10", "C-11", "C-12"],
        ["B-01", "B-02", "B-03", "B-04", "B-05", "B-06"],
        ["A-01"]
    ]

    Loadable: TypeAlias = FuelElement | GraphiteElement | SourceHolder
    Fixture: TypeAlias  = CentralThimble | TransientRod | FuelFollowerControlRod
    Element: TypeAlias  = FuelElement | GraphiteElement | SourceHolder | CentralThimble | TransientRod | FuelFollowerControlRod

    RESERVED_LOCATIONS: ClassVar[List[str]] = ["A-01", "C-01", "C-07", "D-06", "D-14",
                                               "G-01", "G-07", "G-13", "G-19", "G-25", "G-31"]

    @property
    def pitch(self) -> float:
        return self._pitch

    @property
    def central_thimble(self) -> CentralThimble:
        return self._central_thimble

    @property
    def transient_rod(self) -> TransientRod:
        return self._transient_rod

    @property
    def regulating_rod(self) -> FuelFollowerControlRod:
        return self._regulating_rod

    @property
    def shim_1_rod(self) -> FuelFollowerControlRod:
        return self._shim_1_rod

    @property
    def shim_2_rod(self) -> FuelFollowerControlRod:
        return self._shim_2_rod

    @property
    def fill_material(self) -> Material:
        return self._fill_material

    @property
    def loading(self) -> Dict[str, Loadable | None]:
        return self._loading

    @property
    def full_map(self) -> Dict[str, Element | None]:
        return self._full_map

    @property
    def lattice(self) -> HexLattice:
        return self._lattice

    def __init__(self,
                 pitch:           float,
                 central_thimble: CentralThimble,
                 transient_rod:   TransientRod,
                 regulating_rod:  FuelFollowerControlRod,
                 shim_1_rod:      FuelFollowerControlRod,
                 shim_2_rod:      FuelFollowerControlRod,
                 fill_material:   Material,
                 loading:         Dict[str, Loadable | None],
                 name:            str = "core") -> None:
        super().__init__(name)
        assert pitch > 0.0, "Core pitch must be positive."
        self._pitch           = pitch
        self._central_thimble = central_thimble
        self._transient_rod   = transient_rod
        self._regulating_rod  = regulating_rod
        self._shim_1_rod      = shim_1_rod
        self._shim_2_rod      = shim_2_rod
        self._fill_material   = fill_material
        self._loading    = dict(loading)

        for location in self._loading:
            assert any(location in ring for ring in Core.RING_MAP), \
                f"Invalid core location '{location}' in core loading."
            assert location not in Core.RESERVED_LOCATIONS, \
                f"Core location '{location}' is reserved for control rods or central thimble."

        reserved = {
            "A-01": self.central_thimble,
            "C-01": self.transient_rod,
            "C-07": self.regulating_rod,
            "D-06": self.shim_1_rod,
            "D-14": self.shim_2_rod,
            "G-01": None,
            "G-07": None,
            "G-13": None,
            "G-19": None,
            "G-25": None,
            "G-31": None,
        }

        full_map: Dict[str, Core.Element | None] = {}
        for ring in Core.RING_MAP:
            for loc in ring:
                if loc in reserved:
                    full_map[loc] = reserved[loc]
                else:
                    full_map[loc] = self._loading.get(loc, None)
        self._full_map = full_map

        self._lattice = HexLattice(pitch          = self.pitch,
                                   outer_material = self.fill_material,
                                   orientation    = "y",
                                   elements       = [[full_map[loc] for loc in ring]
                                                     for ring in Core.RING_MAP],
                                   map_type="ring")

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return (
            isinstance(other, Core)
            and self.pitch == other.pitch
            and self.central_thimble == other.central_thimble
            and self.transient_rod == other.transient_rod
            and self.regulating_rod == other.regulating_rod
            and self.shim_1_rod == other.shim_1_rod
            and self.shim_2_rod == other.shim_2_rod
            and self.loading == other.loading
            and self.fill_material == other.fill_material
        )

    def __hash__(self) -> int:
        return hash((
            self.pitch,
            self.central_thimble,
            self.transient_rod,
            self.regulating_rod,
            self.shim_1_rod,
            self.shim_2_rod,
            tuple(sorted(self.loading.items())),
            self.fill_material,
        ))
