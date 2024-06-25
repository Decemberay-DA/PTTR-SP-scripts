import datetime
import traceback
import bpy
import json
from types import SimpleNamespace
from typing import *






# Utils.py
class Utils:
    @staticmethod
    def map_action(iterator, func):
        for item in iterator:
            func(item)

    @staticmethod
    def map_iter(iterator, func):
        for item in iterator:
            yield func(item)

    @staticmethod
    def map_iter_pipe(iterator, *funcs):
        for item in iterator:
            for func in funcs:
                item = func(item)
            yield item

    @staticmethod
    def execute_pass_queue(obj, *fn):
        for fn in fn:
            fn(obj)

    @staticmethod
    def do(obj, fn):
        fn()
        return obj

    @staticmethod
    def btw(fn):
        fn()
        return lambda obj: obj









# Decorating.py
class Decorating:
    @staticmethod
    def returns_self(method):
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            return self
        return wrapper































# ConfigLoader.py
class ConfigLoader:
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
    @staticmethod
    def load_config():
        # with open("config.json", "r") as config_file:
        #     config_dict = json.load(config_file)
        config_dict = json.load(ConfigLoader.config_file_json)

        def dict_to_namespace(d):
            return json.loads(json.dumps(d), object_hook=lambda d: SimpleNamespace(**d))
        
        return dict_to_namespace(config_dict)

config = ConfigLoader.load_config()



























class Logging:
    def tab():
        return " " * config.tab_size

    def clear_log_file():
        with open(config.logging.log_file_name, "w") as f:
            pass
    def log_to_file(message):
        time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        stack_depth = len(traceback.extract_stack()) - 1 - 10
        indentation = Logging.tab() * stack_depth
        log_message = f"{time_written}: {indentation}{message}"
        
        with open(config.logging.log_file_name, "a") as f:
            f.write(f"{log_message}\n")

    class LoggerMonad:
        def __init__(self, log_file_name):
            self.log_file_name = log_file_name
            self.current_intent = 0

        @property
        def current_intent(self):
            return self._current_intent
        
        @property
        def current_intent(self, level):
            self._current_intent = level
        
        @property
        def log_file_name(self):
            return self.log_file_name

        @Decorating.returns_self
        def clear_log_file(self):
            Logging.cLoggingear_log_file()

        @Decorating.returns_self
        def write(self, message):
            Logging.log_to_file(message)
        
        @Decorating.returns_self 
        def up(self):
            self.current_intent += 1
        
        @Decorating.returns_self    
        def down(self):
            self.current_intent -= 1
































# BlenderEX.py
class BlenderEX:
    @staticmethod
    def get_root_bone_of_armature(armature):
        return armature.data.edit_bones[armature.data.edit_bones.keys()[0]]

    @staticmethod
    def deselect_everything():
        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    def iter_hierarchy_inclusive(obj):
        yield obj
        for child in obj.children:
            yield from BlenderEX.iter_hierarchy_inclusive(child)
    @staticmethod
    def move_to_collection(obj, target_collection):
        for col in obj.users_collection:
            col.objects.unlink(obj)
        target_collection.objects.link(obj)

    @staticmethod
    def move_to_collection_with_nierarchy(obj, target_collection):
        Utils.map_action(
            BlenderEX.iter_hierarchy_inclusive(obj), 
            lambda x: BlenderEX.move_to_collection(x, target_collection)
        )

    @staticmethod
    def update_view():
        bpy.context.view_layer.update()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    @staticmethod
    def update_view_print(message):
        BlenderEX.update_view()
        print(message)
        Logging.log_to_file(message)

    # Select the object. I SAD: SELECT THE OBJECT
    @staticmethod
    def force_select_object(obj):
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        else:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

















































# passes ------------------------------------------------------------------

def fix_object_normal_pass(obj):
    if config.passes.fix_normals.attribute_name not in obj.keys() or obj[config.passes.fix_normals.attribute_name] is False:
        fix_object_normals(obj)
        Utils.update_view_print(f"Normals fixed for {obj.name}")

def fix_object_normals(obj):
    Utils.force_select_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')



def add_bone_to_armature(armature, bone_name="Bone.001", head=(0, 0, 0), tail=(0, 0, 1), parent_bone=None):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    new_bone = armature.data.edit_bones.new(bone_name)
    new_bone.head = head
    new_bone.tail = tail

    if parent_bone is not None:
        new_bone.parent = parent_bone
    else:
        new_bone.parent = Utils.get_root_bone_of_armature(armature)

    bpy.ops.object.mode_set(mode='OBJECT')

    return new_bone

def fill_object_with_vertex_weight(obj, bone_name, weight=1):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    vertex_group = obj.vertex_groups.new(name=bone_name)
    vertex_indices = [v.index for v in obj.data.vertices]
    vertex_group.add(vertex_indices, weight, 'REPLACE')

def has_armature_modifier(obj):
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            return True
    return False

def create_micro_bone_pass(obj, rig):
    mb_cnf = config.passes.create_micro_bone


    parent_bone = None
    if mb_cnf.micro_bone_parent in obj.keys():
        parent_bone = rig.data.edit_bones[obj[mb_cnf.micro_bone_parent]]

    name = f"{obj.name}__micro_bone"
    if mb_cnf.micro_bone_name in obj.keys():
        name = obj[mb_cnf.micro_bone_name]

    bone = add_bone_to_armature(rig, name, obj.location, obj.location, parent_bone)
    Utils.update_view_print(f"Created micro bone {bone.name} for {obj.name}")

    fill_object_with_vertex_weight(obj, bone.name, 1)
    Utils.update_view_print(f"Filled vertex weight for {obj.name}")

    pass

def apply_render_geometry_modifiers_pass(obj):
    if config.passes.apply_render_geometry_modifiers.enabled:
        apply_render_geometry_modifiers(obj)
        Utils.update_view_print(f"{Logging.tab()}Applied render modifiers to {obj.name}")

def apply_render_geometry_modifiers(obj):
    if obj.modifiers:
        for modifier in obj.modifiers:
            if modifier.show_render:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            else:
                print(f"Skipping modifier '{modifier.name}' (cz not enabled for render)")











































def run_export_pipline_for_rig(rig):
    Utils.update_view_print(f"Exporting for {rig.name} started")

    original_collection_of_the_rig = rig.users_collection[0]
    temporal_export_collection = bpy.data.collections.new(name="Export")
    bpy.context.scene.collection.children.link(temporal_export_collection)
    Utils.update_view_print(f"Created collection {temporal_export_collection.name}")

    # add rig and its childs to the "Export" collection
    Utils.move_to_collection_with_nierarchy(rig, temporal_export_collection)
    Utils.update_view_print(f"Hierarchy of {rig.name} moved to {temporal_export_collection.name}")


    # create game rig  ------------------------------------------------



    # processing meshes and exporting to unreal ------------------------------------------------

    meshes = []
    Utils.update_view_print(f"Collecting meshes of {rig.name}:")
    for obj in temporal_export_collection.all_objects:
        # only for geometry
        if not (
            obj is not None
            and hasattr(obj, 'type') 
            and obj.type is not None 
            and obj.type == "MESH"
        ):
            Utils.update_view_print(f"{Logging.tab()}Skipped {obj.name if obj else 'deez nust'}")
            continue

        meshes.append(obj)
        Utils.update_view_print(f"{Logging.tab()}{obj.name}")




    for obj in meshes:
        Utils.force_select_object(obj)

        Utils.update_view_print(f"Selected {obj.name}")

        # Make single user and apply visual transform
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


        # apply_render_geometry_modifiers_pass(obj)


        bpy.ops.object.visual_transform_apply()
        Utils.update_view_print(f"{Logging.tab()}Made single user and applied visual transform to {obj.name}")


        fix_object_normal_pass(obj)

        # create_micro_bone_pass(obj, rig)

        
        obj.data.name = f"{obj.name}__unique_mesh"
        Utils.update_view_print(f"{Logging.tab()}Renamed object data to {obj.data.name}")

        obj.select_set(False)
        Utils.deselect_everything()

        Utils.update_view_print(f"{Logging.tab()}Finished for {obj.name}")



    # Send to Unreal Engine all things from the "Export" collection
    if config.main.is_export_to_ue:
        Utils.update_view_print(f"Sending to Unreal started")
        bpy.ops.wm.send2ue()
        Utils.update_view_print(f"Sending to Unreal finished")

    # delete the "Export" collection
    bpy.data.collections.remove(temporal_export_collection)
    Utils.move_to_collection_with_nierarchy(rig, original_collection_of_the_rig)
    Utils.update_view_print(f"Moved {rig.name} to {original_collection_of_the_rig.name}")
    Utils.update_view_print(f"Exported rig and its childs {rig.name} finished")

    pass






































def main():
    # Save the current Blender file
    bpy.ops.wm.save_mainfile()

    Logging.clear_log_file()

    Utils.update_view_print("Saved the current Blender file")

    Utils.deselect_everything()

    # Get the objects to export
    rigs_to_export = [
            bpy.data.objects["shum_cloth_rig"],
            bpy.data.objects["shum_control_rig"]
        ]


    for rig in rigs_to_export:
        run_export_pipline_for_rig(rig)

    Utils.update_view_print(f"All rigs exported")
    Utils.update_view_print(f"SCRIPT FINISHED")

    # Revert all changes to the Blender file
    if config.main.is_revert_changes:
        bpy.ops.wm.revert_mainfile()




main()