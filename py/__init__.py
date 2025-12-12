bl_info = {
    "name": "MUDSTAR LOD Lights",
    "author": "MouMoud-dev",
    "version": (1, 0, 0),
    "blender": (4, 80, 0),
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
    IntProperty,
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


# Operator to import LOD lights
class MUDSTAR_OT_ImportLodLights(Operator):
    """Import LOD lights from file"""
    bl_idname = "mudstar.import_lod_lights"
    bl_label = "Import LOD Lights"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.ymap.xml;*.xml;*.json', options={'HIDDEN'})
    
    def execute(self, context):
        import json
        import os
        import xml.etree.ElementTree as ET
        
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        
        try:
            # Import logic based on file extension
            ext = os.path.splitext(self.filepath)[1].lower()
            imported_count = 0
            
            # Get filename without extension for collection name
            filename = os.path.splitext(os.path.basename(self.filepath))[0]
            # Remove .ymap if present
            if filename.endswith('.ymap'):
                filename = filename[:-5]
            
            # Create or get collection
            if filename in bpy.data.collections:
                collection = bpy.data.collections[filename]
            else:
                collection = bpy.data.collections.new(filename)
                context.scene.collection.children.link(collection)
            
            if ext == '.xml':
                # Parse GTA V ymap.xml format
                tree = ET.parse(self.filepath)
                root = tree.getroot()
                
                # Check if this has LODLights or DistantLODLights with data
                lod_lights_soa = root.find('.//LODLightsSOA')
                distant_soa = root.find('.//DistantLODLightsSOA')
                
                # Try to load positions from parent file if exists
                positions_list = []
                rgbi_list = []
                parent_name = root.find('.//parent')
                
                if parent_name is not None and parent_name.text:
                    # Try to find parent file
                    parent_filename = parent_name.text + '.ymap.xml'
                    parent_path = os.path.join(os.path.dirname(self.filepath), parent_filename)
                    
                    if os.path.exists(parent_path):
                        try:
                            parent_tree = ET.parse(parent_path)
                            parent_root = parent_tree.getroot()
                            parent_distant_soa = parent_root.find('.//DistantLODLightsSOA')
                            
                            if parent_distant_soa is not None:
                                positions = parent_distant_soa.find('position')
                                rgbi = parent_distant_soa.find('RGBI')
                                
                                if positions is not None:
                                    positions_list = positions.findall('Item')
                                if rgbi is not None and rgbi.text:
                                    rgbi_list = [int(v) for v in rgbi.text.strip().split()]
                                
                                print(f"Loaded {len(positions_list)} positions from parent file: {parent_filename}")
                        except Exception as e:
                            print(f"Error loading parent file: {e}")
                    else:
                        print(f"Parent file not found: {parent_path}")
                
                # Also check current file for distant positions
                if not positions_list and distant_soa is not None:
                    positions = distant_soa.find('position')
                    rgbi = distant_soa.find('RGBI')
                    
                    if positions is not None:
                        positions_list = positions.findall('Item')
                    if rgbi is not None and rgbi.text:
                        rgbi_list = [int(v) for v in rgbi.text.strip().split()]
                
                # Find LODLightsSOA section
                if lod_lights_soa is None:
                    self.report({'ERROR'}, "No LODLightsSOA section found in XML")
                    return {'CANCELLED'}
                
                # Parse light data
                directions = lod_lights_soa.find('direction')
                hashes = lod_lights_soa.find('hash')
                falloffs = lod_lights_soa.find('falloff')
                falloff_exponents = lod_lights_soa.find('falloffExponent')
                cone_inner = lod_lights_soa.find('coneInnerAngle')
                cone_outer = lod_lights_soa.find('coneOuterAngleOrCapExt')
                corona_intensity = lod_lights_soa.find('coronaIntensity')
                time_flags = lod_lights_soa.find('timeAndStateFlags')
                
                if directions is None or hashes is None:
                    self.report({'ERROR'}, "Missing required LOD light data")
                    return {'CANCELLED'}
                
                # Get number of lights
                direction_items = directions.findall('Item')
                hash_values = hashes.text.strip().split() if hashes.text else []
                
                # Falloff values (can have commas as decimal separators)
                falloff_values = []
                if falloffs is not None and falloffs.text:
                    for v in falloffs.text.strip().split():
                        falloff_values.append(float(v.replace(',', '.')))
                
                # Falloff exponent values (integers only)
                falloff_exp_values = []
                if falloff_exponents is not None and falloff_exponents.text:
                    for v in falloff_exponents.text.strip().split():
                        falloff_exp_values.append(int(float(v.replace(',', '.'))))
                
                # Cone angles (integers)
                cone_inner_values = []
                if cone_inner is not None and cone_inner.text:
                    for v in cone_inner.text.strip().split():
                        cone_inner_values.append(int(float(v.replace(',', '.'))))
                
                cone_outer_values = []
                if cone_outer is not None and cone_outer.text:
                    for v in cone_outer.text.strip().split():
                        cone_outer_values.append(int(float(v.replace(',', '.'))))
                
                # Corona and time flags (integers)
                corona_values = []
                if corona_intensity is not None and corona_intensity.text:
                    for v in corona_intensity.text.strip().split():
                        corona_values.append(int(float(v.replace(',', '.'))))
                
                time_flag_values = []
                if time_flags is not None and time_flags.text:
                    for v in time_flags.text.strip().split():
                        time_flag_values.append(int(v))
                
                # Get entitiesExtentsMin for position offset
                extents_min = root.find('.//entitiesExtentsMin')
                extents_max = root.find('.//entitiesExtentsMax')
                
                offset_x = 0.0
                offset_y = 0.0
                offset_z = 0.0
                
                if extents_min is not None and extents_max is not None:
                    min_x = float(extents_min.get('x', 0))
                    min_y = float(extents_min.get('y', 0))
                    min_z = float(extents_min.get('z', 0))
                    max_x = float(extents_max.get('x', 0))
                    max_y = float(extents_max.get('y', 0))
                    max_z = float(extents_max.get('z', 0))
                    
                    # Use center of bounds as base offset
                    offset_x = (min_x + max_x) / 2.0
                    offset_y = (min_y + max_y) / 2.0
                    offset_z = (min_z + max_z) / 2.0
                
                # Create lights
                for i, direction_item in enumerate(direction_items):
                    # Get direction values
                    dir_x = float(direction_item.find('x').get('value', 0))
                    dir_y = float(direction_item.find('y').get('value', 0))
                    dir_z = float(direction_item.find('z').get('value', 0))
                    
                    # Get hash for name
                    hash_val = hash_values[i] if i < len(hash_values) else str(i)
                    light_name = f"LOD_Light_{hash_val}"
                    
                    # Convert hash to signed int32 for Blender (handles unsigned values)
                    hash_int = int(hash_val)
                    if hash_int > 2147483647:  # If unsigned value > max signed int
                        hash_int = hash_int - 4294967296  # Convert to signed
                    
                    # Get falloff (intensity)
                    falloff = falloff_values[i] if i < len(falloff_values) else 2.3
                    
                    # Get falloff exponent
                    falloff_exp = falloff_exp_values[i] if i < len(falloff_exp_values) else 64
                    
                    # Get corona
                    corona = corona_values[i] if i < len(corona_values) else 0
                    
                    # Get time flags
                    time_flag = time_flag_values[i] if i < len(time_flag_values) else 149946431
                    
                    # Get color from RGBI if available
                    color = (1.0, 1.0, 1.0)
                    if i < len(rgbi_list):
                        rgbi = rgbi_list[i]
                        r = ((rgbi >> 24) & 0xFF) / 255.0
                        g = ((rgbi >> 16) & 0xFF) / 255.0
                        b = ((rgbi >> 8) & 0xFF) / 255.0
                        color = (r, g, b)
                    
                    # Get cone angles (for spot lights)
                    inner_angle = cone_inner_values[i] if i < len(cone_inner_values) else 14
                    outer_angle = cone_outer_values[i] if i < len(cone_outer_values) else 35
                    
                    # Determine light type based on cone angles
                    if inner_angle > 14 or outer_angle > 35:
                        light_type = 'SPOT'
                    else:
                        light_type = 'POINT'
                    
                    # Create new light data
                    lod_light_data = bpy.data.lights.new(name=light_name, type=light_type)
                    lod_light_data.energy = falloff
                    lod_light_data.color = color
                    
                    if light_type == 'SPOT':
                        import math
                        lod_light_data.spot_size = math.radians(outer_angle)
                        lod_light_data.spot_blend = (outer_angle - inner_angle) / outer_angle if outer_angle > 0 else 0.5
                    
                    # Create new object
                    lod_light_obj = bpy.data.objects.new(name=light_name, object_data=lod_light_data)
                    
                    # Save all GTA V properties as custom properties
                    lod_light_obj["is_lod_light"] = True
                    lod_light_obj["gta_falloff"] = falloff
                    lod_light_obj["gta_falloff_exponent"] = falloff_exp
                    lod_light_obj["gta_hash"] = hash_val  # Store as string to avoid int overflow
                    lod_light_obj["gta_corona_intensity"] = corona
                    lod_light_obj["gta_time_flags"] = time_flag
                    
                    # Link to collection
                    collection.objects.link(lod_light_obj)
                    
                    # Set location from positions if available, otherwise use extents
                    if i < len(positions_list):
                        pos_item = positions_list[i]
                        pos_x = float(pos_item.find('x').get('value', 0))
                        pos_y = float(pos_item.find('y').get('value', 0))
                        pos_z = float(pos_item.find('z').get('value', 0))
                        lod_light_obj.location = (pos_x, pos_y, pos_z)
                    else:
                        # Fallback: spread lights around center
                        spread = 5.0
                        lod_light_obj.location = (
                            offset_x + (i % 10) * spread,
                            offset_y + (i // 10) * spread,
                            offset_z
                        )
                    
                    # Set rotation based on direction
                    if dir_x != 0 or dir_y != 0 or dir_z != 0:
                        import math
                        from mathutils import Vector, Quaternion
                        
                        direction = Vector((dir_x, dir_y, dir_z)).normalized()
                        # Calculate rotation to point in direction
                        up = Vector((0, 0, -1))
                        if direction.length > 0:
                            rotation = up.rotation_difference(direction)
                            lod_light_obj.rotation_euler = rotation.to_euler()
                    
                    imported_count += 1
                
                self.report({'INFO'}, f"Imported {imported_count} LOD light(s) from GTA V ymap")
                
            elif ext == '.json':
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                
                for light_data in data.get('lights', []):
                    # Create new light data
                    light_name = light_data.get('name', 'LOD_Light')
                    lod_light_data = bpy.data.lights.new(name=light_name, type='POINT')
                    lod_light_data.energy = light_data.get('intensity', 1.0)
                    lod_light_data.color = light_data.get('color', [1.0, 1.0, 1.0])
                    
                    # Create new object
                    lod_light_obj = bpy.data.objects.new(name=light_name, object_data=lod_light_data)
                    
                    # Mark as LOD light
                    lod_light_obj.mudstar_lod_settings.is_lod_light = True
                    lod_light_obj.mudstar_lod_settings.intensity = light_data.get('intensity', 1.0)
                    lod_light_obj.mudstar_lod_settings.lod_distance = light_data.get('lod_distance', 100.0)
                    
                    # Link to collection
                    collection.objects.link(lod_light_obj)
                    
                    # Set location
                    lod_light_obj.location = light_data.get('location', [0.0, 0.0, 0.0])
                    
                    imported_count += 1
                
                self.report({'INFO'}, f"Imported {imported_count} LOD light(s)")
            else:
                self.report({'ERROR'}, "Unsupported file format. Use .ymap.xml or .json")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Operator to export LOD lights
class MUDSTAR_OT_ExportLodLights(Operator):
    """Export LOD lights data"""
    bl_idname = "mudstar.export_lod_lights"
    bl_label = "Export LOD Lights"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.ymap.xml', options={'HIDDEN'})
    
    def execute(self, context):
        import os
        import math
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        # Get all LOD lights using the custom property
        lod_lights = [obj for obj in bpy.data.objects 
                     if obj.type == 'LIGHT' and 
                     obj.get("is_lod_light", False)]
        
        if not lod_lights:
            self.report({'WARNING'}, "No LOD lights found to export. Import a ymap first or mark lights as LOD lights.")
            return {'CANCELLED'}
        
        if not self.filepath:
            self.report({'ERROR'}, "No file path specified")
            return {'CANCELLED'}
        
        try:
            # Get collection name from first LOD light
            collection_name = None
            for light in lod_lights:
                for coll in light.users_collection:
                    if coll.name and coll.name != 'Scene Collection':
                        collection_name = coll.name
                        break
                if collection_name:
                    break
            
            # If no collection name found, try to extract from filepath
            if not collection_name:
                base_filename = os.path.basename(self.filepath)
                if base_filename and base_filename != '.ymap.xml':
                    collection_name = os.path.splitext(base_filename)[0]
                    if collection_name.endswith('.ymap'):
                        collection_name = collection_name[:-5]
            
            # Fallback to generic name
            if not collection_name or collection_name == '':
                collection_name = 'export'
            
            # Generate filenames based on collection name
            # If collection name already contains 'lodlights', use it as is
            if 'lodlights' in collection_name.lower():
                lodlights_name = collection_name
            else:
                lodlights_name = collection_name + '_lodlights'
            
            # Generate distant name
            if 'lodlights' in lodlights_name:
                distant_name = lodlights_name.replace('lodlights', 'distlodlights')
            else:
                distant_name = lodlights_name + '_distlodlights'
            
            # Construct full paths
            directory = os.path.dirname(self.filepath) if self.filepath else ''
            if not directory:
                directory = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
            
            lodlights_path = os.path.join(directory, lodlights_name + '.ymap.xml')
            distant_path = os.path.join(directory, distant_name + '.ymap.xml')
            
            # Calculate extents
            min_x = min(light.location.x for light in lod_lights)
            min_y = min(light.location.y for light in lod_lights)
            min_z = min(light.location.z for light in lod_lights)
            max_x = max(light.location.x for light in lod_lights)
            max_y = max(light.location.y for light in lod_lights)
            max_z = max(light.location.z for light in lod_lights)
            
            # Add margin for streaming extents
            margin = 2000.0
            stream_min_x = min_x - margin
            stream_min_y = min_y - margin
            stream_min_z = min_z - margin
            stream_max_x = max_x + margin
            stream_max_y = max_y + margin
            stream_max_z = max_z + margin
            
            # Export LOD lights file
            self._export_lodlights(lodlights_path, lodlights_name, distant_name, lod_lights,
                                  stream_min_x, stream_min_y, stream_min_z,
                                  stream_max_x, stream_max_y, stream_max_z,
                                  min_x, min_y, min_z, max_x, max_y, max_z)
            
            # Export Distant LOD lights file
            self._export_distant_lodlights(distant_path, distant_name, lod_lights,
                                          stream_min_x, stream_min_y, stream_min_z,
                                          stream_max_x, stream_max_y, stream_max_z,
                                          min_x, min_y, min_z, max_x, max_y, max_z)
            
            self.report({'INFO'}, f"Exported {len(lod_lights)} LOD light(s) to:\n- {os.path.basename(lodlights_path)}\n- {os.path.basename(distant_path)}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def _export_lodlights(self, filepath, name, parent, lights, 
                         stream_min_x, stream_min_y, stream_min_z,
                         stream_max_x, stream_max_y, stream_max_z,
                         min_x, min_y, min_z, max_x, max_y, max_z):
        """Export LOD lights ymap file"""
        import math
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        root = ET.Element('CMapData')
        
        # Header
        ET.SubElement(root, 'name').text = name
        ET.SubElement(root, 'parent').text = parent
        ET.SubElement(root, 'flags', value='1')
        ET.SubElement(root, 'contentFlags', value='128')
        
        # Streaming extents
        ET.SubElement(root, 'streamingExtentsMin', 
                     x=f'{stream_min_x:.6g}', y=f'{stream_min_y:.6g}', z=f'{stream_min_z:.6g}')
        ET.SubElement(root, 'streamingExtentsMax',
                     x=f'{stream_max_x:.6g}', y=f'{stream_max_y:.6g}', z=f'{stream_max_z:.6g}')
        ET.SubElement(root, 'entitiesExtentsMin',
                     x=f'{min_x:.6g}', y=f'{min_y:.6g}', z=f'{min_z:.6g}')
        ET.SubElement(root, 'entitiesExtentsMax',
                     x=f'{max_x:.6g}', y=f'{max_y:.6g}', z=f'{max_z:.6g}')
        
        # Empty sections
        ET.SubElement(root, 'entities')
        ET.SubElement(root, 'containerLods', itemType='rage__fwContainerLodDef')
        ET.SubElement(root, 'boxOccluders', itemType='BoxOccluder')
        ET.SubElement(root, 'occludeModels', itemType='OccludeModel')
        ET.SubElement(root, 'physicsDictionaries')
        
        # Instance data
        instance_data = ET.SubElement(root, 'instancedData')
        ET.SubElement(instance_data, 'ImapLink')
        ET.SubElement(instance_data, 'PropInstanceList', itemType='rage__fwPropInstanceListDef')
        ET.SubElement(instance_data, 'GrassInstanceList', itemType='rage__fwGrassInstanceListDef')
        
        ET.SubElement(root, 'timeCycleModifiers', itemType='CTimeCycleModifier')
        ET.SubElement(root, 'carGenerators', itemType='CCarGen')
        
        # LODLightsSOA
        lod_lights_soa = ET.SubElement(root, 'LODLightsSOA')
        
        # Direction
        direction = ET.SubElement(lod_lights_soa, 'direction', itemType='FloatXYZ')
        for light in lights:
            item = ET.SubElement(direction, 'Item')
            # Get light direction from rotation
            rotation = light.rotation_euler
            dir_x = -math.sin(rotation.z) * math.cos(rotation.x)
            dir_y = math.cos(rotation.z) * math.cos(rotation.x)
            dir_z = -math.sin(rotation.x)
            
            # Normalize
            length = math.sqrt(dir_x**2 + dir_y**2 + dir_z**2)
            if length > 0:
                dir_x /= length
                dir_y /= length
                dir_z /= length
            else:
                dir_x, dir_y, dir_z = 0, 0, -1
            
            ET.SubElement(item, 'x', value=f'{dir_x:.6g}')
            ET.SubElement(item, 'y', value=f'{dir_y:.6g}')
            ET.SubElement(item, 'z', value=f'{dir_z:.6g}')
        
        # Falloff
        falloff_values = []
        for light in lights:
            # Use saved falloff if available, otherwise calculate from energy
            falloff = light.get("gta_falloff", light.data.energy / 10.0)
            falloff_values.append(f'{falloff:.6g}')
        ET.SubElement(lod_lights_soa, 'falloff').text = '\n   ' + ' '.join(falloff_values) + '\n  '
        
        # Falloff exponent
        falloff_exp = []
        for light in lights:
            exp_val = light.get("gta_falloff_exponent", 64)
            falloff_exp.append(str(exp_val))
        ET.SubElement(lod_lights_soa, 'falloffExponent').text = '\n   ' + ' '.join(falloff_exp) + '\n  '
        
        # Time and state flags
        time_flags = []
        for light in lights:
            flag_val = light.get("gta_time_flags", 149946431)
            time_flags.append(str(flag_val))
        ET.SubElement(lod_lights_soa, 'timeAndStateFlags').text = '\n   ' + ' '.join(time_flags) + '\n  '
        
        # Hash
        hash_values = []
        for light in lights:
            # Use saved hash if available (stored as string)
            hash_val = light.get("gta_hash")
            if hash_val is None:
                hash_val = str(hash(light.name) % 4294967296)
            else:
                hash_val = str(hash_val)
            hash_values.append(hash_val)
        ET.SubElement(lod_lights_soa, 'hash').text = '\n   ' + ' '.join(hash_values) + '\n  '
        
        # Cone angles
        inner_angles = []
        outer_angles = []
        for light in lights:
            if light.data.type == 'SPOT':
                inner = int(math.degrees(light.data.spot_size * (1 - light.data.spot_blend)))
                outer = int(math.degrees(light.data.spot_size))
            else:
                inner = 14
                outer = 35
            inner_angles.append(str(inner))
            outer_angles.append(str(outer))
        
        ET.SubElement(lod_lights_soa, 'coneInnerAngle').text = '\n   ' + ' '.join(inner_angles) + '\n  '
        ET.SubElement(lod_lights_soa, 'coneOuterAngleOrCapExt').text = '\n   ' + ' '.join(outer_angles) + '\n  '
        
        # Corona intensity
        corona_values = []
        for light in lights:
            corona = light.get("gta_corona_intensity", 0)
            corona_values.append(str(corona))
        ET.SubElement(lod_lights_soa, 'coronaIntensity').text = '\n   ' + ' '.join(corona_values) + '\n  '
        
        # DistantLODLightsSOA (empty in LOD file)
        distant_soa = ET.SubElement(root, 'DistantLODLightsSOA')
        ET.SubElement(distant_soa, 'position', itemType='FloatXYZ')
        ET.SubElement(distant_soa, 'RGBI')
        ET.SubElement(distant_soa, 'numStreetLights', value='0')
        ET.SubElement(distant_soa, 'category', value='0')
        
        # Block
        block = ET.SubElement(root, 'block')
        ET.SubElement(block, 'version', value='1040236171')
        ET.SubElement(block, 'flags', value='0')
        ET.SubElement(block, 'name')
        ET.SubElement(block, 'exportedBy')
        ET.SubElement(block, 'owner')
        ET.SubElement(block, 'time')
        
        # Write to file
        self._write_xml(root, filepath)
    
    def _export_distant_lodlights(self, filepath, name, lights,
                                  stream_min_x, stream_min_y, stream_min_z,
                                  stream_max_x, stream_max_y, stream_max_z,
                                  min_x, min_y, min_z, max_x, max_y, max_z):
        """Export Distant LOD lights ymap file"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('CMapData')
        
        # Header
        ET.SubElement(root, 'name').text = name
        ET.SubElement(root, 'parent')  # No parent for distant
        ET.SubElement(root, 'flags', value='3')
        ET.SubElement(root, 'contentFlags', value='256')
        
        # Streaming extents (larger for distant)
        ET.SubElement(root, 'streamingExtentsMin',
                     x=f'{stream_min_x:.6g}', y=f'{stream_min_y:.6g}', z=f'{stream_min_z:.6g}')
        ET.SubElement(root, 'streamingExtentsMax',
                     x=f'{stream_max_x:.6g}', y=f'{stream_max_y:.6g}', z=f'{stream_max_z:.6g}')
        ET.SubElement(root, 'entitiesExtentsMin',
                     x=f'{min_x:.6g}', y=f'{min_y:.6g}', z=f'{min_z:.6g}')
        ET.SubElement(root, 'entitiesExtentsMax',
                     x=f'{max_x:.6g}', y=f'{max_y:.6g}', z=f'{max_z:.6g}')
        
        # Empty sections
        ET.SubElement(root, 'entities')
        ET.SubElement(root, 'containerLods', itemType='rage__fwContainerLodDef')
        ET.SubElement(root, 'boxOccluders', itemType='BoxOccluder')
        ET.SubElement(root, 'occludeModels', itemType='OccludeModel')
        ET.SubElement(root, 'physicsDictionaries')
        
        # Instance data
        instance_data = ET.SubElement(root, 'instancedData')
        ET.SubElement(instance_data, 'ImapLink')
        ET.SubElement(instance_data, 'PropInstanceList', itemType='rage__fwPropInstanceListDef')
        ET.SubElement(instance_data, 'GrassInstanceList', itemType='rage__fwGrassInstanceListDef')
        
        ET.SubElement(root, 'timeCycleModifiers', itemType='CTimeCycleModifier')
        ET.SubElement(root, 'carGenerators', itemType='CCarGen')
        
        # LODLightsSOA (empty in distant file)
        lod_lights_soa = ET.SubElement(root, 'LODLightsSOA')
        ET.SubElement(lod_lights_soa, 'direction', itemType='FloatXYZ')
        ET.SubElement(lod_lights_soa, 'falloff')
        ET.SubElement(lod_lights_soa, 'falloffExponent')
        ET.SubElement(lod_lights_soa, 'timeAndStateFlags')
        ET.SubElement(lod_lights_soa, 'hash')
        ET.SubElement(lod_lights_soa, 'coneInnerAngle')
        ET.SubElement(lod_lights_soa, 'coneOuterAngleOrCapExt')
        ET.SubElement(lod_lights_soa, 'coronaIntensity')
        
        # DistantLODLightsSOA (contains positions and colors)
        distant_soa = ET.SubElement(root, 'DistantLODLightsSOA')
        
        # Positions
        position = ET.SubElement(distant_soa, 'position', itemType='FloatXYZ')
        for light in lights:
            item = ET.SubElement(position, 'Item')
            ET.SubElement(item, 'x', value=f'{light.location.x:.6g}')
            ET.SubElement(item, 'y', value=f'{light.location.y:.6g}')
            ET.SubElement(item, 'z', value=f'{light.location.z:.6g}')
        
        # RGBI (color and intensity packed)
        rgbi_values = []
        for light in lights:
            color = light.data.color
            r = int(min(max(color[0] * 255, 0), 255))
            g = int(min(max(color[1] * 255, 0), 255))
            b = int(min(max(color[2] * 255, 0), 255))
            
            # Calculate intensity from falloff or energy
            falloff = light.get("gta_falloff", light.data.energy)
            i = int(min(max(falloff * 10, 0), 255))
            
            # Pack as RGBI integer (R|G|B|I format)
            rgbi = (r << 24) | (g << 16) | (b << 8) | i
            rgbi_values.append(str(rgbi))
        
        ET.SubElement(distant_soa, 'RGBI').text = '\n   ' + ' '.join(rgbi_values) + '\n  '
        ET.SubElement(distant_soa, 'numStreetLights', value='0')
        ET.SubElement(distant_soa, 'category', value='1')
        
        # Block
        block = ET.SubElement(root, 'block')
        ET.SubElement(block, 'version', value='1040236171')
        ET.SubElement(block, 'flags', value='0')
        ET.SubElement(block, 'name')
        ET.SubElement(block, 'exportedBy')
        ET.SubElement(block, 'owner')
        ET.SubElement(block, 'time')
        
        # Write to file
        self._write_xml(root, filepath)
    
    def _write_xml(self, root, filepath):
        """Write XML with proper formatting"""
        from xml.dom import minidom
        import xml.etree.ElementTree as ET
        
        # Convert to string
        xml_str = ET.tostring(root, encoding='utf-8')
        
        # Pretty print
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent=' ', encoding='UTF-8')
        
        # Write to file
        with open(filepath, 'wb') as f:
            f.write(pretty_xml)
    
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
        box.label(text="LOD Light Tools", icon='LIGHT')
        box.label(text="For GTA V")
        
        # Settings section
        if context.active_object and context.active_object.type == 'LIGHT':
            obj = context.active_object
            
            box = layout.box()
            box.label(text=f"Light: {obj.name}", icon='OUTLINER_OB_LIGHT')
            
            # Show if it's a LOD light
            is_lod = obj.get("is_lod_light", False)
            if is_lod:
                box.label(text="✓ LOD Light", icon='CHECKMARK')
            
            # Light data properties
            box.label(text="Blender Properties:")
            row = box.row()
            row.prop(obj.data, "energy", text="Intensity")
            row = box.row()
            row.prop(obj.data, "color", text="Color")
            
            # GTA V Custom properties (if LOD light)
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
        else:
            layout.label(text="Select a light to view info", icon='INFO')
        
        # Actions
        layout.separator()
        
        col = layout.column()
        col.operator("mudstar.import_lod_lights", icon='IMPORT')
        col.operator("mudstar.export_lod_lights", icon='EXPORT')


# Registration
classes = (
    MUDSTAR_PG_LodLightSettings,
    MUDSTAR_OT_ImportLodLights,
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
