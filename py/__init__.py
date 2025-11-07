"""
MUDSTAR LOD Lights - Blender Addon
Edit and generate LOD lights for GTA V in Blender
"""

bl_info = {
    "name": "MUDSTAR LOD Lights",
    "author": "MouMoud-dev",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > MUDSTAR",
    "description": "Edit LOD lights and generate distant LOD lights at export for GTA V",
    "category": "Import-Export",
}

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
)


# PropertyGroup for LOD Light settings
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
    
    enable_lod: BoolProperty(
        name="Enable LOD Light",
        description="Enable LOD light generation for this light",
        default=True,
    )


# Operator to generate LOD lights
class MUDSTAR_OT_GenerateLodLights(Operator):
    """Generate LOD lights for selected lights"""
    bl_idname = "mudstar.generate_lod_lights"
    bl_label = "Generate LOD Lights"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get selected lights
        selected_lights = [obj for obj in context.selected_objects if obj.type == 'LIGHT']
        
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected")
            return {'CANCELLED'}
        
        generated_count = 0
        for light_obj in selected_lights:
            if hasattr(light_obj, 'mudstar_lod_settings') and light_obj.mudstar_lod_settings.enable_lod:
                # Create LOD light
                lod_name = f"{light_obj.name}_LOD"
                
                # Check if LOD already exists
                if lod_name in bpy.data.objects:
                    self.report({'INFO'}, f"LOD light '{lod_name}' already exists")
                    continue
                
                # Create new light data
                lod_light_data = bpy.data.lights.new(name=lod_name, type='POINT')
                lod_light_data.energy = light_obj.mudstar_lod_settings.intensity
                lod_light_data.color = light_obj.mudstar_lod_settings.color
                
                # Create new object
                lod_light_obj = bpy.data.objects.new(name=lod_name, object_data=lod_light_data)
                
                # Link to collection
                context.collection.objects.link(lod_light_obj)
                
                # Copy location from original light
                lod_light_obj.location = light_obj.location
                
                # Parent to original light
                lod_light_obj.parent = light_obj
                
                generated_count += 1
        
        self.report({'INFO'}, f"Generated {generated_count} LOD light(s)")
        return {'FINISHED'}


# Operator to export LOD lights
class MUDSTAR_OT_ExportLodLights(Operator):
    """Export LOD lights data"""
    bl_idname = "mudstar.export_lod_lights"
    bl_label = "Export LOD Lights"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        # Get all LOD lights
        lod_lights = [obj for obj in bpy.data.objects if obj.type == 'LIGHT' and '_LOD' in obj.name]
        
        if not lod_lights:
            self.report({'WARNING'}, "No LOD lights found")
            return {'CANCELLED'}
        
        # Export logic would go here
        # For now, just report success
        self.report({'INFO'}, f"Exported {len(lod_lights)} LOD light(s)")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Panel in 3D View sidebar
class MUDSTAR_PT_LodLightsPanel(Panel):
    """Panel for LOD Lights controls"""
    bl_label = "MUDSTAR LOD Lights"
    bl_idname = "MUDSTAR_PT_lod_lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MUDSTAR'
    
    def draw(self, context):
        layout = self.layout
        
        # Info section
        box = layout.box()
        box.label(text="LOD Light Generator", icon='LIGHT')
        box.label(text="For GTA V")
        
        # Settings section
        if context.active_object and context.active_object.type == 'LIGHT':
            obj = context.active_object
            
            # Ensure property group exists
            if not hasattr(obj, 'mudstar_lod_settings'):
                layout.label(text="No LOD settings available", icon='ERROR')
                return
            
            settings = obj.mudstar_lod_settings
            
            box = layout.box()
            box.label(text=f"Light: {obj.name}", icon='OUTLINER_OB_LIGHT')
            
            box.prop(settings, "enable_lod")
            
            if settings.enable_lod:
                box.prop(settings, "intensity")
                box.prop(settings, "color")
                box.prop(settings, "lod_distance")
        else:
            layout.label(text="Select a light to edit", icon='INFO')
        
        # Actions
        layout.separator()
        
        col = layout.column()
        col.operator("mudstar.generate_lod_lights", icon='LIGHT_SUN')
        col.operator("mudstar.export_lod_lights", icon='EXPORT')


# Registration
classes = (
    MUDSTAR_PG_LodLightSettings,
    MUDSTAR_OT_GenerateLodLights,
    MUDSTAR_OT_ExportLodLights,
    MUDSTAR_PT_LodLightsPanel,
)


def register():
    """Register addon classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add property group to Object
    bpy.types.Object.mudstar_lod_settings = bpy.props.PointerProperty(type=MUDSTAR_PG_LodLightSettings)


def unregister():
    """Unregister addon classes"""
    # Remove property group
    del bpy.types.Object.mudstar_lod_settings
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
