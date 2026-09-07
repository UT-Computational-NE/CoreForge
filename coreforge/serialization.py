""" Serialization for materials and geometry elements

A CoreForge model is a Python program today, which means it cannot be archived,
diffed, reviewed, or handed to anything that is not a Python process holding the
same imports. This module gives it a document form.

The acceptance criteria live in ``test/unit/test_serialization_contract.py``.
This docstring records *why* the format looks the way it does, and — where a
decision rests on inference rather than something checked — says so plainly.


The asymmetry: recipe for materials, resolved state for geometry
---------------------------------------------------------------

These pull in opposite directions and the difference is not cosmetic.

**Materials serialize their recipe** — class name plus constructor arguments.
Two reasons, both checked:

1. ``mpact_builder.DEFAULT_MPACT_MATERIAL_SPECS`` is typed
   ``Dict[type[Material], MPACTSpecs]`` — keyed by *class*. ``UZrH`` maps to
   ``{'Zr': "Zr_in_ZrH2", 'H': "H1_in_ZrH"}``. Rebuild a material as a generic
   ``Material`` carrying the right number densities and it compares equal
   (``Material.__eq__`` only inspects name, density, temperature and number
   densities) — so a round-trip test passes while MPACT rendering silently
   loses its thermal scattering. A passing test over a broken model.
2. ``Graphite`` is a *calculation*, not a composition: theoretical density,
   boron-equivalent contamination, and a ``pore_intrusion`` map, mixed through
   OpenMC. Its number densities cannot be inverted back into its arguments.

**Geometry elements serialize their resolved state** — what the object *is*
after construction, not the arguments that produced it. ``CylindricalPinCell``
accepts ``radii``/``materials`` and lowers them into ``zones``; it accepts
``min_zone_thickness``, filters zones with it, and then **does not retain it**
(verified: no attribute survives construction). The filtering is already
materialized in the zones, so storing zones reproduces the object exactly and
storing the threshold would be storing something the object does not have.

Note the class docstring of ``CylindricalPinCell`` lists ``min_zone_thickness``
under Attributes. It is not one. That is a documentation bug in that module, not
a thing this format should try to honour.


Shared nodes are interned by content
------------------------------------

A core is mostly the same element repeated. Inlining it once per position loses
object identity on load, so a build that de-duplicates by hash sees N distinct
lattices where it should see one.

So a document is a flat table of nodes keyed by content hash, plus a root
reference. Any value that is itself a serializable object is replaced by its
hash. Identity is therefore restored by *content*, never by name — two
same-named objects with different content are different nodes, which mirrors the
guard in ``unique_materials``.

**Floats are rounded with ``relative_round`` before hashing**, using the same
``ROUNDING_RELATIVE_TOLERANCE`` the library's ``__hash__`` implementations use.
Without that, two objects that compare equal under the tolerance-aware
``__eq__`` would intern as two different nodes, and the format would break the
very de-duplication it exists to preserve.


What is *not* settled
---------------------

Stated so a reviewer can disagree with a decision rather than discover it.

- **The hash is truncated to 16 hex characters.** Long enough that a collision
  is not a practical concern for a reactor model, short enough to read in a
  diff. Arbitrary; change it freely.
- **The format tag is ``coreforge/1``.** There is no migration story yet,
  because there is nothing to migrate. When the shape changes, this is where a
  version check goes.
- **A node's ``class`` tag is the bare class name.** Readable in a diff, and
  unique across everything registered today. It is *not* unique across the
  package: ``geometry_elements.block.Block`` and
  ``geometry_elements.msre.block.Block`` share a name, as do the two
  ``OneSidedCone`` classes. Neither pair is registered yet, so nothing collides
  today; ``register_serializable(tag=...)`` is the escape hatch, and a
  collision raises at import rather than overwriting. The alternative — keying
  by ``module.qualname`` — was rejected because it bakes module paths into
  stored documents, so moving a file would invalidate archived models.
- **Only registered classes serialize.** 18 of the 52 concrete classes are
  implemented; the rest raise a clear error naming themselves rather than
  silently emitting a partial document. ``test_serialization_coverage.py``
  holds the full inventory, and fails when a new class is added without a
  decision either way.
- Whether the document should carry provenance — a CoreForge version, a
  timestamp — is deliberately left open. Adding it changes the content hash, so
  it should be decided before anything depends on hashes being stable.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, Type

from mpactpy.utils import relative_round, ROUNDING_RELATIVE_TOLERANCE as TOL

__all__ = [
    "FORMAT",
    "SerializationNotImplemented",
    "Serializable",
    "register_serializable",
    "serializable_tag",
]

#: Document format tag. Bump when the shape changes incompatibly.
FORMAT = "coreforge/1"

#: Characters of the content hash kept as a node key.
HASH_LENGTH = 16

#: tag -> class, populated by :func:`register_serializable`.
_REGISTRY: Dict[str, type] = {}


class SerializationNotImplemented(NotImplementedError):
    """ A class in the object graph does not serialize yet

        Raised by name rather than emitting a partial document, so a gap is
        obvious at the point it is hit instead of surfacing as a confusing
        reload failure later.
    """


def register_serializable(cls: type = None, *, tag: str = None):
    """ Register a class for ``from_dict`` dispatch

        The tag defaults to the bare class name, which keeps documents readable.
        Bare names are not unique across this package — there are two ``Block``
        classes and two ``OneSidedCone`` classes — so ``tag`` is available to
        disambiguate. A collision raises rather than silently overwriting.

        Parameters
        ----------
        cls : type, optional
            The class to register. Omitted when used as ``@register_serializable(tag=...)``.
        tag : str, optional
            The name to store in the document. Defaults to ``cls.__name__``.

        Returns
        -------
        type
            ``cls``, so this can be used as a decorator.
    """
    if cls is None:
        return lambda target: register_serializable(target, tag=tag)

    tag = tag if tag is not None else cls.__name__
    existing = _REGISTRY.get(tag)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"two classes registered as {tag!r}: {existing!r} and {cls!r}. "
            "Pass an explicit tag= to disambiguate; see coreforge/serialization.py."
        )
    _REGISTRY[tag] = cls
    return cls


def serializable_tag(obj: Any) -> str:
    """ The registry tag for ``obj``'s class

        Raises
        ------
        SerializationNotImplemented
            If the class has not been registered.
    """
    tag = type(obj).__name__
    if tag not in _REGISTRY:
        raise SerializationNotImplemented(
            f"{tag} does not serialize yet. Register it with "
            "@register_serializable and give it _serial_state / "
            "_from_serial_state; see coreforge/serialization.py."
        )
    return tag


def _canonical(value: Any) -> Any:
    """ Round floats so tolerance-equal values hash identically
    """
    if isinstance(value, float):
        return relative_round(value, TOL)
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in sorted(value.items(), key=repr)}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def _content_hash(state: dict) -> str:
    payload = json.dumps(_canonical(state), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:HASH_LENGTH]


class Serializable:
    """ Mixin giving a class a document form

        A subclass implements two methods:

        ``_serial_state(self, intern)``
            Return this object's own fields as a plain dict. Call ``intern``
            on any value that is itself serializable; it returns a reference
            string to be stored in place of the object.

        ``_from_serial_state(cls, state, resolve)``
            Rebuild from that dict. Call ``resolve`` on a reference string to
            get the object back.
    """

    def _serial_state(self, intern: Callable[[Any], str]) -> dict:
        raise SerializationNotImplemented(
            f"{type(self).__name__} has no _serial_state; see "
            "coreforge/serialization.py"
        )

    @classmethod
    def _from_serial_state(cls, state: dict, resolve: Callable[[str], Any]) -> Any:
        raise SerializationNotImplemented(
            f"{cls.__name__} has no _from_serial_state; see "
            "coreforge/serialization.py"
        )

    def to_dict(self) -> dict:
        """ Build a self-contained document describing this object

            Returns
            -------
            dict
                ``{"format": ..., "root": <ref>, "nodes": {<ref>: {...}}}``,
                JSON-serializable throughout.
        """
        nodes: Dict[str, dict] = {}
        root = _intern(self, nodes)
        return {"format": FORMAT, "root": root, "nodes": nodes}

    @classmethod
    def from_dict(cls, document: dict) -> Any:
        """ Rebuild the object a document describes

            The concrete class comes from the document, not from the class this
            is called on, so ``GeometryElement.from_dict`` and
            ``CylindricalPinCell.from_dict`` behave identically.

            Raises
            ------
            ValueError
                If the format tag is unrecognised.
        """
        fmt = document.get("format")
        if fmt != FORMAT:
            raise ValueError(
                f"unrecognised document format {fmt!r}; this build reads {FORMAT!r}"
            )
        return _resolve(document["root"], document["nodes"], {})


def _intern(obj: Any, nodes: Dict[str, dict]) -> str:
    """ Store ``obj`` in ``nodes`` under its content hash; return the reference
    """
    tag = serializable_tag(obj)
    # pylint: disable=protected-access
    # _serial_state / _from_serial_state are this module's own protocol. They
    # are underscored so they do not show up as public API on every material
    # and geometry element, and this module is the only intended caller.
    state = obj._serial_state(lambda child: _intern(child, nodes))
    node = {"class": tag, "state": state}
    ref = _content_hash(node)
    nodes.setdefault(ref, node)
    return ref


def _resolve(ref: str, nodes: Dict[str, dict], cache: Dict[str, Any]) -> Any:
    """ Rebuild the object a reference names, sharing repeated nodes
    """
    if ref in cache:
        return cache[ref]

    node = nodes.get(ref)
    if node is None:
        raise ValueError(f"document references unknown node {ref!r}")

    tag = node["class"]
    target: Type[Any] | None = _REGISTRY.get(tag)
    if target is None:
        raise SerializationNotImplemented(
            f"document contains a {tag!r} node, but no such class is registered "
            "in this build"
        )

    obj = target._from_serial_state(  # pylint: disable=protected-access
        node["state"], lambda child_ref: _resolve(child_ref, nodes, cache)
    )
    cache[ref] = obj
    return obj
