# Copyright (C) 2026 Venous FX
#
# This file is part of the RainFlow Python integration.
# You may redistribute and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, version 3 or
# (at your option) any later version. It is provided without warranty.
# See the bundled LICENSE file for the complete license.

"""3D View sidebar UI for RainFlow."""

import bpy

from .constants import (
    CONTROL_SOCKET_ORDER,
    SETUP_SOCKET_NAMES,
    SOCKET_SLIDERS,
    SOCKET_UI_LABELS,
)
from .library import input_sockets, is_rainflow_modifier, modifier_socket_input
from .operators import active_controller, find_controllers


def _modifier_for(controller):
    return next((m for m in controller.modifiers if is_rainflow_modifier(m)), None)


def _draw_socket(layout, modifier, socket):
    row = layout.row(align=True)
    label = SOCKET_UI_LABELS.get(socket.name, socket.name)
    entry = modifier_socket_input(modifier, socket.identifier)
    if entry:
        row.prop(
            entry, "value", text=label,
            slider=socket.name in SOCKET_SLIDERS,
        )
    else:
        row.prop(
            modifier,
            '["' + socket.identifier + '"]',
            text=label,
            slider=socket.name in SOCKET_SLIDERS,
        )


def _control_sockets(node_group):
    order = {name: index for index, name in enumerate(CONTROL_SOCKET_ORDER)}
    sockets = [
        socket for socket in input_sockets(node_group)
        if socket.name not in SETUP_SOCKET_NAMES
    ]
    return sorted(sockets, key=lambda socket: order.get(socket.name, len(order)))


class RAINFLOW_PT_main(bpy.types.Panel):
    bl_label = "RainFlow Surface Raindrops"
    bl_idname = "RAINFLOW_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RainFlow"

    def draw(self, context):
        layout = self.layout
        controller = active_controller(context)

        if controller:
            layout.label(text="Active setup", icon='GEOMETRY_NODES')
            layout.label(text=controller.name, icon='OBJECT_DATA')
        elif context.scene:
            layout.operator("rainflow.add_simulation", icon='ADD')
        else:
            layout.label(text="Choose a Simulation Mesh Collection to create a setup.", icon='INFO')

        controllers = find_controllers(context.scene)
        if controllers:
            box = layout.box()
            box.label(text=f"Scene setups ({len(controllers)})", icon='OUTLINER_COLLECTION')
            for item in controllers:
                row = box.row(align=True)
                row.operator("rainflow.select_simulation", text=item.name, icon='RESTRICT_SELECT_OFF').controller_name = item.name

        if not controller:
            return

        modifier = _modifier_for(controller)
        if not modifier:
            layout.label(text="RainFlow modifier is missing.", icon='ERROR')
            return

        setup = layout.box()
        setup.label(text="Setup", icon='OUTLINER_COLLECTION')
        for socket in input_sockets(modifier.node_group):
            if socket.name in SETUP_SOCKET_NAMES:
                _draw_socket(setup, modifier, socket)
        setup.operator("rainflow.refresh_parent", icon='CONSTRAINT')
        if controller.parent:
            setup.label(text=f"Follows: {controller.parent.name}", icon='LINKED')
        else:
            setup.label(text="Follows: World Space", icon='WORLD')

        controls = layout.box()
        controls.label(text="Rain Controls", icon='MOD_PHYSICS')
        for socket in _control_sockets(modifier.node_group):
            _draw_socket(controls, modifier, socket)

        row = layout.row(align=True)
        row.operator("rainflow.duplicate_simulation", icon='DUPLICATE')
        row.operator("rainflow.open_nodes", text="Nodes", icon='NODETREE')
        layout.separator()
        layout.operator("rainflow.remove_simulation", icon='TRASH')


CLASSES = (RAINFLOW_PT_main,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
