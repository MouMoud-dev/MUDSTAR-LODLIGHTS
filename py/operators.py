"""Import/Export operators for MUDSTAR LOD Lights"""

import bpy
import os
import math
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from mathutils import Vector, Quaternion
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import Operator, OperatorFileListElement


class MUDSTAR_OT_ImportLodLights(Operator):
    """Import LOD lights from GTA V ymap.xml or JSON file (supports multiple files)"""
    bl_idname = "mudstar.import_lod_lights"
    bl_label = "Import LOD Lights"
    bl_options = {'REGISTER', 'UNDO'}
    
    files: CollectionProperty(type=OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: StringProperty(subtype='DIR_PATH')
    filter_glob: StringProperty(default='*.ymap.xml;*.xml;*.json', options={'HIDDEN'})
    
    def execute(self, context):
        if not self.files and not self.directory:
            self.report({'ERROR'}, "No files selected")
            return {'CANCELLED'}
        
        try:
            # Handle multiple files
            total_imported = 0
            files_processed = 0
            
            for file_elem in self.files:
                filepath = os.path.join(self.directory, file_elem.name)
                ext = os.path.splitext(filepath)[1].lower()
                
                if ext == '.xml':
                    count = self._import_xml(context, filepath)
                    total_imported += count
                    files_processed += 1
                elif ext == '.json':
                    count = self._import_json(context, filepath)
                    total_imported += count
                    files_processed += 1
                else:
                    self.report({'WARNING'}, f"Skipped unsupported file: {file_elem.name}")
            
            if files_processed == 0:
                self.report({'ERROR'}, "No valid files to import")
                return {'CANCELLED'}
            
            self.report({'INFO'}, f"Imported {total_imported} lights from {files_processed} file(s)")
            return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def _import_xml(self, context, filepath):
        """Import from GTA V ymap.xml format"""
        # Get filename without extension for collection name
        filename = os.path.splitext(os.path.basename(filepath))[0]
        if filename.endswith('.ymap'):
            filename = filename[:-5]
        
        # Create or get collection
        if filename in bpy.data.collections:
            collection = bpy.data.collections[filename]
        else:
            collection = bpy.data.collections.new(filename)
            context.scene.collection.children.link(collection)
            # Set collection color to yellow for LOD lights
            collection.color_tag = 'COLOR_03'  # Yellow
        
        # Parse XML
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Get parent name for distant file naming
        parent_name_element = root.find('.//parent')
        if parent_name_element is not None and parent_name_element.text:
            # Store the distant LOD filename in collection properties
            collection["distant_lod_name"] = parent_name_element.text
        else:
            # Try to derive distant name from current filename
            if 'lodlights' in filename.lower():
                # Replace various LOD patterns with dist patterns
                distant_name = filename.replace('_lodlights', '_distantlights')
                distant_name = distant_name.replace('_LODLIGHTS', '_distantlights')
                distant_name = distant_name.replace('lodlights', 'distantlights')
                distant_name = distant_name.replace('LODLIGHTS', 'distantlights')
                collection["distant_lod_name"] = distant_name
            else:
                collection["distant_lod_name"] = filename + "_distantlights"
        
        # Get LOD lights data
        lod_lights_soa = root.find('.//LODLightsSOA')
        distant_soa = root.find('.//DistantLODLightsSOA')
        
        if lod_lights_soa is None:
            return 0
        
        # Load positions from parent file if specified
        positions_list, rgbi_list = self._load_positions_from_parent(root, filepath)
        
        # If no positions from parent, check current file
        if not positions_list and distant_soa is not None:
            positions = distant_soa.find('position')
            rgbi = distant_soa.find('RGBI')
            
            if positions is not None:
                positions_list = positions.findall('Item')
            if rgbi is not None and rgbi.text:
                rgbi_list = [int(v) for v in rgbi.text.strip().split()]
        
        # Parse light data
        light_data = self._parse_lod_light_data(lod_lights_soa)
        
        if not light_data['directions']:
            return 0
        
        # Get extents for position fallback
        extents = self._get_extents(root)
        
        # Create lights in Blender
        imported_count = self._create_lights(
            collection, 
            light_data, 
            positions_list, 
            rgbi_list, 
            extents
        )
        
        return imported_count
    
    def _load_positions_from_parent(self, root, filepath):
        """Load positions from parent file if it exists"""
        positions_list = []
        rgbi_list = []
        
        parent_name = root.find('.//parent')
        if parent_name is not None and parent_name.text:
            parent_filename = parent_name.text + '.ymap.xml'
            parent_path = os.path.join(os.path.dirname(filepath), parent_filename)
            
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
                        
                        print(f"Loaded {len(positions_list)} positions from parent: {parent_filename}")
                except Exception as e:
                    print(f"Error loading parent file: {e}")
        
        return positions_list, rgbi_list
    
    def _parse_lod_light_data(self, lod_lights_soa):
        """Parse LOD light data from XML"""
        data = {
            'directions': [],
            'hashes': [],
            'falloffs': [],
            'falloff_exponents': [],
            'cone_inner': [],
            'cone_outer': [],
            'coronas': [],
            'time_flags': []
        }
        
        # Directions
        directions = lod_lights_soa.find('direction')
        if directions is not None:
            data['directions'] = directions.findall('Item')
        
        # Hashes
        hashes = lod_lights_soa.find('hash')
        if hashes is not None and hashes.text:
            data['hashes'] = hashes.text.strip().split()
        
        # Falloffs
        falloffs = lod_lights_soa.find('falloff')
        if falloffs is not None and falloffs.text:
            data['falloffs'] = [float(v.replace(',', '.')) for v in falloffs.text.strip().split()]
        
        # Falloff exponents
        falloff_exp = lod_lights_soa.find('falloffExponent')
        if falloff_exp is not None and falloff_exp.text:
            data['falloff_exponents'] = [int(float(v.replace(',', '.'))) for v in falloff_exp.text.strip().split()]
        
        # Cone angles
        cone_inner = lod_lights_soa.find('coneInnerAngle')
        if cone_inner is not None and cone_inner.text:
            data['cone_inner'] = [int(float(v.replace(',', '.'))) for v in cone_inner.text.strip().split()]
        
        cone_outer = lod_lights_soa.find('coneOuterAngleOrCapExt')
        if cone_outer is not None and cone_outer.text:
            data['cone_outer'] = [int(float(v.replace(',', '.'))) for v in cone_outer.text.strip().split()]
        
        # Corona
        corona = lod_lights_soa.find('coronaIntensity')
        if corona is not None and corona.text:
            data['coronas'] = [int(float(v.replace(',', '.'))) for v in corona.text.strip().split()]
        
        # Time flags
        time_flags = lod_lights_soa.find('timeAndStateFlags')
        if time_flags is not None and time_flags.text:
            data['time_flags'] = [int(v) for v in time_flags.text.strip().split()]
        
        return data
    
    def _get_extents(self, root):
        """Get extents from XML"""
        extents_min = root.find('.//entitiesExtentsMin')
        extents_max = root.find('.//entitiesExtentsMax')
        
        offset_x = offset_y = offset_z = 0.0
        
        if extents_min is not None and extents_max is not None:
            min_x = float(extents_min.get('x', 0))
            min_y = float(extents_min.get('y', 0))
            min_z = float(extents_min.get('z', 0))
            max_x = float(extents_max.get('x', 0))
            max_y = float(extents_max.get('y', 0))
            max_z = float(extents_max.get('z', 0))
            
            offset_x = (min_x + max_x) / 2.0
            offset_y = (min_y + max_y) / 2.0
            offset_z = (min_z + max_z) / 2.0
        
        return (offset_x, offset_y, offset_z)
    
    def _create_lights(self, collection, light_data, positions_list, rgbi_list, extents):
        """Create light objects in Blender"""
        imported_count = 0
        
        for i, direction_item in enumerate(light_data['directions']):
            # Get direction
            dir_x = float(direction_item.find('x').get('value', 0))
            dir_y = float(direction_item.find('y').get('value', 0))
            dir_z = float(direction_item.find('z').get('value', 0))
            
            # Get properties
            hash_val = light_data['hashes'][i] if i < len(light_data['hashes']) else str(i)
            falloff = light_data['falloffs'][i] if i < len(light_data['falloffs']) else 2.3
            falloff_exp = light_data['falloff_exponents'][i] if i < len(light_data['falloff_exponents']) else 64
            corona = light_data['coronas'][i] if i < len(light_data['coronas']) else 0
            time_flag = light_data['time_flags'][i] if i < len(light_data['time_flags']) else 149946431
            inner_angle = light_data['cone_inner'][i] if i < len(light_data['cone_inner']) else 14
            outer_angle = light_data['cone_outer'][i] if i < len(light_data['cone_outer']) else 35
            
            # Get color from RGBI (packed as: I << 24 | R << 16 | G << 8 | B)
            color = (1.0, 1.0, 1.0)
            rgbi_intensity = 0
            if i < len(rgbi_list):
                rgbi = rgbi_list[i]
                rgbi_intensity = (rgbi >> 24) & 0xFF
                r = ((rgbi >> 16) & 0xFF) / 255.0
                g = ((rgbi >> 8) & 0xFF) / 255.0
                b = (rgbi & 0xFF) / 255.0
                color = (r, g, b)
            
            # Determine light type
            light_type = 'SPOT' if (inner_angle > 14 or outer_angle > 35) else 'POINT'
            
            # Create light
            light_name = f"LOD_Light_{hash_val}"
            light_data_obj = bpy.data.lights.new(name=light_name, type=light_type)
            light_data_obj.energy = falloff
            light_data_obj.color = color
            
            if light_type == 'SPOT':
                light_data_obj.spot_size = math.radians(outer_angle)
                light_data_obj.spot_blend = (outer_angle - inner_angle) / outer_angle if outer_angle > 0 else 0.5
            
            # Create object
            light_obj = bpy.data.objects.new(name=light_name, object_data=light_data_obj)
            
            # Store GTA V properties
            light_obj["is_lod_light"] = True
            light_obj["gta_falloff"] = falloff
            light_obj["gta_falloff_exponent"] = falloff_exp
            light_obj["gta_hash"] = hash_val
            light_obj["gta_corona_intensity"] = corona
            light_obj["gta_time_flags"] = time_flag
            light_obj["gta_rgbi_intensity"] = rgbi_intensity
            
            # Link to collection
            collection.objects.link(light_obj)
            
            # Set position
            if i < len(positions_list):
                pos_item = positions_list[i]
                pos_x = float(pos_item.find('x').get('value', 0))
                pos_y = float(pos_item.find('y').get('value', 0))
                pos_z = float(pos_item.find('z').get('value', 0))
                light_obj.location = (pos_x, pos_y, pos_z)
            else:
                # Fallback position
                spread = 5.0
                light_obj.location = (
                    extents[0] + (i % 10) * spread,
                    extents[1] + (i // 10) * spread,
                    extents[2]
                )
            
            # Set rotation from direction
            # Light's local -Z axis should point along the direction vector
            if dir_x != 0 or dir_y != 0 or dir_z != 0:
                direction = Vector((dir_x, dir_y, dir_z)).normalized()
                quat = direction.to_track_quat('-Z', 'Y')
                light_obj.rotation_euler = quat.to_euler()
            
            imported_count += 1
        
        return imported_count
    
    def _import_json(self, context, filepath):
        """Import from JSON format"""
        filename = os.path.splitext(os.path.basename(filepath))[0]
        
        # Create collection
        if filename in bpy.data.collections:
            collection = bpy.data.collections[filename]
        else:
            collection = bpy.data.collections.new(filename)
            context.scene.collection.children.link(collection)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        imported_count = 0
        for light_data in data.get('lights', []):
            light_name = light_data.get('name', 'LOD_Light')
            light_obj_data = bpy.data.lights.new(name=light_name, type='POINT')
            light_obj_data.energy = light_data.get('intensity', 1.0)
            light_obj_data.color = light_data.get('color', [1.0, 1.0, 1.0])
            
            light_obj = bpy.data.objects.new(name=light_name, object_data=light_obj_data)
            light_obj.mudstar_lod_settings.is_lod_light = True
            light_obj.mudstar_lod_settings.intensity = light_data.get('intensity', 1.0)
            light_obj.mudstar_lod_settings.lod_distance = light_data.get('lod_distance', 100.0)
            
            collection.objects.link(light_obj)
            light_obj.location = light_data.get('location', [0.0, 0.0, 0.0])
            imported_count += 1
        
        return imported_count
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MUDSTAR_OT_ExportLodLights(Operator):
    """Export selected collections with LOD lights to GTA V ymap.xml format"""
    bl_idname = "mudstar.export_lod_lights"
    bl_label = "Export LOD Lights"
    bl_options = {'REGISTER'}
    
    directory: StringProperty(subtype='DIR_PATH')
    
    def execute(self, context):
        selected_collections = []
        collections_to_export = set()
        
        # Check active collection in outliner (selected collection)
        view_layer = context.view_layer
        active_layer_collection = view_layer.active_layer_collection
        
        if active_layer_collection and active_layer_collection.collection:
            coll = active_layer_collection.collection
            # Only export if it's not the root Scene Collection and has LOD lights
            if coll.name != 'Scene Collection':
                lod_lights = [o for o in coll.objects 
                             if o.type == 'LIGHT' and o.get("is_lod_light", False)]
                if lod_lights:
                    collections_to_export.add(coll.name)
        
        # If no active collection selected or no LOD lights, export all
        if not collections_to_export:
            for coll in bpy.data.collections:
                lod_lights = [obj for obj in coll.objects 
                             if obj.type == 'LIGHT' and obj.get("is_lod_light", False)]
                if lod_lights:
                    collections_to_export.add(coll.name)
        
        # Build export list
        for coll_name in collections_to_export:
            coll = bpy.data.collections.get(coll_name)
            if coll:
                lod_lights = [obj for obj in coll.objects 
                             if obj.type == 'LIGHT' and obj.get("is_lod_light", False)]
                if lod_lights:
                    selected_collections.append((coll.name, lod_lights))
        
        if not selected_collections:
            self.report({'WARNING'}, "No collections with LOD lights found.")
            return {'CANCELLED'}
        
        if not self.directory:
            self.report({'ERROR'}, "No directory specified")
            return {'CANCELLED'}
        
        try:
            # Export each collection
            total_exported = 0
            files_created = []
            
            for collection_name, lod_lights in selected_collections:
                # Generate filenames
                lodlights_name, distant_name = self._generate_filenames(collection_name)
                
                lodlights_path = os.path.join(self.directory, lodlights_name + '.ymap.xml')
                distant_path = os.path.join(self.directory, distant_name + '.ymap.xml')
                
                # Calculate extents
                extents = self._calculate_extents(lod_lights)
                
                # Export files
                self._export_lodlights(lodlights_path, lodlights_name, distant_name, lod_lights, extents)
                self._export_distant_lodlights(distant_path, distant_name, lod_lights, extents)
                
                files_created.append(lodlights_name + '.ymap.xml')
                files_created.append(distant_name + '.ymap.xml')
                total_exported += len(lod_lights)
            
            self.report({'INFO'}, f"Exported {total_exported} LOD light(s) from {len(selected_collections)} collection(s)\nCreated {len(files_created)} file(s)")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def _generate_filenames(self, collection_name):
        """Generate lodlights and distant filenames using stored names"""
        # Get the collection object
        coll = bpy.data.collections.get(collection_name)
        
        # Use the collection name as lodlights name
        lodlights_name = collection_name
        
        # Get stored distant name from collection properties
        if coll and "distant_lod_name" in coll:
            distant_name = coll["distant_lod_name"]
        else:
            # Fallback: try to derive distant name
            if 'lodlights' in collection_name.lower():
                distant_name = collection_name.replace('_lodlights', '_distantlights')
                distant_name = distant_name.replace('_LODLIGHTS', '_distantlights')
                distant_name = distant_name.replace('lodlights', 'distantlights')
                distant_name = distant_name.replace('LODLIGHTS', 'distantlights')
            elif 'lod' in collection_name.lower():
                distant_name = collection_name.replace('_lod', '_dist')
                distant_name = distant_name.replace('lod', 'dist')
            else:
                distant_name = collection_name + '_distantlights'
        
        return lodlights_name, distant_name
    
    def _get_all_layer_collections(self, layer_collection):
        """Recursively get all layer collections"""
        yield layer_collection
        for child in layer_collection.children:
            yield from self._get_all_layer_collections(child)
    
    def _calculate_extents(self, lights):
        """Calculate bounding extents for lights"""
        min_x = min(light.location.x for light in lights)
        min_y = min(light.location.y for light in lights)
        min_z = min(light.location.z for light in lights)
        max_x = max(light.location.x for light in lights)
        max_y = max(light.location.y for light in lights)
        max_z = max(light.location.z for light in lights)
        
        margin = 2000.0
        return {
            'min': (min_x, min_y, min_z),
            'max': (max_x, max_y, max_z),
            'stream_min': (min_x - margin, min_y - margin, min_z - margin),
            'stream_max': (max_x + margin, max_y + margin, max_z + margin)
        }
    
    def _export_lodlights(self, filepath, name, parent, lights, extents):
        """Export LOD lights ymap file"""
        root = ET.Element('CMapData')
        
        # Header
        ET.SubElement(root, 'name').text = name
        ET.SubElement(root, 'parent').text = parent
        ET.SubElement(root, 'flags', value='1')
        ET.SubElement(root, 'contentFlags', value='128')
        
        # Extents
        self._add_extents(root, extents)
        
        # Empty sections
        self._add_empty_sections(root)
        
        # LODLightsSOA
        lod_lights_soa = ET.SubElement(root, 'LODLightsSOA')
        self._add_lod_light_data(lod_lights_soa, lights)
        
        # DistantLODLightsSOA (empty)
        distant_soa = ET.SubElement(root, 'DistantLODLightsSOA')
        ET.SubElement(distant_soa, 'position', itemType='FloatXYZ')
        ET.SubElement(distant_soa, 'RGBI')
        ET.SubElement(distant_soa, 'numStreetLights', value='0')
        ET.SubElement(distant_soa, 'category', value='0')
        
        # Block
        self._add_block(root)
        
        # Write
        self._write_xml(root, filepath)
    
    def _export_distant_lodlights(self, filepath, name, lights, extents):
        """Export Distant LOD lights ymap file"""
        root = ET.Element('CMapData')
        
        # Header
        ET.SubElement(root, 'name').text = name
        ET.SubElement(root, 'parent')
        ET.SubElement(root, 'flags', value='3')
        ET.SubElement(root, 'contentFlags', value='256')
        
        # Extents
        self._add_extents(root, extents)
        
        # Empty sections
        self._add_empty_sections(root)
        
        # LODLightsSOA (empty)
        lod_lights_soa = ET.SubElement(root, 'LODLightsSOA')
        ET.SubElement(lod_lights_soa, 'direction', itemType='FloatXYZ')
        ET.SubElement(lod_lights_soa, 'falloff')
        ET.SubElement(lod_lights_soa, 'falloffExponent')
        ET.SubElement(lod_lights_soa, 'timeAndStateFlags')
        ET.SubElement(lod_lights_soa, 'hash')
        ET.SubElement(lod_lights_soa, 'coneInnerAngle')
        ET.SubElement(lod_lights_soa, 'coneOuterAngleOrCapExt')
        ET.SubElement(lod_lights_soa, 'coronaIntensity')
        
        # DistantLODLightsSOA (with data)
        distant_soa = ET.SubElement(root, 'DistantLODLightsSOA')
        self._add_distant_light_data(distant_soa, lights)
        
        # Block
        self._add_block(root)
        
        # Write
        self._write_xml(root, filepath)
    
    def _add_extents(self, root, extents):
        """Add extent elements to XML"""
        ET.SubElement(root, 'streamingExtentsMin',
                     x=f'{extents["stream_min"][0]:.6g}',
                     y=f'{extents["stream_min"][1]:.6g}',
                     z=f'{extents["stream_min"][2]:.6g}')
        ET.SubElement(root, 'streamingExtentsMax',
                     x=f'{extents["stream_max"][0]:.6g}',
                     y=f'{extents["stream_max"][1]:.6g}',
                     z=f'{extents["stream_max"][2]:.6g}')
        ET.SubElement(root, 'entitiesExtentsMin',
                     x=f'{extents["min"][0]:.6g}',
                     y=f'{extents["min"][1]:.6g}',
                     z=f'{extents["min"][2]:.6g}')
        ET.SubElement(root, 'entitiesExtentsMax',
                     x=f'{extents["max"][0]:.6g}',
                     y=f'{extents["max"][1]:.6g}',
                     z=f'{extents["max"][2]:.6g}')
    
    def _add_empty_sections(self, root):
        """Add empty required sections"""
        ET.SubElement(root, 'entities')
        ET.SubElement(root, 'containerLods', itemType='rage__fwContainerLodDef')
        ET.SubElement(root, 'boxOccluders', itemType='BoxOccluder')
        ET.SubElement(root, 'occludeModels', itemType='OccludeModel')
        ET.SubElement(root, 'physicsDictionaries')
        
        instance_data = ET.SubElement(root, 'instancedData')
        ET.SubElement(instance_data, 'ImapLink')
        ET.SubElement(instance_data, 'PropInstanceList', itemType='rage__fwPropInstanceListDef')
        ET.SubElement(instance_data, 'GrassInstanceList', itemType='rage__fwGrassInstanceListDef')
        
        ET.SubElement(root, 'timeCycleModifiers', itemType='CTimeCycleModifier')
        ET.SubElement(root, 'carGenerators', itemType='CCarGen')
    
    def _add_lod_light_data(self, parent, lights):
        """Add LOD light data to XML"""
        # Directions
        direction = ET.SubElement(parent, 'direction', itemType='FloatXYZ')
        for light in lights:
            item = ET.SubElement(direction, 'Item')
            # Compute direction from full rotation matrix
            # Light points along its local -Z axis
            mat = light.rotation_euler.to_matrix()
            dir_vec = mat @ Vector((0, 0, -1))
            dir_vec.normalize()
            
            ET.SubElement(item, 'x', value=f'{dir_vec.x:.6g}')
            ET.SubElement(item, 'y', value=f'{dir_vec.y:.6g}')
            ET.SubElement(item, 'z', value=f'{dir_vec.z:.6g}')
        
        # Falloff
        falloff_values = [f'{light.get("gta_falloff", light.data.energy / 10.0):.6g}' for light in lights]
        ET.SubElement(parent, 'falloff').text = '\n   ' + ' '.join(falloff_values) + '\n  '
        
        # Falloff exponent
        falloff_exp = [str(light.get("gta_falloff_exponent", 64)) for light in lights]
        ET.SubElement(parent, 'falloffExponent').text = '\n   ' + ' '.join(falloff_exp) + '\n  '
        
        # Time flags
        time_flags = [str(light.get("gta_time_flags", 149946431)) for light in lights]
        ET.SubElement(parent, 'timeAndStateFlags').text = '\n   ' + ' '.join(time_flags) + '\n  '
        
        # Hash
        hash_values = [str(light.get("gta_hash", hash(light.name) % 4294967296)) for light in lights]
        ET.SubElement(parent, 'hash').text = '\n   ' + ' '.join(hash_values) + '\n  '
        
        # Cone angles
        inner_angles = []
        outer_angles = []
        for light in lights:
            if light.data.type == 'SPOT':
                inner = round(math.degrees(light.data.spot_size * (1 - light.data.spot_blend)))
                outer = round(math.degrees(light.data.spot_size))
            else:
                inner, outer = 14, 35
            inner_angles.append(str(inner))
            outer_angles.append(str(outer))
        
        ET.SubElement(parent, 'coneInnerAngle').text = '\n   ' + ' '.join(inner_angles) + '\n  '
        ET.SubElement(parent, 'coneOuterAngleOrCapExt').text = '\n   ' + ' '.join(outer_angles) + '\n  '
        
        # Corona
        corona_values = [str(light.get("gta_corona_intensity", 0)) for light in lights]
        ET.SubElement(parent, 'coronaIntensity').text = '\n   ' + ' '.join(corona_values) + '\n  '
    
    def _add_distant_light_data(self, parent, lights):
        """Add distant LOD light data to XML"""
        # Positions
        position = ET.SubElement(parent, 'position', itemType='FloatXYZ')
        for light in lights:
            item = ET.SubElement(position, 'Item')
            ET.SubElement(item, 'x', value=f'{light.location.x:.6g}')
            ET.SubElement(item, 'y', value=f'{light.location.y:.6g}')
            ET.SubElement(item, 'z', value=f'{light.location.z:.6g}')
        
        # RGBI (packed as: I << 24 | R << 16 | G << 8 | B)
        rgbi_values = []
        for light in lights:
            color = light.data.color
            r = int(min(max(color[0] * 255, 0), 255))
            g = int(min(max(color[1] * 255, 0), 255))
            b = int(min(max(color[2] * 255, 0), 255))
            
            i = int(min(max(light.get("gta_rgbi_intensity", 0), 0), 255))
            
            rgbi = (i << 24) | (r << 16) | (g << 8) | b
            rgbi_values.append(str(rgbi))
        
        ET.SubElement(parent, 'RGBI').text = '\n   ' + ' '.join(rgbi_values) + '\n  '
        ET.SubElement(parent, 'numStreetLights', value='0')
        ET.SubElement(parent, 'category', value='1')
    
    def _add_block(self, root):
        """Add block section to XML"""
        block = ET.SubElement(root, 'block')
        ET.SubElement(block, 'version', value='1040236171')
        ET.SubElement(block, 'flags', value='0')
        ET.SubElement(block, 'name')
        ET.SubElement(block, 'exportedBy')
        ET.SubElement(block, 'owner')
        ET.SubElement(block, 'time')
    
    def _write_xml(self, root, filepath):
        """Write XML with proper formatting"""
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent=' ', encoding='UTF-8')
        
        with open(filepath, 'wb') as f:
            f.write(pretty_xml)
    
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Registration
classes = (
    MUDSTAR_OT_ImportLodLights,
    MUDSTAR_OT_ExportLodLights,
)


def register():
    """Register operator classes"""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister operator classes"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
