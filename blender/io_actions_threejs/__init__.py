#TODO: add licence info

bl_info = {
    "name": "three.js actions",
    "author": "apendua",
    "version": (0, 0, 1),
    "blender": (2, 6, 7),
    #TODO: find out current version "api": 35622,
    "location": "File > Import-Export",
    "description": "Import-Export three.js actions",
    "warning": "",
    "wiki_url": "https://github.com/apendua/threejs-actions/tree/master/blender",
    "tracker_url": "https://github.com/apendua/threejs-actions/issues",
    "category": "Import-Export"
}

# To support reload properly, try to access a package var,
# if it's there, reload everything

import bpy

if "bpy" in locals():
    import imp
    if "export_actions" in locals():
        imp.reload(export_actions)

from bpy.props import *
from bpy_extras.io_utils import ExportHelper

# exporter - settings
# this code is from threejs mesh exporter

SETTINGS_FILE_EXPORT = "threejs_actions_settings_export.js"

import os
import json

def file_exists(filename):
    """Return true if file exists and accessible for reading.

    Should be safer than just testing for existence due to links and
    permissions magic on Unix filesystems.

    @rtype: boolean
    """

    try:
        f = open(filename, 'r')
        f.close()
        return True
    except IOError:
        return False

def get_settings_fullpath():
    return os.path.join(bpy.app.tempdir, SETTINGS_FILE_EXPORT)

def save_settings_export(properties):

    settings = {}

    fname = get_settings_fullpath()
    f = open(fname, "w")
    json.dump(settings, f)

def restore_settings_export(properties):

    settings = {}

    fname = get_settings_fullpath()
    if file_exists(fname):
        f = open(fname, "r")
        settings = json.load(f)
    # ...

# ################################################################
# Exporter
# ################################################################

class ExportActionsThreeJS(bpy.types.Operator, ExportHelper):
    '''Export actions for Three.js (ASCII JSON format).'''

    bl_idname = "export.actions_threejs"
    bl_label  = "Export Actions Three.js"

    filename_ext = ".js"

    def invoke(self, context, event):
        restore_settings_export(self.properties)
        return ExportHelper.invoke(self, context, event)

    @classmethod
    def poll(cls, context):
        return True
        #return context.active_object != None

    def execute(self, context):
        #print("Selected: " + context.active_object.name)

        if not self.properties.filepath:
            raise Exception("filename not set")

        save_settings_export(self.properties)

        filepath = self.filepath

        import io_actions_threejs.export_actions
        return io_actions_threejs.export_actions.save(self, context, **self.properties)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Actions:")

        #row.label(text="--------- Experimental ---------")
        #layout.separator()

        #row.label(text="Animation:")

        #row.prop(self.properties, "option_all_actions")
        #layout.separator()

# register / unregister

def menu_func_export(self, context):
    default_path = bpy.data.filepath.replace(".blend", ".js")
    self.layout.operator(ExportActionsTHREEJS.bl_idname, text="Actions Three.js (.js)").filepath = default_path

def register():
    bpy.utils.register_class(ExportActionsThreeJS)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportActionsThreeJS)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
