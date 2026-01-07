from __future__ import annotations
from typing import List
from math import inf, sqrt

from coreforge import geometry_elements
import coreforge.geometry_elements.triga as geometry_elements_triga


def build_end_fitting_segments(length: float,
                               r2: float,
                               direction: str,
                               material: geometry_elements.Material,
                               outer_material: geometry_elements.Material,
                               target_axial_thickness: float,
                               name: str = "end_fitting"
                               ) -> List[geometry_elements.Stack.Segment]:
    """Build stack segments that approximate a conical end fitting.

    The cone is represented by equal-height cylinders whose radii preserve volume
    in each axial slice. Cylindrical pincells use a unionized set of radii shared
    across all segments, and each segment fills only the radii up to its effective
    radius with the end fitting material, filling the remaining rings with the
    outer material. The returned list is ordered from bottom to top based on the
    specified direction.

    Parameters
    ----------
    length : float
        Cone length (base to apex) [cm].
    r2 : float
        Square of the slope (dr/dz)^2 for the conical section.
    direction : str
        Orientation of the fitting ("up" or "down").
    material : Material
        End fitting material.
    outer_material : Material
        Material surrounding the end fitting.
    target_axial_thickness : float
        Target axial thickness for subdivision (cm).
    name : str, optional
        Base name for the generated pincell segments.

    Returns
    -------
    List[Stack.Segment]
        Stack segments representing the end fitting.
    """
    if not target_axial_thickness:
        target_axial_thickness = inf

    num_subd = max(1, int(length // target_axial_thickness))
    subd_length = length / num_subd

    r_base = sqrt(r2) * length

    radii = []
    for i in range(num_subd):
        z0 = i * subd_length
        z1 = (i + 1) * subd_length
        r0 = r_base * (1.0 - z0 / length)
        r1 = r_base * (1.0 - z1 / length)
        r_eq = sqrt((r0 * r0 + r0 * r1 + r1 * r1) / 3.0)
        radii.append(r_eq)

    radii = sorted(set(radii), reverse=True)

    segments = []
    for i, r_eq in enumerate(radii):
        materials = [material if radius <= r_eq else outer_material
                     for radius in radii]
        materials.append(outer_material)
        pincell = geometry_elements.CylindricalPinCell(
            radii=radii,
            materials=materials,
            name=f"{name}_{i:02d}_pincell",
        )
        segments.append(geometry_elements.Stack.Segment(pincell, subd_length))

    if direction == "down":
        segments = list(reversed(segments))

    return segments
