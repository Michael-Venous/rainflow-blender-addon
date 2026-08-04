# RainFlow Blender Add-on — GPL Source Only

> [!IMPORTANT]
> **This repository is not the complete or installable RainFlow product.** It contains only the GPL-licensed Python integration source and intentionally omits the required RainFlow Geometry Nodes library, example scene, customer documentation, and packaged product. A clone or GitHub-generated ZIP will not function as the full add-on by itself.

## What this repository contains

This repository publishes the Python wrapper used by RainFlow:

- The RainFlow sidebar and artist-facing controls
- Guided creation of non-destructive simulation controllers
- Simulation, static-distribution, and rain-spawner collection management
- Automatic creation of a wireframe spawn plane when no spawner is supplied
- Independent node-tree copies for multiple RainFlow setups
- Driver repair, duplication, selection, and clean removal tools

The Python source is provided under **GPL-3.0-or-later** so it can be inspected, modified, and redistributed under that license.

## What is deliberately missing

The commercial product's required `rainflow/resources/rainflow_library.blend` asset is **not** published here. This repository also excludes:

- The RainFlow Geometry Nodes simulation and its nested node groups
- The installable customer package
- `example.blend`
- Product documentation, renders, and seller materials

The Python wrapper expects a compatible node library at runtime and reports an installation error when that asset is absent. The missing asset is not replaced by the GPL license for this code.

## For customers

Install the complete ZIP supplied through an official RainFlow product download rather than downloading this repository:

- [Purchase on Gumroad](https://venousfx.gumroad.com/l/rainflow)
- [Purchase on Superhive](https://superhivemarket.com/products/rainflow)

RainFlow requires **Blender 5.2 or newer**.

## For developers

You can study or modify the wrapper from this repository. Runtime testing additionally requires a compatible node library that you created or obtained under terms allowing its use:

1. Place it at `rainflow/resources/rainflow_library.blend`.
2. Zip the **contents** of the `rainflow` directory so `blender_manifest.toml` and `__init__.py` are at the ZIP root.
3. In Blender 5.2+, choose **Edit → Preferences → Get Extensions → Install from Disk**.

These steps are for source development and do not recreate the commercial RainFlow node asset.

## License boundary

The Python integration in this repository is GPL-3.0-or-later; see [LICENSE](LICENSE). The separately distributed Geometry Nodes library and other non-code product assets have their own asset license. Nothing in this repository grants rights to assets that are not present here.

## Support development

If this source or RainFlow has helped you, you can support continued development through [Venous FX on Ko-fi](https://ko-fi.com/venous_fx).

For product support, email **the.michael.venous@gmail.com**, message **@MrBullCrap** on Discord, or use the support conversation on the marketplace where you purchased RainFlow. Response time is normally within seven calendar days. Refund requests are governed by the marketplace used for purchase and RainFlow's published 30-day limited refund policy.
