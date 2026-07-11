"""Library loading and Geometry Nodes interface helpers."""

from pathlib import Path

import bpy

from .constants import (
    CONTROLLER_GROUP_TAG,
    GROUP_OWNER_TAG,
    LIBRARY_GROUP_NAME,
    LIBRARY_TAG,
    SOCKET_HELP,
)


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
        or node_group.get(CONTROLLER_GROUP_TAG) is not None
        or node_group.name == LIBRARY_GROUP_NAME
    )


def is_rainflow_modifier(modifier):
    return modifier.type == 'NODES' and is_rainflow_group(modifier.node_group)


def find_loaded_group():
    for group in bpy.data.node_groups:
        if (
            group.get(LIBRARY_TAG) is not None
            and not group.get(CONTROLLER_GROUP_TAG)
        ):
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


def _modifier_data_path(modifier, old_path):
    """Retarget an existing modifier ID-property path without changing its socket suffix."""
    suffix = old_path
    if old_path.startswith('modifiers["') and '"]' in old_path:
        suffix = old_path.split('"]', 1)[1]
    escaped_name = modifier.name.replace('\\', '\\\\').replace('"', '\\"')
    return f'modifiers["{escaped_name}"]{suffix}'


def relink_group_drivers(node_group, controller, modifier):
    """Point every object driver in a private control group at its controller."""
    animation_data = node_group.animation_data
    if not animation_data:
        return
    for fcurve in animation_data.drivers:
        for variable in fcurve.driver.variables:
            for target in variable.targets:
                if target.id_type != 'OBJECT':
                    continue
                target.id = controller
                target.data_path = _modifier_data_path(modifier, target.data_path)


def make_controller_node_group(controller, modifier, source_group=None):
    """Create an isolated main tree and isolated driven subgroups for one controller."""
    source_group = source_group or load_node_group()
    controller_group = source_group.copy()
    controller_group.name = f"{LIBRARY_GROUP_NAME} — {controller.name}"
    controller_group[CONTROLLER_GROUP_TAG] = True
    controller_group[GROUP_OWNER_TAG] = controller.name
    if LIBRARY_TAG in controller_group:
        del controller_group[LIBRARY_TAG]

    for node in controller_group.nodes:
        child_group = getattr(node, "node_tree", None)
        animation_data = getattr(child_group, "animation_data", None)
        if not animation_data or not animation_data.drivers:
            continue
        child_copy = child_group.copy()
        child_copy.name = f"{child_group.name} — {controller.name}"
        child_copy[CONTROLLER_GROUP_TAG] = True
        child_copy[GROUP_OWNER_TAG] = controller.name
        node.node_tree = child_copy
        relink_group_drivers(child_copy, controller, modifier)

    modifier.node_group = controller_group
    return controller_group


def ensure_controller_node_group(controller, modifier):
    """Migrate a shared/legacy setup or repair targets on an isolated setup."""
    node_group = modifier.node_group
    if not node_group or not node_group.get(CONTROLLER_GROUP_TAG):
        return make_controller_node_group(controller, modifier, node_group or load_node_group())

    node_group[GROUP_OWNER_TAG] = controller.name
    for node in node_group.nodes:
        child_group = getattr(node, "node_tree", None)
        if child_group and child_group.get(CONTROLLER_GROUP_TAG):
            child_group[GROUP_OWNER_TAG] = controller.name
            relink_group_drivers(child_group, controller, modifier)
    return node_group


def remove_controller_node_groups(node_group):
    """Remove private controller trees after their modifier owner has been deleted."""
    if not node_group or not node_group.get(CONTROLLER_GROUP_TAG):
        return
    child_groups = [
        node.node_tree for node in node_group.nodes
        if getattr(node, "node_tree", None)
        and node.node_tree.get(CONTROLLER_GROUP_TAG)
    ]
    if node_group.users == 0:
        bpy.data.node_groups.remove(node_group)
    for child_group in child_groups:
        if child_group.users == 0:
            bpy.data.node_groups.remove(child_group)
