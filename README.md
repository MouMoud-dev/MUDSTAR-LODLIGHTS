# MUDSTAR LOD Lights

![MUDSTAR LOD Lights Logo](mudstar_lodlights.svg)

A Blender addon for editing and generating LOD (Level of Detail) lights for GTA V.

## Description

MUDSTAR LOD Lights is a Blender addon that allows users to edit LOD lights and automatically generate distant LOD lights at export. This tool is specifically designed for GTA V modding workflows, making it easier to manage lighting in your custom maps and models.

## Features

- **LOD Light Editor**: Edit properties of LOD lights directly in Blender
- **Multi-file Import**: Import multiple ymap.xml files at once
- **Automatic Collection Management**: Each imported file creates its own collection
- **Multi-collection Export**: Export all collections with LOD lights in one operation
- **Automatic Generation**: Generate distant LOD lights from existing lights
- **GTA V Compatible**: Designed specifically for GTA V modding workflow
- **Easy Export**: Export LOD lights data with automatic file naming
- **Intuitive UI**: Simple sidebar panel in Blender's 3D viewport

## Installation

1. Download the latest release or clone this repository
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install` and select `MUDSTAR-LODLIGHTS.zip`
4. Enable the "MUDSTAR LOD Lights" addon from the list
5. The addon panel will appear in the 3D View sidebar under the "M*LODLights" tab

## Usage

### Import
1. Click "Import (Multi-file)" in the M*LODLights panel
2. Select one or more `.ymap.xml` files (hold Shift to select multiple)
3. Each file will be imported into its own collection
4. LOD lights will be created with all GTA V properties preserved
5. ⚠️ You need to export from code walker the lod + dist lod, exemple : lodlights_medium015.ymap + distlodlights_medium015.ymap

### Export
1. Click "Export All Collections" in the M*LODLights panel
2. Select a directory for export
3. All collections containing LOD lights will be exported as separate file pairs:
   - `collectionname_lodlights.ymap.xml` (LOD light data)
   - `collectionname_distlodlights.ymap.xml` (distant light positions and colors)

### View Light Information
1. Select a light object in your scene
2. Open the sidebar (press `N` in the 3D viewport)
3. Navigate to the "M*LODLights" tab
4. View LOD light information and configure settings:
   - View if the light is a LOD light
   - See Blender properties (intensity, color)
   - View GTA V properties (falloff, corona, hash, time flags)

## Requirements

- Blender 2.80 or higher
- Python 3.7+

## File Structure

```
MUDSTAR-LODLIGHTS/
├── __init__.py             
├── py/                     
│   ├── properties.py      
│   ├── operators.py       
│   └── ui.py             
├── mudstar_lodlights.svg  
├── LICENSE                
├── README.md             
└── .gitignore           
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.

## Credits

Developed by MouMoud

---

**Note**: This addon is designed for GTA V modding purposes.
