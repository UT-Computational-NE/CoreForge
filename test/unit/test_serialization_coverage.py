""" The inventory of what serializes and what does not

    ``test_serialization_contract.py`` says what a document must do. This file
    says how much of the package can produce one, and makes the remainder an
    explicit, reviewable list rather than a silence.

    The rule: every concrete ``Material``, ``GeometryElement`` and ``Shape`` is
    either registered as serializable or named in ``NOT_YET_SERIALIZABLE``
    below. Adding a class without doing one or the other fails, which is the
    point — the decision gets made when the class is written, by the person who
    knows what its state is, rather than discovered later by whoever first tries
    to archive a model.

    Removing an entry from the list is how implementing one is recorded. Leaving
    a stale entry also fails.
"""

import importlib
import inspect
import pkgutil

import pytest

import coreforge
from coreforge.geometry_elements.geometry_element import GeometryElement
from coreforge.materials import Material
from coreforge.serialization import (_REGISTRY, register_serializable,
                                     Serializable, SerializationNotImplemented)
from coreforge.shapes import Shape


#: Concrete classes that do not serialize yet, by ``module.ClassName``.
#:
#: This is a work list, not a rejection list. Nothing here is believed to be
#: unserializable; it is what had not been reached when the mechanism landed.
#: The materials are MSRE's four; the geometry is everything above the
#: pincell/lattice spine, plus the shape vocabulary beyond ``Circle``.
NOT_YET_SERIALIZABLE = frozenset({
    # -- Shapes. Mechanical: each is a handful of dimensions. Note the two
    #    OneSidedCone classes share a bare name and will need an explicit
    #    tag= when both are registered.
    "coreforge.shapes.cap.ASME_Flanged_Dished_Dome",
    "coreforge.shapes.cap.Torispherical_Dome",
    "coreforge.shapes.cone.Cone",
    "coreforge.shapes.cone.OneSidedCone",
    "coreforge.shapes.hexagon.Hexagon",
    "coreforge.shapes.rectangle.Rectangle",
    "coreforge.shapes.rectangle.Square",
    "coreforge.shapes.stadium.Stadium",

    # -- Geometry. Stack and CylindricalStack carry Segment specs whose
    #    meshing/geometry split needs deciding before they serialize (see
    #    the geometry-versus-mesh trap in the contract). The two Block
    #    classes share a bare name, as above.
    "coreforge.geometry_elements.block.Block",
    "coreforge.geometry_elements.cone.OneSidedCone",
    "coreforge.geometry_elements.cylindrical_stack.CylindricalStack",
    "coreforge.geometry_elements.msre.block.Block",
    "coreforge.geometry_elements.msre.control_channel.ControlChannel",
    "coreforge.geometry_elements.msre.stringer.Stringer",
    "coreforge.geometry_elements.rect_lattice.RectLattice",
    "coreforge.geometry_elements.stack.Stack",

    # -- TRIGA. These are the ones that matter for archiving the as-built
    #    NETL core, and they are the next work: each is composed from the
    #    elements above, so they unlock in dependency order.
    "coreforge.geometry_elements.triga.fuel_element.FuelElement",
    "coreforge.geometry_elements.triga.graphite_element.GraphiteElement",
    "coreforge.geometry_elements.triga.netl.beam_port.BeamPort",
    "coreforge.geometry_elements.triga.netl.central_thimble.CentralThimble",
    "coreforge.geometry_elements.triga.netl.core.Core",
    "coreforge.geometry_elements.triga.netl.fuel_follower_control_rod.FuelFollowerControlRod",
    "coreforge.geometry_elements.triga.netl.grid_plate.GridPlate",
    "coreforge.geometry_elements.triga.netl.pool.Pool",
    "coreforge.geometry_elements.triga.netl.reactor.Reactor",
    "coreforge.geometry_elements.triga.netl.reflector.Reflector",
    "coreforge.geometry_elements.triga.netl.rsr_cavity.RSRCavity",
    "coreforge.geometry_elements.triga.netl.shroud.Shroud",
    "coreforge.geometry_elements.triga.netl.source_holder.SourceHolder",
    "coreforge.geometry_elements.triga.netl.transient_rod.TransientRod",
})


def _import_the_whole_package():
    """ Subclasses are only discoverable once their module is imported
    """
    for module in pkgutil.walk_packages(coreforge.__path__, "coreforge."):
        importlib.import_module(module.name)


def _concrete_subclasses(base):
    """ Every non-abstract subclass of ``base``, at any depth
    """
    found = set()
    for subclass in base.__subclasses__():
        found.add(subclass)
        found |= _concrete_subclasses(subclass)
    return {cls for cls in found if not inspect.isabstract(cls)}


def _qualified(cls):
    return f"{cls.__module__}.{cls.__name__}"


def _all_concrete_classes():
    _import_the_whole_package()
    classes = set()
    for base in (Material, GeometryElement, Shape):
        classes |= _concrete_subclasses(base)
    return classes


def _registered(cls):
    """ Whether ``cls`` actually implements the mechanism

        Three ways to not be serializable, and all must read as "no": the class
        may not mix in ``Serializable`` at all — most ``Shape`` subclasses do
        not, only ``Circle`` does; it may mix it in and inherit the raising
        stub; or it may inherit a perfectly good implementation from its base
        and never be registered, in which case ``to_dict`` works and
        ``from_dict`` has nothing to dispatch to. The MSRE materials were all
        in that third state, which is what this predicate was written wrong for
        the first time.
    """
    own = getattr(cls, "_serial_state", None)
    implemented = own is not None and own is not Serializable._serial_state
    return implemented and cls.__name__ in _REGISTRY


# ---------------------------------------------------------------------------

def test_every_concrete_class_is_accounted_for():
    """ A new class must be implemented or listed, never neither

        This is the whole point of the file. It fails on the class that was
        added without a decision, naming it.
    """
    unaccounted = sorted(_qualified(cls) for cls in _all_concrete_classes()
                         if not _registered(cls)
                         and _qualified(cls) not in NOT_YET_SERIALIZABLE)

    assert not unaccounted, (
        "these classes neither serialize nor are listed as not-yet:\n  "
        + "\n  ".join(unaccounted)
        + "\n\nImplement _serial_state/_from_serial_state and register the "
          "class, or add it to NOT_YET_SERIALIZABLE with a note saying why."
    )


def test_the_not_yet_list_does_not_go_stale():
    """ Implementing a class must remove it from the list

        Otherwise the inventory drifts into fiction, which is worse than not
        having one.
    """
    by_name = {_qualified(cls): cls for cls in _all_concrete_classes()}

    now_implemented = sorted(name for name in NOT_YET_SERIALIZABLE
                             if name in by_name and _registered(by_name[name]))
    assert not now_implemented, (
        "these serialize now and should be removed from NOT_YET_SERIALIZABLE:\n  "
        + "\n  ".join(now_implemented))

    vanished = sorted(name for name in NOT_YET_SERIALIZABLE if name not in by_name)
    assert not vanished, (
        "these are listed as not-yet-serializable but no longer exist:\n  "
        + "\n  ".join(vanished))


def test_an_unregistered_class_fails_loudly_and_says_which():
    """ The gap must not surface as a confusing reload failure later

        A document that silently drops an unimplemented sub-object is the
        failure mode this guards against. Both ways of not implementing it
        raise, and both name the class.
    """
    class Unregistered(Serializable):
        """ Mixes the mixin in but never registers """

    with pytest.raises(SerializationNotImplemented, match="Unregistered"):
        Unregistered().to_dict()


def test_a_registered_class_without_state_fails_loudly_too():
    """ Registration alone is not implementation
    """
    @register_serializable(tag="_RegisteredButEmpty")
    class RegisteredButEmpty(Serializable):
        """ Registered, but never given _serial_state """

    with pytest.raises(SerializationNotImplemented, match="RegisteredButEmpty"):
        RegisteredButEmpty().to_dict()


def test_the_registry_holds_no_ambiguous_tags():
    """ Documents key nodes by bare class name, which is not globally unique

        Two ``Block`` classes and two ``OneSidedCone`` classes exist. None are
        registered yet, so nothing collides today, but whoever registers the
        second of a pair must pass an explicit ``tag=``. This asserts the
        registry is currently unambiguous so that a collision shows up as a
        failure here rather than as a silently overwritten node type.
    """
    _import_the_whole_package()
    tags = [cls.__name__ for cls in _REGISTRY.values()]
    duplicates = sorted({tag for tag in tags if tags.count(tag) > 1})

    assert not duplicates, f"ambiguous serialization tags: {duplicates}"
