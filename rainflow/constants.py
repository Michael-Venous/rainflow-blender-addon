ADDON_ID = "rainflow"
VERSION = "1.0.0"
LIBRARY_GROUP_NAME = "raindrop"
LIBRARY_TAG = "rainflow_library_version"
LIBRARY_SOURCE_TAG = "rainflow_library_source"
CONTROLLER_TAG = "rainflow_controller"
CONTROLLER_GROUP_TAG = "rainflow_controller_node_group"
GROUP_OWNER_TAG = "rainflow_group_owner"
GROUP_GRAPH_VERSION_TAG = "rainflow_group_graph_version"
GROUP_GRAPH_VERSION = 3
TARGET_TAG = "rainflow_target"
SIM_COLLECTION_TAG = "rainflow_simulation_collection"
SPAWNER_COLLECTION_TAG = "rainflow_spawner_collection"
SPAWNER_TAG = "rainflow_spawn_surface"

# Product defaults applied to every newly created RainFlow modifier. These are
# intentionally stored in the add-on instead of relying on mutable node-group
# interface defaults in the source .blend.
DEFAULT_SOCKET_VALUES = {
    "rain vector": (0.0, 0.0, -1.0),
    "speed": 1.0,
    "rain lifetime": 20.0,
    "iterations": 1,
    "density": 50.0,
    "density static": 100.0,
    "lifetime": 8.0,
    "adhesion": 0.5,
    "noise scale": 0.03,
    "direction vector": (0.0, 0.0, -0.1),
    "wind factor": 2.0,
    "size": 2.0,
    "mesh detail": 1,
}

SOCKET_NAME_ALIASES = {
    "adhesion (inverted)": "adhesion",
}

# Inputs introduced by the add-on around the authored node graph. Keeping this
# migration here lets older saved setups acquire new controls without changing
# any existing socket identifiers.
REQUIRED_INPUT_SOCKETS = {
    "rain lifetime": {
        "socket_type": "NodeSocketFloat",
        "default": DEFAULT_SOCKET_VALUES["rain lifetime"],
        "min": 0.0,
        "soft_max": 250.0,
    },
    "iterations": {
        "socket_type": "NodeSocketInt",
        "default": DEFAULT_SOCKET_VALUES["iterations"],
        "min": 1,
        "soft_max": 64,
    },
    "density static": {
        "socket_type": "NodeSocketFloat",
        "default": DEFAULT_SOCKET_VALUES["density static"],
        "min": 0.0,
        "soft_max": 250.0,
    },
}

# Direct output bindings used by the streamlined controls/post node groups.
CONTROL_OUTPUT_BINDINGS = {
    "rain_speed": "rain vector",
    "rain_lifetime": "rain lifetime",
    "density": "density",
    "max age": "lifetime",
    "adhesion": "adhesion",
    "noise scale": "noise scale",
    "direction vector": "direction vector",
    "wind factor": "wind factor",
}
POST_OUTPUT_BINDINGS = {
    "size": "size",
    "detail": "mesh detail",
    "density static": "density static",
}

# These descriptions make the current clean control frame readable to artists.
# The UI remains data-driven: any future published socket still appears.
SOCKET_HELP = {
    "hide static in viewport": "Hide extra static droplets in the viewport while keeping them visible in final renders.",
    "rain spawner": "Collection containing the surfaces that emit falling rain.",
    "static distribute mesh": "Collection whose surfaces receive extra non-moving droplets. Defaults to the simulation collection.",
    "simulation mesh": "Collection containing the mesh surfaces that the animated droplets move across.",
    "rain vector": "World-space direction of the falling rain. Its length also affects the initial rain velocity.",
    "speed": "Overall movement-speed multiplier for droplets flowing across the surface.",
    "rain lifetime": "Maximum lifetime of falling rain before it is removed from the simulation.",
    "iterations": "Number of simulation steps evaluated per frame. More steps can improve stability but take longer to calculate.",
    "density": "Amount of falling rain generated across the spawner surfaces.",
    "density static": "Amount of non-moving droplets distributed across the static surfaces.",
    "lifetime": "Maximum age of droplets after they reach the simulation surface.",
    "adhesion": "How sticky the droplets are and how strongly they resist moving. 0 moves freely; 1 is most adhesive.",
    "noise scale": "Scale of the procedural variation that breaks up uniform droplet flow.",
    "direction vector": "World-space direction used by wind to push droplets across the surface.",
    "wind factor": "Multiplier for wind-driven motion. Higher values push droplets more strongly along the Direction Vector, especially on surfaces facing into it.",
    "size": "Scale of the rendered raindrop geometry.",
    "mesh detail": "Geometry detail level of the rendered droplets. Higher values produce smoother drops and use more geometry.",
}

SOCKET_UI_RANGES = {
    "adhesion": (0.0, 1.0),
    "rain lifetime": (0.0, 100000.0),
    "iterations": (1, 1000000),
}

SOCKET_UI_LABELS = {
    "adhesion": "Adhesion",
    "rain lifetime": "Rain Lifetime",
}

SOCKET_SLIDERS = {
    "adhesion",
}

CONTROL_SOCKET_ORDER = (
    "rain vector",
    "speed",
    "rain lifetime",
    "iterations",
    "density",
    "density static",
    "lifetime",
    "adhesion",
    "noise scale",
    "direction vector",
    "wind factor",
    "size",
    "mesh detail",
)

SETUP_SOCKET_NAMES = {
    "hide static in viewport",
    "rain spawner",
    "static distribute mesh",
    "simulation mesh",
}
