bl_info = {
    "name": "Export To UE Custom Pipline",
    "blender": (3, 3, 0),
    "category": "object",
}

import bpy
import sys
import os

addon_directory = os.path.dirname(os.path.abspath(__file__))
if addon_directory not in sys.path:
    sys.path.append(addon_directory)

import ExporterScript


class ExportOperator(bpy.types.Operator):
    bl_idname = "object.export_to_ue_custom_pipline"
    bl_label = "Export To UE Custom Pipline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ExporterScript.main()
        return {"FINISHED"}
    


def register():
    bpy.utils.register_class(ExportOperator)

def unregister():
    bpy.utils.unregister_class(ExportOperator)

if __name__ == "__main__":
    register()