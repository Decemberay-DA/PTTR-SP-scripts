import datetime
from functools import wraps
import inspect
import traceback
import bpy
import json
from types import SimpleNamespace
from typing import TypeVar, Generic, Callable, Optional
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



A = TypeVar("A")
@final
class Option(Generic[A]): # wheel reinvented))))
    def __init__(self, is_some, value:A):
        self._is_some = is_some
        self._value = value
    
    @property
    def is_none(self) -> bool:
        return not self._is_some
    
    @property
    def is_some(self) -> bool:
        return self._is_some
    
    def unwrap(self) -> A:
        return self._value
    
    def match(self, none = lambda: None, some = lambda x: x):
        if self.is_some:
            return some(self._value)
        else:
            return none()
    
    def switch(self, none = lambda: None, some = lambda x: x) -> None:
        if self.is_some:
            some(self._value)
        else:
            none()

@final
class OPTION:
    @staticmethod
    def none() -> Option[None]:
        return Option(False, None)
    
    @staticmethod
    def some(value: A) -> Option[A]:
        return Option(True, value)
    
    @staticmethod
    def from_nullable(value: Optional[A]) -> Option[Optional[A]]:
        if value is None:
            return OPTION.none()
        else:
            return OPTION.some(value)
        
    @staticmethod
    def from_emptyable_collection(value: Optional[A]) -> Option[Optional[A]]:
        if value is None or len(value) == 0:
            return OPTION.none()
        else:
            return OPTION.some(value)




























# ConfigLoader.py
@final
class ConfigLoader:
    config_file_json = """
{
    "main": {
        "is_revert_changes": false,
        "is_export_to_ue": false
    },
    "logging": {
        "tab_size": 3,
        "this_file_name": "ExporterScript.py",
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

    @classmethod
    def _load_config(cls):
        config_dict = json.loads(cls.config_file_json)
        obj = json.loads(json.dumps(config_dict), object_hook=lambda a: SimpleNamespace(**a))
        return obj

# Initialize the config
ConfigLoader.config = ConfigLoader._load_config()

























# Logging.py
@final
class Logging:
    @staticmethod
    def logged_method(method):
        method_signature = inspect.signature(method)
        is_takes_any_parameters = len(method_signature.parameters) > 0

        def both(*args, **kwargs):
            Logging.logger.up()
            if is_takes_any_parameters:
                method_arguments = ", ".join(f"{name}={value!r}" for name, value in method_signature.bind(*args, **kwargs).arguments.items())
                pre_message = f"{method.__name__} started with arguments: {method_arguments}"
            else:
                pre_message = f"{method.__name__} started without arguments"
            Logging.logger.write(pre_message)

            result = OPTION.from_nullable(
                method(*args, **kwargs) if is_takes_any_parameters == True else method()
            )

            post_message = result.match(
                none = lambda: f"{method.__name__} finished without result", 
                some = lambda x: f"{method.__name__} finished with result: {x!r}")
            Logging.logger.write(post_message)
            Logging.logger.down()

            return result.match(none=lambda: None, some=lambda x: x)
        
        return both # is good)
    
    @staticmethod
    def tab():
        return " " * ConfigLoader.config.logging.tab_size
    
    @staticmethod
    def clear_log_file():
        with open(ConfigLoader.config.logging.log_file_name, "w") as _:
            pass

    @staticmethod
    def log_to_file(message, stack_depth=0):
        time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        # stack_depth = len(traceback.extract_stack()) - 1 - 10
        indentation = Logging.tab() * stack_depth
        log_message = f"{time_written}: {indentation}{message}"
        
        with open(ConfigLoader.config.logging.log_file_name, "a") as f:
            f.write(f"{log_message}\n")

    @final
    class LoggerMonad:
        def __init__(self, log_file_name):
            self.log_file_name = log_file_name
            self.current_intent = 0

        @Decorating.returns_self
        def clear_log_file(self):
            Logging.clear_log_file()

        @Decorating.returns_self
        def write(self, message):
            Logging.log_to_file(message, self.current_intent)
        
        @Decorating.returns_self 
        def up(self):
            self.current_intent += 1
        
        @Decorating.returns_self    
        def down(self):
            self.current_intent -= 1

    # shared instance of logger for this file
    logger = LoggerMonad(ConfigLoader.config.logging.log_file_name)































# BlenderEX.py
class BlenderEX:
    @staticmethod
    @Logging.logged_method
    def get_root_bone_of_armature(armature):
        return armature.data.edit_bones[armature.data.edit_bones.keys()[0]]

    @staticmethod
    @Logging.logged_method
    def deselect_everything():
        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    @Logging.logged_method
    def iter_hierarchy_inclusive(obj):
        yield obj
        for child in obj.children:
            yield from BlenderEX.iter_hierarchy_inclusive(child)

    @staticmethod
    @Logging.logged_method
    def move_to_collection(obj, target_collection):
        for col in obj.users_collection:
            col.objects.unlink(obj)
        target_collection.objects.link(obj)

    @staticmethod
    @Logging.logged_method
    def move_to_collection_with_nierarchy(obj, target_collection):
        Utils.map_action(
            BlenderEX.iter_hierarchy_inclusive(obj), 
            lambda x: BlenderEX.move_to_collection(x, target_collection)
        )

    @staticmethod
    @Logging.logged_method
    def update_view():
        bpy.context.view_layer.update()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    @staticmethod
    # @Logging.logged_method
    def update_view_print(message):
        BlenderEX.update_view()
        print(message)
        Logging.log_to_file(message)

    # Select the object. I SAD: SELECT THE OBJECT
    @staticmethod
    @Logging.logged_method
    def force_select_object(obj):
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        else:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

















































# passes ------------------------------------------------------------------
@Logging.logged_method
def fix_object_normal_pass(obj):
    if ConfigLoader.config.passes.fix_normals.attribute_name not in obj.keys() or obj[ConfigLoader.config.passes.fix_normals.attribute_name] is False:
        fix_object_normals(obj)
        BlenderEX.update_view_print(f"Normals fixed for {obj.name}")
        
@Logging.logged_method
def fix_object_normals(obj):
    BlenderEX.force_select_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')



@Logging.logged_method
def add_bone_to_armature(armature, bone_name="Bone.001", head=(0, 0, 0), tail=(0, 0, 1), parent_bone=None):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    new_bone = armature.data.edit_bones.new(bone_name)
    new_bone.head = head
    new_bone.tail = tail

    if parent_bone is not None:
        new_bone.parent = parent_bone
    else:
        new_bone.parent = BlenderEX.get_root_bone_of_armature(armature)

    bpy.ops.object.mode_set(mode='OBJECT')

    return new_bone

@Logging.logged_method
def fill_object_with_vertex_weight(obj, bone_name, weight=1):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    vertex_group = obj.vertex_groups.new(name=bone_name)
    vertex_indices = [v.index for v in obj.data.vertices]
    vertex_group.add(vertex_indices, weight, 'REPLACE')

@Logging.logged_method
def has_armature_modifier(obj):
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            return True
    return False

@Logging.logged_method
def create_micro_bone_pass(obj, rig):
    mb_cnf = ConfigLoader.config.passes.create_micro_bone


    parent_bone = None
    if mb_cnf.micro_bone_parent in obj.keys():
        parent_bone = rig.data.edit_bones[obj[mb_cnf.micro_bone_parent]]

    name = f"{obj.name}__micro_bone"
    if mb_cnf.micro_bone_name in obj.keys():
        name = obj[mb_cnf.micro_bone_name]

    bone = add_bone_to_armature(rig, name, obj.location, obj.location, parent_bone)
    BlenderEX.update_view_print(f"Created micro bone {bone.name} for {obj.name}")

    fill_object_with_vertex_weight(obj, bone.name, 1)
    BlenderEX.update_view_print(f"Filled vertex weight for {obj.name}")

    pass

@Logging.logged_method
def apply_render_geometry_modifiers_pass(obj):
    if ConfigLoader.config.passes.apply_render_geometry_modifiers.enabled:
        apply_render_geometry_modifiers(obj)
        BlenderEX.update_view_print(f"{Logging.tab()}Applied render modifiers to {obj.name}")

@Logging.logged_method
def apply_render_geometry_modifiers(obj):
    if obj.modifiers:
        for modifier in obj.modifiers:
            if modifier.show_render:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            else:
                print(f"Skipping modifier '{modifier.name}' (cz not enabled for render)")











































@Logging.logged_method
def run_export_pipline_for_rig(rig):
    BlenderEX.update_view_print(f"Exporting for {rig.name} started")

    original_collection_of_the_rig = rig.users_collection[0]
    temporal_export_collection = bpy.data.collections.new(name="Export")
    bpy.context.scene.collection.children.link(temporal_export_collection)
    BlenderEX.update_view_print(f"Created collection {temporal_export_collection.name}")

    # add rig and its childs to the "Export" collection
    BlenderEX.move_to_collection_with_nierarchy(rig, temporal_export_collection)
    BlenderEX.update_view_print(f"Hierarchy of {rig.name} moved to {temporal_export_collection.name}")


    # create game rig  ------------------------------------------------



    # processing meshes and exporting to unreal ------------------------------------------------

    meshes = []
    BlenderEX.update_view_print(f"Collecting meshes of {rig.name}:")
    for obj in temporal_export_collection.all_objects:
        # only for geometry
        if not (
            obj is not None
            and hasattr(obj, 'type') 
            and obj.type is not None 
            and obj.type == "MESH"
        ):
            BlenderEX.update_view_print(f"{Logging.tab()}Skipped {obj.name if obj else 'deez nust'}")
            continue

        meshes.append(obj)
        BlenderEX.update_view_print(f"{Logging.tab()}{obj.name}")




    for obj in meshes:
        BlenderEX.force_select_object(obj)

        BlenderEX.update_view_print(f"Selected {obj.name}")

        # Make single user and apply visual transform
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


        # apply_render_geometry_modifiers_pass(obj)


        bpy.ops.object.visual_transform_apply()
        BlenderEX.update_view_print(f"{Logging.tab()}Made single user and applied visual transform to {obj.name}")


        fix_object_normal_pass(obj)

        # create_micro_bone_pass(obj, rig)

        
        obj.data.name = f"{obj.name}__unique_mesh"
        BlenderEX.update_view_print(f"{Logging.tab()}Renamed object data to {obj.data.name}")

        obj.select_set(False)
        BlenderEX.deselect_everything()

        BlenderEX.update_view_print(f"{Logging.tab()}Finished for {obj.name}")



    # Send to Unreal Engine all things from the "Export" collection
    if ConfigLoader.config.main.is_export_to_ue:
        BlenderEX.update_view_print(f"Sending to Unreal started")
        bpy.ops.wm.send2ue()
        BlenderEX.update_view_print(f"Sending to Unreal finished")

    # delete the "Export" collection
    bpy.data.collections.remove(temporal_export_collection)
    BlenderEX.move_to_collection_with_nierarchy(rig, original_collection_of_the_rig)
    BlenderEX.update_view_print(f"Moved {rig.name} to {original_collection_of_the_rig.name}")
    BlenderEX.update_view_print(f"Exported rig and its childs {rig.name} finished")

    pass






































def main():
    # Save the current Blender file
    bpy.ops.wm.save_mainfile()

    Logging.clear_log_file()

    BlenderEX.update_view_print("Saved the current Blender file")

    BlenderEX.deselect_everything()

    # Get the objects to export
    rigs_to_export = [
            bpy.data.objects["shum_cloth_rig"],
            bpy.data.objects["shum_control_rig"]
        ]

    for rig in rigs_to_export:
        run_export_pipline_for_rig(rig)

    BlenderEX.update_view_print(f"All rigs exported")
    BlenderEX.update_view_print(f"SCRIPT FINISHED")

    # Revert all changes to the Blender file
    if ConfigLoader.config.main.is_revert_changes:
        bpy.ops.wm.revert_mainfile()




main()