"""RainFlow Surface Raindrops Blender add-on."""

bl_info = {
    "name": "RainFlow Surface Raindrops",
    "author": "RainFlow",
    "version": (1, 0, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > RainFlow",
    "description": "Create and manage animated Geometry Nodes raindrop simulations",
    "category": "Object",
}

from . import operators, ui


MODULES = (operators, ui)


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
