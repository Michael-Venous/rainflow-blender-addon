"""Operators that create, manage, and remove isolated RainFlow setups."""

import bpy
from mathutils import Vector

from .constants import (
    CONTROLLER_TAG,
    SIM_COLLECTION_TAG,
    SPAWNER_COLLECTION_TAG,
    SPAWNER_TAG,
    TARGET_TAG,
    VERSION,
)
from .library import input_sockets, is_rainflow_modifier, load_node_group


def _ensure_scene_collection(name, tag):
    collection = bpy.data.collections.new(name)
    collection[tag] = True
    bpy.context.scene.collection.children.link(collection)
    return collection


def _link_once(collection, obj):
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)


def _world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    upper = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return lower, upper


def _create_spawn_surface(name, target, collection):
    lower, upper = _world_bounds(target)
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


def _create_controller(name, target, sim_collection, spawner_collection):
    mesh = bpy.data.meshes.new(f"{name} Mesh")
    mesh.from_pydata([(0, 0, 0), (0.001, 0, 0), (0, 0.001, 0)], [], [(0, 1, 2)])
    controller = bpy.data.objects.new(name, mesh)
    controller[CONTROLLER_TAG] = True
    controller[TARGET_TAG] = target.name
    controller.hide_render = True
    bpy.context.scene.collection.objects.link(controller)

    modifier = controller.modifiers.new("RainFlow Surface Raindrops", 'NODES')
    modifier.node_group = load_node_group()
    for socket in input_sockets(modifier.node_group):
        if socket.name == "hide static in viewport":
            modifier[socket.identifier] = True
        elif socket.name == "rain spawner":
            modifier[socket.identifier] = spawner_collection
        elif socket.name in {"static distribute mesh", "simulation mesh"}:
            modifier[socket.identifier] = sim_collection
    return controller


def find_controllers(scene=None):
    scene = scene or bpy.context.scene
    return [obj for obj in scene.objects if obj.get(CONTROLLER_TAG)]


def active_controller(context):
    obj = context.object
    if obj and obj.get(CONTROLLER_TAG):
        return obj
    return None


class RAINFLOW_OT_add_simulation(bpy.types.Operator):
    bl_idname = "rainflow.add_simulation"
    bl_label = "Add RainFlow to Selected Mesh"
    bl_description = "Create a non-destructive RainFlow controller and collections for the selected mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        target = context.active_object
        base_name = f"RainFlow — {target.name}"
        sim_collection = _ensure_scene_collection(f"{base_name} — Simulation", SIM_COLLECTION_TAG)
        spawner_collection = _ensure_scene_collection(f"{base_name} — Spawners", SPAWNER_COLLECTION_TAG)
        _link_once(sim_collection, target)
        _create_spawn_surface(f"{base_name} — Spawn Surface", target, spawner_collection)
        controller = _create_controller(f"{base_name} — Controller", target, sim_collection, spawner_collection)
        context.view_layer.objects.active = controller
        controller.select_set(True)
        self.report({'INFO'}, f"Created RainFlow setup for {target.name}")
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
        linked_collections = set()
        for modifier in controller.modifiers:
            if is_rainflow_modifier(modifier):
                for socket in input_sockets(modifier.node_group):
                    value = modifier.get(socket.identifier)
                    if isinstance(value, bpy.types.Collection):
                        linked_collections.add(value)

        bpy.data.objects.remove(controller, do_unlink=True)
        for collection in linked_collections:
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


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
