ADDON_ID = "rainflow"
VERSION = "1.0.0"
LIBRARY_GROUP_NAME = "raindrop"
LIBRARY_TAG = "rainflow_library_version"
CONTROLLER_TAG = "rainflow_controller"
TARGET_TAG = "rainflow_target"
SIM_COLLECTION_TAG = "rainflow_simulation_collection"
SPAWNER_COLLECTION_TAG = "rainflow_spawner_collection"
SPAWNER_TAG = "rainflow_spawn_surface"

# Product defaults applied to every newly created RainFlow modifier. These are
# intentionally stored in the add-on instead of relying on mutable node-group
# interface defaults in the source .blend.
DEFAULT_SOCKET_VALUES = {
    "rain vector": (0.0, 0.0, -0.01),
    "speed": 1.0,
    "iterations": 1.0,
    "density": 1.0,
    "lifetime": 18.0,
    "adhesion (inverted)": 1.0,
    "noise scale": 0.03,
    "direction vector": (0.0, 0.0, -0.1),
    "wind factor": 2.0,
    "size": 8.0,
    "mesh detail": 1,
}

# These descriptions make the current clean control frame readable to artists.
# The UI remains data-driven: any future published socket still appears.
SOCKET_HELP = {
    "hide static in viewport": "Hide the static/distribution geometry in the viewport while keeping the rain result visible.",
    "rain spawner": "Collection containing the spawn surface or rain emitters.",
    "static distribute mesh": "Collection used when distributing the static rain state.",
    "simulation mesh": "Collection of meshes the raindrops flow across.",
    "rain vector": "Initial world-space rain direction.",
    "speed": "Overall rain-flow speed.",
    "iterations": "Simulation iterations per frame. Higher values can improve stability at a performance cost.",
    "density": "Amount of rain generated across the spawn surface.",
    "lifetime": "How long each generated droplet remains in the simulation.",
    "adhesion (inverted)": "Inverse surface adhesion. Tune it to control how readily drops move across the mesh.",
    "noise scale": "Scale of the variation used to break up uniform flow.",
    "direction vector": "World-space direction used to steer flow across the surface.",
    "wind factor": "Strength of wind influence on the droplets.",
    "size": "Raindrop size.",
    "mesh detail": "Detail level used when creating the visible droplet mesh.",
}

SETUP_SOCKET_NAMES = {
    "hide static in viewport",
    "rain spawner",
    "static distribute mesh",
    "simulation mesh",
}
