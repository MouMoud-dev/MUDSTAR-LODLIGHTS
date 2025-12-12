"""Property definitions for MUDSTAR LOD Lights"""

import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
)
from bpy.types import PropertyGroup


class MUDSTAR_PG_LodLightSettings(PropertyGroup):
    """Settings for LOD lights"""
    
    intensity: FloatProperty(
        name="Intensity",
        description="Light intensity for LOD",
        default=1.0,
        min=0.0,
        max=100.0,
    )
    
    color: FloatVectorProperty(
        name="Color",
        description="Light color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
    )
    
    lod_distance: FloatProperty(
        name="LOD Distance",
        description="Distance at which LOD light becomes visible",
        default=100.0,
        min=0.0,
        max=10000.0,
    )
    
    falloff: FloatProperty(
        name="Falloff",
        description="Light falloff value for GTA V",
        default=2.3,
        min=0.0,
        max=100.0,
    )
    
    falloff_exponent: IntProperty(
        name="Falloff Exponent",
        description="Falloff exponent for GTA V",
        default=64,
        min=0,
        max=255,
    )
    
    hash_value: IntProperty(
        name="Hash",
        description="Hash value for GTA V",
        default=0,
        min=-2147483648,
        max=2147483647,
    )
    
    corona_intensity: IntProperty(
        name="Corona Intensity",
        description="Corona intensity for GTA V",
        default=0,
        min=0,
        max=255,
    )
    
    time_and_state_flags: IntProperty(
        name="Time and State Flags",
        description="Time and state flags for GTA V (controls day/night visibility)",
        default=149946431,
        min=0,
    )
    
    enable_lod: BoolProperty(
        name="Enable LOD Light",
        description="Enable LOD light generation for this light",
        default=True,
    )
    
    is_lod_light: BoolProperty(
        name="Is LOD Light",
        description="This is a generated LOD light",
        default=False,
    )


# Registration
classes = (
    MUDSTAR_PG_LodLightSettings,
)


def register():
    """Register property classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add property group to Object
    bpy.types.Object.mudstar_lod_settings = bpy.props.PointerProperty(
        type=MUDSTAR_PG_LodLightSettings
    )


def unregister():
    """Unregister property classes"""
    # Remove property group
    del bpy.types.Object.mudstar_lod_settings
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
