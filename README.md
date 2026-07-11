# RainFlow Blender Add-on

This repository contains the source code for the RainFlow Blender add-on, licensed under **GPL-3.0-or-later**.

RainFlow provides the Blender user interface and non-destructive scene-management workflow around a Geometry Nodes rain system. Artists select a required Simulation Mesh Collection, may select optional Static Distribute and Rain Spawner collections, and control every published input on the attached Geometry Nodes group. Static distribution defaults to the simulation collection; when no spawner is selected, RainFlow generates a correctly sized wireframe plane that is hidden from renders.

## Important: this is source code only

This public repository deliberately does **not** contain `rainflow/resources/rainflow_library.blend`, example scenes, renders, customer packages, or seller documentation. The add-on loads that library at runtime; it is supplied with the separately distributed RainFlow product package.

The source in this repository is complete for the Python add-on wrapper. It can be inspected, modified, and redistributed under the terms of the GPL-3.0-or-later license. Do not assume that the absence of the commercial node-library asset grants a license to that asset.

## Requirements

- Blender 5.1 or newer
- A compatible `rainflow_library.blend` at `rainflow/resources/rainflow_library.blend`

## Install from source

1. Clone or download this repository.
2. Place the compatible node library at `rainflow/resources/rainflow_library.blend`.
3. Zip the `rainflow` directory so that `rainflow/__init__.py` is inside the zip.
4. In Blender, open **Edit → Preferences → Add-ons → Install from Disk**, choose the zip, enable **RainFlow Surface Raindrops**, then open the **RainFlow** tab in the 3D View sidebar.

## License boundary

Blender’s Extensions Platform requires GPL-3.0-or-later for add-ons and CC0 for assets included in an extension. This repository therefore publishes the add-on code under GPL. Before submitting any product that bundles a non-CC0 node library to the official Extensions Platform, confirm the licensing and packaging model with Blender’s current platform requirements or qualified counsel.
