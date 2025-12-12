bl_info = {
    "name": "MUDSTAR LOD Lights",
    "author": "MouMoud-dev",
    "version": (1, 0, 0),
    "blender": (4, 80, 0),
    "location": "View3D > Sidebar > M*LODLights",
    "description": "Edit LOD lights and generate distant LOD lights at export for GTA V",
    "category": "Import-Export",
}

import bpy

# Import modules
from .py import properties
from .py import operators
from .py import ui


# Module classes to register
modules = (
    properties,
    operators,
    ui,
)


def register():
    """Register addon"""
    # Register all modules
    for module in modules:
        module.register()


def unregister():
    """Unregister addon"""
    # Unregister all modules in reverse order
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
