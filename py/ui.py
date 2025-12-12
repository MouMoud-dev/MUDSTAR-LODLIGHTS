"""User interface for MUDSTAR LOD Lights"""

import bpy
from bpy.types import Panel


class MUDSTAR_PT_LodLightsPanel(Panel):
    """Main panel for M*LODLights"""
    bl_label = "M*LODLights"
    bl_idname = "MUDSTAR_PT_lod_lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'M*LODLights'
    
    def draw(self, context):
        layout = self.layout
        
        # Info section
        box = layout.box()
        box.label(text="LOD Light Tools", icon='LIGHT')
        box.label(text="For GTA V", icon='INFO')
        
        # Active object info
        if context.active_object and context.active_object.type == 'LIGHT':
            self._draw_light_info(context, layout)
        else:
            layout.label(text="Select a light to view info", icon='INFO')
        
        # Actions
        layout.separator()
        self._draw_actions(layout)
    
    def _draw_light_info(self, context, layout):
        """Draw information about the active light"""
        obj = context.active_object
        
        box = layout.box()
        box.label(text=f"Light: {obj.name}", icon='OUTLINER_OB_LIGHT')
        
        # Check if LOD light
        is_lod = obj.get("is_lod_light", False)
        if is_lod:
            box.label(text="✓ LOD Light", icon='CHECKMARK')
        else:
            box.label(text="Not a LOD Light", icon='X')
        
        # Blender properties
        box.separator()
        box.label(text="Blender Properties:")
        row = box.row()
        row.prop(obj.data, "energy", text="Intensity")
        row = box.row()
        row.prop(obj.data, "color", text="Color")
        
        # GTA V properties (if LOD light)
        if is_lod:
            box.separator()
            box.label(text="GTA V Properties:")
            
            falloff = obj.get("gta_falloff", 0)
            box.label(text=f"Falloff: {falloff:.2f}")
            
            falloff_exp = obj.get("gta_falloff_exponent", 64)
            box.label(text=f"Falloff Exponent: {falloff_exp}")
            
            corona = obj.get("gta_corona_intensity", 0)
            box.label(text=f"Corona Intensity: {corona}")
            
            time_flags = obj.get("gta_time_flags", 149946431)
            box.label(text=f"Time Flags: {time_flags}")
            
            hash_val = obj.get("gta_hash", "")
            box.label(text=f"Hash: {hash_val}")
    
    def _draw_actions(self, layout):
        """Draw action buttons"""
        box = layout.box()
        box.label(text="Import/Export", icon='FILEBROWSER')
        
        col = box.column(align=True)
        col.operator("mudstar.import_lod_lights", text="Import", icon='IMPORT')
        col.operator("mudstar.export_lod_lights", text="Export", icon='EXPORT')
        
        # Stats
        lod_count = sum(1 for obj in bpy.data.objects 
                       if obj.type == 'LIGHT' and obj.get("is_lod_light", False))
        
        if lod_count > 0:
            layout.separator()
            info_box = layout.box()
            info_box.label(text=f"Total LOD Lights: {lod_count}", icon='LIGHT_DATA')


# Registration
classes = (
    MUDSTAR_PT_LodLightsPanel,
)


def register():
    """Register UI classes"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister UI classes"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
