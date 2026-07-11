"""Library loading and Geometry Nodes interface helpers."""

from pathlib import Path

import bpy

from .constants import LIBRARY_GROUP_NAME, LIBRARY_TAG, SOCKET_HELP


def bundled_library_path():
    return Path(__file__).parent / "resources" / "rainflow_library.blend"


def input_sockets(node_group):
    """Return all real input sockets in their published interface order."""
    return [
        item for item in node_group.interface.items_tree
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT'
    ]


def socket_tooltip(socket):
    return socket.description or SOCKET_HELP.get(socket.name, "")


def is_rainflow_group(node_group):
    return bool(node_group) and (
        node_group.get(LIBRARY_TAG) is not None
        or node_group.name == LIBRARY_GROUP_NAME
    )


def is_rainflow_modifier(modifier):
    return modifier.type == 'NODES' and is_rainflow_group(modifier.node_group)


def find_loaded_group():
    for group in bpy.data.node_groups:
        if group.get(LIBRARY_TAG) is not None:
            return group
    return bpy.data.node_groups.get(LIBRARY_GROUP_NAME)


def load_node_group():
    """Append the commercial node tree only when it is not loaded yet."""
    existing = find_loaded_group()
    if existing:
        return existing

    library = bundled_library_path()
    if not library.is_file():
        raise FileNotFoundError(
            "RainFlow's node library is missing. Reinstall the complete RainFlow package."
        )

    with bpy.data.libraries.load(str(library), link=False) as (data_from, data_to):
        if LIBRARY_GROUP_NAME not in data_from.node_groups:
            raise RuntimeError(
                "The bundled RainFlow library does not contain its main node group."
            )
        data_to.node_groups = [LIBRARY_GROUP_NAME]

    group = data_to.node_groups[0] or find_loaded_group()
    if not group:
        raise RuntimeError("Blender could not append the RainFlow node group.")
    return group
