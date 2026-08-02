"""Library loading and Geometry Nodes interface helpers."""

from pathlib import Path

import bpy

from .constants import (
    CONTROLLER_GROUP_TAG,
    CONTROL_OUTPUT_BINDINGS,
    DEFAULT_SOCKET_VALUES,
    GROUP_GRAPH_VERSION,
    GROUP_GRAPH_VERSION_TAG,
    GROUP_OWNER_TAG,
    LIBRARY_GROUP_NAME,
    LIBRARY_SOURCE_TAG,
    LIBRARY_TAG,
    POST_OUTPUT_BINDINGS,
    REQUIRED_INPUT_SOCKETS,
    SOCKET_HELP,
    SOCKET_NAME_ALIASES,
    SOCKET_UI_RANGES,
)


def bundled_library_path():
    return Path(__file__).parent / "resources" / "rainflow_library.blend"


def input_sockets(node_group):
    """Return all real input sockets in their published interface order."""
    return [
        item for item in node_group.interface.items_tree
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT'
    ]


def ensure_user_interface(node_group):
    """Apply backwards-compatible names, descriptions, and required inputs."""
    for socket in input_sockets(node_group):
        socket.name = SOCKET_NAME_ALIASES.get(socket.name, socket.name)

    sockets_by_name = {socket.name: socket for socket in input_sockets(node_group)}
    for name, spec in REQUIRED_INPUT_SOCKETS.items():
        socket = sockets_by_name.get(name)
        if socket and socket.socket_type != spec["socket_type"]:
            node_group.interface.remove(socket)
            socket = None
        if not socket:
            socket = node_group.interface.new_socket(
                name=name,
                in_out='INPUT',
                socket_type=spec["socket_type"],
            )
        socket.default_value = spec["default"]
        if "min" in spec:
            socket.min_value = spec["min"]
        if "soft_max" in spec:
            socket.max_value = spec["soft_max"]
        sockets_by_name[name] = socket

    for socket in input_sockets(node_group):
        description = SOCKET_HELP.get(socket.name)
        if description:
            socket.description = description
        if socket.name in DEFAULT_SOCKET_VALUES and hasattr(socket, "default_value"):
            socket.default_value = DEFAULT_SOCKET_VALUES[socket.name]
        limits = SOCKET_UI_RANGES.get(socket.name)
        if limits and hasattr(socket, "min_value"):
            socket.min_value, socket.max_value = limits
    return node_group


def modifier_socket_input(modifier, identifier):
    """Return Blender 5.2's typed modifier input entry when available."""
    properties = getattr(modifier, "properties", None)
    inputs = getattr(properties, "inputs", None) if properties else None
    return getattr(inputs, identifier, None) if inputs else None


def modifier_socket_value(modifier, identifier):
    """Read a Geometry Nodes modifier input in Blender 5.1 or 5.2+."""
    entry = modifier_socket_input(modifier, identifier)
    if entry:
        return entry.value
    try:
        return modifier.get(identifier)
    except TypeError:
        return None


def set_modifier_socket_value(modifier, identifier, value):
    """Write a Geometry Nodes modifier input in Blender 5.1 or 5.2+."""
    entry = modifier_socket_input(modifier, identifier)
    if entry:
        entry.value = value
        return
    modifier[identifier] = value


def _set_modifier_property(modifier, identifier, value):
    """Replace an ID property when its Python type needs to change."""
    entry = modifier_socket_input(modifier, identifier)
    if entry:
        entry.value = value
        return
    current = modifier.get(identifier)
    if current is not None and type(current) is not type(value):
        del modifier[identifier]
    modifier[identifier] = value


def ensure_modifier_properties(modifier, apply_defaults=False):
    """Create new controls, migrate types, and attach real UI tooltips."""
    node_group = ensure_user_interface(modifier.node_group)
    for socket in input_sockets(node_group):
        identifier = socket.identifier
        current = modifier_socket_value(modifier, identifier)

        if socket.name == "iterations":
            value = DEFAULT_SOCKET_VALUES["iterations"] if current is None else current
            if apply_defaults:
                value = DEFAULT_SOCKET_VALUES["iterations"]
            _set_modifier_property(modifier, identifier, max(1, int(round(value))))
        elif socket.name in DEFAULT_SOCKET_VALUES and (apply_defaults or current is None):
            _set_modifier_property(
                modifier, identifier, DEFAULT_SOCKET_VALUES[socket.name]
            )

        description = SOCKET_HELP.get(socket.name, "")
        limits = SOCKET_UI_RANGES.get(socket.name)
        if modifier_socket_input(modifier, identifier):
            continue
        try:
            ui_data = modifier.id_properties_ui(identifier)
            ui_options = {"description": description}
            if socket.name in DEFAULT_SOCKET_VALUES:
                ui_options["default"] = DEFAULT_SOCKET_VALUES[socket.name]
            if limits:
                ui_options.update(
                    min=limits[0], max=limits[1],
                    soft_min=limits[0], soft_max=limits[1],
                )
            ui_data.update(**ui_options)
        except (KeyError, TypeError):
            pass


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
        return ensure_user_interface(existing)

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
    return ensure_user_interface(group)


def _socket_identifier_from_path(data_path):
    if "].properties.inputs." in data_path:
        return data_path.split(".properties.inputs.", 1)[1].split(".", 1)[0]
    quoted = data_path.split('["')
    if len(quoted) >= 3:
        return quoted[-1].split('"]', 1)[0]
    return None


def _modifier_data_path(modifier, old_path, modifier_sockets=None):
    """Retarget a driver to the current modifier and Blender input API."""
    suffix = old_path
    if old_path.startswith('modifiers["') and '"]' in old_path:
        suffix = old_path.split('"]', 1)[1]
    escaped_name = modifier.name.replace('\\', '\\\\').replace('"', '\\"')
    identifier = _socket_identifier_from_path(old_path)
    if identifier == "Socket_5" and modifier_sockets:
        identifier = modifier_sockets.get("iterations", identifier)
    entry = modifier_socket_input(modifier, identifier) if identifier else None
    array_suffix = ""
    if old_path.endswith("]") and "[" in old_path.rsplit('"', 1)[-1]:
        array_suffix = old_path[old_path.rfind("["):]
    if entry:
        return (
            f'modifiers["{escaped_name}"].properties.inputs.'
            f'{identifier}.value{array_suffix}'
        )
    if identifier:
        return f'modifiers["{escaped_name}"]["{identifier}"]{array_suffix}'
    return f'modifiers["{escaped_name}"]{suffix}'


def relink_group_drivers(
    node_group, controller, modifier, modifier_sockets=None
):
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
                target.data_path = _modifier_data_path(
                    modifier, target.data_path, modifier_sockets
                )


def _configure_socket_driver(socket, socket_identifier, controller, modifier, index=None):
    """Create or replace one direct Group Output driver."""
    fcurve = (
        socket.driver_add("default_value", index)
        if index is not None else socket.driver_add("default_value")
    )
    driver = fcurve.driver
    while driver.variables:
        driver.variables.remove(driver.variables[0])
    variable = driver.variables.new()
    variable.name = socket_identifier
    variable.type = 'SINGLE_PROP'
    target = variable.targets[0]
    target.id_type = 'OBJECT'
    target.id = controller
    suffix = f'[{index}]' if index is not None else ''
    target.data_path = _modifier_data_path(
        modifier, f'modifiers["unused"]["{socket_identifier}"]{suffix}'
    )
    driver.expression = variable.name


def ensure_direct_output_drivers(node_group, controller, modifier, modifier_sockets):
    """Restore streamlined controls/post drivers directly on Group Output sockets."""
    if node_group.name.startswith("controls"):
        bindings = CONTROL_OUTPUT_BINDINGS
    elif node_group.name.startswith("post"):
        bindings = POST_OUTPUT_BINDINGS
    else:
        return

    output_node = next(
        (node for node in node_group.nodes if node.bl_idname == 'NodeGroupOutput'),
        None,
    )
    if not output_node:
        return
    for output_name, modifier_socket_name in bindings.items():
        output_socket = output_node.inputs.get(output_name)
        socket_identifier = modifier_sockets.get(modifier_socket_name)
        if not output_socket or not socket_identifier:
            continue
        linked_sockets = [
            link.from_socket
            for link in node_group.links
            if link.to_socket == output_socket
        ]
        target_socket = linked_sockets[0] if linked_sockets else output_socket
        default_value = getattr(target_socket, "default_value", None)
        if hasattr(default_value, "__len__") and not isinstance(default_value, str):
            for index in range(len(default_value)):
                _configure_socket_driver(
                    target_socket, socket_identifier, controller, modifier, index
                )
        else:
            _configure_socket_driver(
                target_socket, socket_identifier, controller, modifier
            )


def _copy_group_graph(source_group, controller, modifier, modifier_sockets, copies):
    """Copy a node group and its complete nested Geometry Nodes dependency graph."""
    if source_group in copies:
        return copies[source_group]

    group_copy = source_group.copy()
    copies[source_group] = group_copy
    group_copy.name = f"{source_group.name} — {controller.name}"
    group_copy[CONTROLLER_GROUP_TAG] = True
    group_copy[GROUP_OWNER_TAG] = controller.name
    group_copy[GROUP_GRAPH_VERSION_TAG] = GROUP_GRAPH_VERSION
    if LIBRARY_TAG in group_copy:
        del group_copy[LIBRARY_TAG]
    if LIBRARY_SOURCE_TAG in group_copy:
        del group_copy[LIBRARY_SOURCE_TAG]

    for node in group_copy.nodes:
        child_group = getattr(node, "node_tree", None)
        if not child_group or child_group.bl_idname != 'GeometryNodeTree':
            continue
        node.node_tree = _copy_group_graph(
            child_group, controller, modifier, modifier_sockets, copies
        )

    relink_group_drivers(
        group_copy, controller, modifier, modifier_sockets
    )
    ensure_direct_output_drivers(
        group_copy, controller, modifier, modifier_sockets
    )
    return group_copy


def make_controller_node_group(controller, modifier, source_group=None):
    """Create an isolated recursive node-group graph for one controller."""
    source_group = ensure_user_interface(source_group or load_node_group())
    modifier_sockets = {
        socket.name: socket.identifier for socket in input_sockets(source_group)
    }
    controller_group = _copy_group_graph(
        source_group, controller, modifier, modifier_sockets, copies={}
    )
    modifier.node_group = controller_group
    # Blender 5.2 creates its typed modifier input entries only after the node
    # group is assigned, so driver paths must be finalized at this point.
    for group in controller_group_graph(controller_group):
        relink_group_drivers(
            group, controller, modifier, modifier_sockets
        )
        ensure_direct_output_drivers(
            group, controller, modifier, modifier_sockets
        )
    ensure_modifier_properties(modifier)
    return controller_group


def ensure_controller_node_group(controller, modifier):
    """Migrate a shared/legacy setup or repair targets on an isolated setup."""
    node_group = modifier.node_group
    if (
        not node_group
        or not node_group.get(CONTROLLER_GROUP_TAG)
        or node_group.get(GROUP_GRAPH_VERSION_TAG) != GROUP_GRAPH_VERSION
    ):
        old_group = node_group
        new_group = make_controller_node_group(
            controller, modifier, load_node_group()
        )
        if old_group and old_group.get(CONTROLLER_GROUP_TAG):
            remove_controller_node_groups(old_group)
        ensure_modifier_properties(modifier)
        return new_group

    ensure_user_interface(node_group)
    modifier_sockets = {
        socket.name: socket.identifier for socket in input_sockets(node_group)
    }
    for group in controller_group_graph(node_group):
        group[GROUP_OWNER_TAG] = controller.name
        relink_group_drivers(
            group, controller, modifier, modifier_sockets
        )
        ensure_direct_output_drivers(
            group, controller, modifier, modifier_sockets
        )
    ensure_modifier_properties(modifier)
    return node_group


def controller_group_graph(node_group):
    """Return every private group reachable from a controller's main group."""
    groups = []
    visited = set()

    def visit(group):
        if not group or group in visited or not group.get(CONTROLLER_GROUP_TAG):
            return
        visited.add(group)
        groups.append(group)
        for node in group.nodes:
            visit(getattr(node, "node_tree", None))

    visit(node_group)
    return groups


def remove_controller_node_groups(node_group):
    """Remove private controller trees after their modifier owner has been deleted."""
    if not node_group or not node_group.get(CONTROLLER_GROUP_TAG):
        return
    pending = controller_group_graph(node_group)
    while pending:
        removed_any = False
        for group in list(pending):
            if group.users == 0:
                bpy.data.node_groups.remove(group)
                pending.remove(group)
                removed_any = True
        if not removed_any:
            break
