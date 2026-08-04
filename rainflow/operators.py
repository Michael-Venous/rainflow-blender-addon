# Copyright (C) 2026 Venous FX
#
# This file is part of the RainFlow Python integration.
# You may redistribute and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, version 3 or
# (at your option) any later version. It is provided without warranty.
# See the bundled LICENSE file for the complete license.

"""Operators that create, manage, and remove isolated RainFlow setups."""

import bpy
from bpy.app.handlers import persistent
from mathutils import Vector

from .constants import (
    CONTROLLER_TAG,
    SIM_COLLECTION_TAG,
    SPAWNER_COLLECTION_TAG,
    SPAWNER_TAG,
    TARGET_TAG,
)
from .library import (
    ensure_controller_node_group,
    ensure_modifier_properties,
    input_sockets,
    is_rainflow_modifier,
    load_node_group,
    make_controller_node_group,
    modifier_socket_value,
    remove_controller_node_groups,
    set_modifier_socket_value,
)


def _ensure_scene_collection(name, tag):
    collection = bpy.data.collections.new(name)
    collection[tag] = True
    bpy.context.scene.collection.children.link(collection)
    return collection


def _link_once(collection, obj):
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)


def _simulation_meshes(collection):
    """Return meshes in the selected collection and any child collections."""
    return [obj for obj in collection.all_objects if obj.type == 'MESH']


def _collection_world_bounds(collection):
    meshes = _simulation_meshes(collection)
    if not meshes:
        raise ValueError("Simulation Mesh Collection must contain at least one mesh object")
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in meshes
        for corner in obj.bound_box
    ]
    lower = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    upper = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return lower, upper


def _create_spawn_surface(name, simulation_collection, collection):
    lower, upper = _collection_world_bounds(simulation_collection)
    width = max(upper.x - lower.x, 0.1) * 1.5
    depth = max(upper.y - lower.y, 0.1) * 1.5
    z = upper.z + max(upper.z - lower.z, width, depth) * 0.05
    cx, cy = (lower.x + upper.x) / 2, (lower.y + upper.y) / 2
    vertices = [
        (cx - width / 2, cy - depth / 2, z),
        (cx + width / 2, cy - depth / 2, z),
        (cx + width / 2, cy + depth / 2, z),
        (cx - width / 2, cy + depth / 2, z),
    ]
    mesh = bpy.data.meshes.new(f"{name} Mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    surface = bpy.data.objects.new(name, mesh)
    surface[SPAWNER_TAG] = True
    surface.hide_render = True
    surface.display_type = 'WIRE'
    _link_once(collection, surface)
    return surface


def _create_controller(name, simulation_collection, static_collection, spawner_collection):
    mesh = bpy.data.meshes.new(f"{name} Mesh")
    mesh.from_pydata([(0, 0, 0), (0.001, 0, 0), (0, 0.001, 0)], [], [(0, 1, 2)])
    controller = bpy.data.objects.new(name, mesh)
    controller[CONTROLLER_TAG] = True
    controller[TARGET_TAG] = simulation_collection.name
    # The controller carries the generated raindrop geometry, so it must be
    # render-visible by default. The auto-created spawner plane remains hidden
    # from renders above; only that helper surface should be viewport-only.
    controller.hide_render = False
    bpy.context.scene.collection.objects.link(controller)

    modifier = controller.modifiers.new("RainFlow Surface Raindrops", 'NODES')
    make_controller_node_group(controller, modifier, load_node_group())
    for socket in input_sockets(modifier.node_group):
        if socket.name == "hide static in viewport":
            set_modifier_socket_value(modifier, socket.identifier, False)
        elif socket.name == "rain spawner":
            set_modifier_socket_value(
                modifier, socket.identifier, spawner_collection
            )
        elif socket.name == "static distribute mesh":
            set_modifier_socket_value(
                modifier, socket.identifier, static_collection
            )
        elif socket.name == "simulation mesh":
            set_modifier_socket_value(
                modifier, socket.identifier, simulation_collection
            )
    ensure_modifier_properties(modifier, apply_defaults=True)
    return controller


def find_controllers(scene=None):
    scene = scene or bpy.context.scene
    return [obj for obj in scene.objects if obj.get(CONTROLLER_TAG)]


def active_controller(context):
    obj = context.object
    if obj and obj.get(CONTROLLER_TAG):
        return obj
    return None


def _controller_collections(controller):
    """Return collections assigned to RainFlow modifiers on one controller."""
    collections = set()
    for modifier in controller.modifiers:
        if not is_rainflow_modifier(modifier):
            continue
        for socket in input_sockets(modifier.node_group):
            value = modifier_socket_value(modifier, socket.identifier)
            if isinstance(value, bpy.types.Collection):
                collections.add(value)
    return collections


def repair_existing_controllers():
    """Migrate legacy shared groups and restore driver targets after file load."""
    for controller in (obj for obj in bpy.data.objects if obj.get(CONTROLLER_TAG)):
        for modifier in controller.modifiers:
            if is_rainflow_modifier(modifier):
                ensure_controller_node_group(controller, modifier)


@persistent
def _repair_on_load(_unused):
    repair_existing_controllers()


def _repair_after_register():
    try:
        repair_existing_controllers()
    except AttributeError:
        return 0.1
    return None


class RAINFLOW_OT_add_simulation(bpy.types.Operator):
    bl_idname = "rainflow.add_simulation"
    bl_label = "Create RainFlow Simulation"
    bl_description = "Create a non-destructive RainFlow controller from a selected Simulation Mesh Collection"
    bl_options = {'REGISTER', 'UNDO'}

    simulation_collection_name: bpy.props.StringProperty(
        name="Simulation Mesh Collection",
        description="Required collection containing the meshes where raindrops flow",
    )
    static_collection_name: bpy.props.StringProperty(
        name="Static Distribute Collection",
        description="Optional collection for extra static drops; defaults to Simulation Mesh Collection",
    )
    spawner_collection_name: bpy.props.StringProperty(
        name="Rain Spawner Collection",
        description="Optional collection containing rain-spawn surfaces; a wireframe plane is created when empty",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=460)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop_search(
            self, "simulation_collection_name", bpy.data, "collections",
            text="Simulation Mesh Collection",
        )
        layout.prop_search(
            self, "static_collection_name", bpy.data, "collections",
            text="Static Distribute Collection",
        )
        layout.prop_search(
            self, "spawner_collection_name", bpy.data, "collections",
            text="Rain Spawner Collection",
        )
        layout.separator()
        layout.label(text="Simulation Mesh Collection is required.", icon='INFO')
        layout.label(text="Blank optional fields use safe generated defaults.")

    def execute(self, context):
        simulation_collection = bpy.data.collections.get(self.simulation_collection_name)
        if not simulation_collection:
            self.report({'ERROR'}, "Select a Simulation Mesh Collection")
            return {'CANCELLED'}
        if not _simulation_meshes(simulation_collection):
            self.report({'ERROR'}, "Simulation Mesh Collection must contain at least one mesh")
            return {'CANCELLED'}

        static_collection = (
            bpy.data.collections.get(self.static_collection_name)
            if self.static_collection_name else simulation_collection
        )
        if self.static_collection_name and not static_collection:
            self.report({'ERROR'}, "Static Distribute Collection no longer exists")
            return {'CANCELLED'}
        spawner_collection = (
            bpy.data.collections.get(self.spawner_collection_name)
            if self.spawner_collection_name else None
        )
        if self.spawner_collection_name and not spawner_collection:
            self.report({'ERROR'}, "Rain Spawner Collection no longer exists")
            return {'CANCELLED'}
        base_name = f"RainFlow — {simulation_collection.name}"
        if not spawner_collection:
            spawner_collection = _ensure_scene_collection(
                f"{base_name} — Spawners", SPAWNER_COLLECTION_TAG
            )
            _create_spawn_surface(
                f"{base_name} — Spawn Surface", simulation_collection, spawner_collection
            )
        controller = _create_controller(
            f"{base_name} — Controller",
            simulation_collection,
            static_collection,
            spawner_collection,
        )
        context.view_layer.objects.active = controller
        controller.select_set(True)
        self.report({'INFO'}, f"Created RainFlow setup for {simulation_collection.name}")
        return {'FINISHED'}


class RAINFLOW_OT_select_simulation(bpy.types.Operator):
    bl_idname = "rainflow.select_simulation"
    bl_label = "Select RainFlow Setup"
    controller_name: bpy.props.StringProperty()

    def execute(self, context):
        controller = bpy.data.objects.get(self.controller_name)
        if not controller:
            self.report({'ERROR'}, "That RainFlow controller no longer exists")
            return {'CANCELLED'}
        for obj in context.selected_objects:
            obj.select_set(False)
        controller.select_set(True)
        context.view_layer.objects.active = controller
        return {'FINISHED'}


class RAINFLOW_OT_duplicate_simulation(bpy.types.Operator):
    bl_idname = "rainflow.duplicate_simulation"
    bl_label = "Duplicate RainFlow Setup"
    bl_description = "Duplicate the controller and its current settings; configure its collections for a new target"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return active_controller(context) is not None

    def execute(self, context):
        source = active_controller(context)
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.name = f"{source.name} Copy"
        duplicate.data.name = f"{source.data.name} Copy"
        context.scene.collection.objects.link(duplicate)
        for modifier in duplicate.modifiers:
            if is_rainflow_modifier(modifier):
                make_controller_node_group(duplicate, modifier, modifier.node_group)
        for obj in context.selected_objects:
            obj.select_set(False)
        duplicate.select_set(True)
        context.view_layer.objects.active = duplicate
        self.report({'INFO'}, "Duplicated controller. Change the collection inputs before using it on another target.")
        return {'FINISHED'}


class RAINFLOW_OT_remove_simulation(bpy.types.Operator):
    bl_idname = "rainflow.remove_simulation"
    bl_label = "Remove RainFlow Setup"
    bl_description = "Delete this RainFlow controller and its generated spawn plane; source meshes are never deleted"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return active_controller(context) is not None

    def execute(self, context):
        controller = active_controller(context)
        linked_collections = _controller_collections(controller)
        collections_used_elsewhere = set()
        for other_controller in find_controllers(context.scene):
            if other_controller != controller:
                collections_used_elsewhere.update(
                    _controller_collections(other_controller)
                )
        controller_groups = []
        for modifier in controller.modifiers:
            if is_rainflow_modifier(modifier):
                controller_groups.append(modifier.node_group)

        bpy.data.objects.remove(controller, do_unlink=True)
        for node_group in controller_groups:
            remove_controller_node_groups(node_group)
        for collection in linked_collections:
            if collection in collections_used_elsewhere:
                continue
            if collection.get(SPAWNER_COLLECTION_TAG):
                for obj in list(collection.objects):
                    if obj.get(SPAWNER_TAG):
                        bpy.data.objects.remove(obj, do_unlink=True)
            if collection.get(SIM_COLLECTION_TAG):
                for obj in list(collection.objects):
                    collection.objects.unlink(obj)
            if collection.get(SIM_COLLECTION_TAG) or collection.get(SPAWNER_COLLECTION_TAG):
                bpy.data.collections.remove(collection)

        self.report({'INFO'}, "Removed RainFlow setup. Your original source mesh was left untouched.")
        return {'FINISHED'}


class RAINFLOW_OT_open_nodes(bpy.types.Operator):
    bl_idname = "rainflow.open_nodes"
    bl_label = "Open Node Group"
    bl_description = "Open this setup's Geometry Nodes group in the current area when possible"

    @classmethod
    def poll(cls, context):
        return active_controller(context) is not None

    def execute(self, context):
        controller = active_controller(context)
        modifier = next((m for m in controller.modifiers if is_rainflow_modifier(m)), None)
        if not modifier:
            return {'CANCELLED'}
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.spaces.active.tree_type = 'GeometryNodeTree'
                area.spaces.active.geometry_nodes_type = 'MODIFIER'
                area.spaces.active.pin = True
                area.spaces.active.node_tree = modifier.node_group
                self.report({'INFO'}, "Opened RainFlow node group")
                return {'FINISHED'}
        self.report({'WARNING'}, "Open a Geometry Node Editor, then click this button again")
        return {'CANCELLED'}


CLASSES = (
    RAINFLOW_OT_add_simulation,
    RAINFLOW_OT_select_simulation,
    RAINFLOW_OT_duplicate_simulation,
    RAINFLOW_OT_remove_simulation,
    RAINFLOW_OT_open_nodes,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    if _repair_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_repair_on_load)
    if not bpy.app.timers.is_registered(_repair_after_register):
        bpy.app.timers.register(_repair_after_register, first_interval=0.1)


def unregister():
    if _repair_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_repair_on_load)
    if bpy.app.timers.is_registered(_repair_after_register):
        bpy.app.timers.unregister(_repair_after_register)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
