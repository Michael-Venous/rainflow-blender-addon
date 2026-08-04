# Copyright (C) 2026 Venous FX
#
# This file is part of the RainFlow Python integration.
# You may redistribute and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, version 3 or
# (at your option) any later version. It is provided without warranty.
# See the bundled LICENSE file for the complete license.

"""RainFlow Surface Raindrops Blender add-on."""

bl_info = {
    "name": "RainFlow Surface Raindrops",
    "author": "Venous FX",
    "version": (1, 0, 0),
    "blender": (5, 2, 0),
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
