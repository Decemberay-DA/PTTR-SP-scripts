import json
from types import *

config_file_json = """
{
    "main": {
        "is_revert_changes": false,
        "is_export_to_ue": false
    },
    "logging": {
        "tab_size": 3,
        "this_file_name": "ExporterScript",
        "log_file_name": "ExporterScript.log"
    },
    "passes": {
        "fix_normals": {
            "enabled": true,
            "attribute_name": "dont_fix_normals"
        },
        "create_micro_bone": {
            "enabled": true,
            "attribute_name": "create_micro_bone",
            "micro_bone_parent": "micro_bone_parent",
            "micro_bone_name": "micro_bone_name"
        },
        "apply_render_geometry_modifiers": {
            "enabled": false,
            "attribute_name": "is_apply_render_or_view_modifiers"
        }
    }
}
"""

def load_config():
    # with open("config.json", "r") as config_file:
    #     config_dict = json.load(config_file)
    config_dict = json.load(config_file_json)

    def dict_to_namespace(d):
        return json.loads(json.dumps(d), object_hook=lambda d: SimpleNamespace(**d))
    
    return dict_to_namespace(config_dict)

