#----------------------------------------------------------
# File __init__.py
#----------------------------------------------------------

#    Addon info
bl_info = {
    "name": "Galvanized Tools",
    "description": "Tools for general improved functionality.",
    "author": "Anthony Esau",
    "version": (20170325),
    "blender": (2, 78, 0),
    "location": "3D View > Toolbar",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}

# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import imp
    imp.reload(dimprop)
    imp.reload(parenttools)
    print("Reloaded multifiles")
else:
    from . import dimprop, parenttools
    print("Imported multifiles")


import bpy


#
#    Registration
#

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
