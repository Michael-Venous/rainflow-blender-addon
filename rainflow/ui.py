"""3D View sidebar UI for RainFlow."""

import bpy

from .constants import SETUP_SOCKET_NAMES
from .library import input_sockets, is_rainflow_modifier, socket_tooltip
from .operators import active_controller, find_controllers


def _modifier_for(controller):
    return next((m for m in controller.modifiers if is_rainflow_modifier(m)), None)


def _draw_socket(layout, modifier, socket):
    row = layout.row(align=True)
    row.prop(modifier, '["' + socket.identifier + '"]', text=socket.name)
    tooltip = socket_tooltip(socket)
    if tooltip:
        row.label(text="", icon='QUESTION')
        row.active = True
        row.alert = False
        row.operator_context = 'INVOKE_DEFAULT'


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
            layout.label(text="Active setup", icon='MOD_NODES')
            layout.label(text=controller.name, icon='OBJECT_DATA')
        elif context.active_object and context.active_object.type == 'MESH':
            layout.operator("rainflow.add_simulation", icon='ADD')
        else:
            layout.label(text="Select a mesh to create a setup.", icon='INFO')

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

        controls = layout.box()
        controls.label(text="Rain Controls", icon='MOD_PHYSICS')
        for socket in input_sockets(modifier.node_group):
            if socket.name not in SETUP_SOCKET_NAMES:
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
