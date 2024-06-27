import datetime
from functools import wraps
import inspect
import os
import traceback
import bpy
import json
from types import SimpleNamespace
from typing import TypeVar, Generic, Callable, Optional
from typing import *
import pprint





















































# Utils.py
class Utils:
    @staticmethod
    def recirsive_to_string(obj) -> str:
        string = ""
        for name, value in inspect.getmembers(obj):
            string += f"{name}: {value!r}\n"
            if inspect.ismodule(value):
                string += Utils.recirsive_to_string(value)
        return string
    
    # @staticmethod
    # def to_json(self) -> str:
    #     return json.dumps(self, default=lambda o: o.__dict__)

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
        "is_update_view_every_logging": true,
        "tab_size": 3,
        "this_file_name": "export_to_ue__custom_pipline.py",
        "log_file_name": "export_to_ue__custom_pipline.log",
        "log_file_path": "Y://___Projects___//PTTR.SP - Patternolitsadiya Shum for portfolio//300 Art"
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
    def get_log_file_full_path():
        return os.path.join(ConfigLoader.config.logging.log_file_path, ConfigLoader.config.logging.log_file_name)

    @staticmethod
    def load_config():
        config_dict = json.loads(ConfigLoader.config_file_json)
        obj = json.loads(json.dumps(config_dict), object_hook=lambda a: SimpleNamespace(**a))
        return obj

# Initialize the config
ConfigLoader.config = ConfigLoader.load_config()

























# Logging.py
@final
class Logging:

    @staticmethod
    def update_view():
        bpy.context.view_layer.update()
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

    @staticmethod
    def logged_method(method):
        method_signature = inspect.signature(method)
        is_takes_any_parameters = len(method_signature.parameters) > 0

        Logging.update_view()

        def two_lined(*args, **kwargs):
            Logging.logger.up()
            if is_takes_any_parameters:
                method_arguments = ", ".join(f"{name}={value!r}" for name, value in method_signature.bind(*args, **kwargs).arguments.items())
                pre_message = f"> {method.__name__}({method_arguments})"
            else:
                pre_message = f"> {method.__name__}()"
            Logging.logger.write(pre_message)

            result = OPTION.from_nullable(
                method(*args, **kwargs) if is_takes_any_parameters == True else method()
            )

            if ConfigLoader.config.logging.is_update_view_every_logging: 
                Logging.update_view()

            post_message = result.match(
                none = lambda: f"< {method.__name__} -> None", 
                some = lambda x: f"< {method.__name__} -> {x!r}")
            Logging.logger.write(post_message)
            Logging.logger.down()

            return result.match(none=lambda: None, some=lambda x: x)
        
        return two_lined # is good)

    @staticmethod
    def logged_method_hight(method):
        method_signature = inspect.signature(method)
        is_takes_any_parameters = len(method_signature.parameters) > 0

        def update_view():
            bpy.context.view_layer.update()
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

        def two_lined(*args, **kwargs):
            Logging.logger.up()
            if is_takes_any_parameters:
                method_arguments = ", ".join(f"{name}={value!r}" for name, value in method_signature.bind(*args, **kwargs).arguments.items())
                pre_message = f"> {method.__name__}({method_arguments})"
            else:
                pre_message = f"> {method.__name__}()"
            Logging.logger.write(pre_message)

            Logging.logger.up()
            result = OPTION.from_nullable(
                method(*args, **kwargs) if is_takes_any_parameters == True else method()
            )
            Logging.logger.down()

            if ConfigLoader.config.logging.is_update_view_every_logging: 
                update_view()

            post_message = result.match(
                none = lambda: f"< {method.__name__} -> None", 
                some = lambda x: f"< {method.__name__} -> {x!r}")
            Logging.logger.write(post_message)
            Logging.logger.down()

            return result.match(none=lambda: None, some=lambda x: x)
        
        return two_lined # is good)
    
    @staticmethod
    def tab() -> str:
        return " " * ConfigLoader.config.logging.tab_size
    
    @staticmethod
    def clear_log_file():
        with open(ConfigLoader.get_log_file_full_path(), "w") as f:
            pass

    @staticmethod
    def log_to_file(message, stack_depth=0):
        time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        indentation = ""
        for i in range(stack_depth):
            indentation += "." + Logging.tab()
        log_message = f"{time_written}: {indentation}{message}"
        
        with open(ConfigLoader.get_log_file_full_path(), "a") as f:
            f.write(f"{log_message}\n")

    @final
    class LoggerMonad:
        def __init__(self, log_file_name):
            self.log_file_name = log_file_name
            self.depth = 0

        # @Decorating.returns_self
        def clear_log_file(self):
            Logging.clear_log_file()

        # @Decorating.returns_self
        def write(self, message:str):
            Logging.log_to_file(message, self.depth)
        
        @Decorating.returns_self 
        def up(self):
            self.depth += 1
        
        @Decorating.returns_self    
        def down(self):
            self.depth -= 1

    # shared instance of logger for this file
    logger = LoggerMonad(ConfigLoader.config.logging.log_file_name)































# whole god damn it Game_Rig_Tools-221_B35_B36/ folder in here cz i dont give a shit on how to call operator with presets that i need)))))))0
@final
class GRT_Generate_Game_Rig:
    operator_settings = SimpleNamespace(**{
        # additional
        "Hierarchy_Mode" : 'RIGIFY',
        "Use_Legacy" : False,
        "Use_Regenerate_Rig" : False,
        # base from Default_-_keep_hierarchy.py
        "Extract_Mode": "DEFORM",
        "Flat_Hierarchy": True,
        "Disconnect_Bone": True,
        "Constraint_Type": "TRANSFORM",
        "Animator_Remove_BBone": False,
        "Animator_Disable_Deform": False,
        "Parent_To_Deform_Rig": True,
        "Deform_Armature_Name": "",
        "Deform_Remove_BBone": True,
        "Deform_Move_Bone_to_Layer1": True,
        "Deform_Set_Inherit_Rotation_True": True,
        "Deform_Set_Inherit_Scale_Full": True,
        "Deform_Set_Local_Location_True": True,
        "Deform_Remove_Non_Deform_Bone": True,
        "Deform_Unlock_Transform": True,
        "Deform_Remove_Shape": True,
        "Deform_Remove_All_Constraints": True,
        "Deform_Copy_Transform": True,
        "Deform_Bind_to_Deform_Rig": True,
        "Remove_Custom_Properties": True,
        "Remove_Animation_Data": True,
        "Show_Advanced": False
    })

    @staticmethod
    @Logging.logged_method
    def find_deform(bone, bones):
        if not "DEF-" in bone.name:
            new_name = bone.name.replace("ORG-", "DEF-")
            return bones.get(new_name)

    @staticmethod
    @Logging.logged_method
    def get_root(bone):
        if bone.parent:
            return GRT_Generate_Game_Rig.get_root(bone.parent)
        else:
            return bone
        
    @staticmethod
    @Logging.logged_method
    def invoke(presets, context):
        scn = context.scene
        Global_Settings = scn.GRT_Action_Bakery_Global_Settings
        # Action_Bakery = scn.GRT_Action_Bakery

        control_rig = Global_Settings.Source_Armature
        deform_rig = Global_Settings.Target_Armature

        if deform_rig:
            presets.Deform_Armature_Name = deform_rig.name
        elif control_rig:
            presets.Deform_Armature_Name = control_rig.name + "_deform"


    @staticmethod
    @Logging.logged_method
    def execute(operator_presets, context):
            
            GRT_Generate_Game_Rig.invoke(
                GRT_Generate_Game_Rig.operator_settings,
                bpy.context
            )

            object = context.object

            scn = context.scene
            Global_Settings = scn.GRT_Action_Bakery_Global_Settings
            Action_Bakery = scn.GRT_Action_Bakery

            control_rig = Global_Settings.Source_Armature
            deform_rig = Global_Settings.Target_Armature

            if operator_presets.Hierarchy_Mode == "KEEP_EXISTING":
                operator_presets.Rigify_Hierarchy_Fix = False
                operator_presets.Flat_Hierarchy = False
            if operator_presets.Hierarchy_Mode == "RIGIFY":
                operator_presets.Rigify_Hierarchy_Fix = True
                operator_presets.Flat_Hierarchy = False
            if operator_presets.Hierarchy_Mode == "FLAT":
                operator_presets.Rigify_Hierarchy_Fix = False
                operator_presets.Flat_Hierarchy = True
                

            Logging.update_view()


            if not operator_presets.Use_Legacy:
                object = control_rig


            if not object: return

            if object.type != "ARMATURE": return

            bpy.ops.object.mode_set(mode = "OBJECT")

            ORI_Edit_Bones = object.data.bones

            for bone in ORI_Edit_Bones:

                if operator_presets.Animator_Remove_BBone:
                    bone.bbone_segments = 0


            game_rig = None

            if not operator_presets.Use_Legacy:
                if operator_presets.Use_Regenerate_Rig:
                    game_rig = deform_rig
                    game_rig.hide_set(False)
                    game_rig.hide_viewport = False

            if not game_rig:
                game_rig = object.copy()
                game_rig.name = operator_presets.Deform_Armature_Name
                if not operator_presets.Use_Legacy:
                    Global_Settings.Target_Armature = game_rig

            game_rig.display_type = "SOLID"
            game_rig.show_in_front = True
            game_rig.data = object.data.copy()

            if not bpy.context.collection.objects.get(game_rig.name):

                bpy.context.collection.objects.link(game_rig)

            bpy.ops.object.select_all(action="DESELECT")
            game_rig.select_set(True)
            context.view_layer.objects.active = game_rig
            bpy.ops.object.mode_set(mode = "EDIT")

            Edit_Bones = game_rig.data.edit_bones

            if operator_presets.Rigify_Hierarchy_Fix:
                # @Logging.logged_method
                def apply_Rigify_Hierarchy_Fix(bone):
                    if bone.use_deform:
                        if bone.parent:
                            if not bone.parent.use_deform:
                                recursive_parent = bone.parent_recursive
                                
                                for f in recursive_parent:
                                    
                                    if f.use_deform:
                                        bone.parent = f
                                        break
                                    else:
                                        b = GRT_Generate_Game_Rig.find_deform(f, Edit_Bones)
                                        if b:
                                            if not b.name == bone.name:
                                                if b.use_deform:
                                                    bone.parent = b
                                                    break
                for bone in Edit_Bones:
                    apply_Rigify_Hierarchy_Fix(bone)

            if operator_presets.Remove_Animation_Data:

                game_rig.animation_data_clear()
                game_rig.data.animation_data_clear()

            if operator_presets.Deform_Move_Bone_to_Layer1:
                for i, layer in enumerate(game_rig.data.layers):
                    if i == 0:
                        game_rig.data.layers[i] = True
                    else:
                        game_rig.data.layers[i] = False

            # @Logging.logged_method
            def process_bone(bone):

                    if operator_presets.Flat_Hierarchy:
                        bone.parent = None
                    if operator_presets.Disconnect_Bone:
                        bone.use_connect = False

                    if operator_presets.Remove_Custom_Properties:
                        bone.id_properties_clear()
                        # if bone.get("_RNA_UI"):
                        #     for property in bone["_RNA_UI"]:
                        #         del bone[property]

                    if operator_presets.Deform_Remove_BBone:
                        bone.bbone_segments = 0

                    if operator_presets.Deform_Set_Inherit_Rotation_True:
                        bone.use_inherit_rotation = True

                    if operator_presets.Deform_Set_Local_Location_True:
                        bone.use_local_location = True

                    if operator_presets.Deform_Set_Inherit_Scale_Full:
                        bone.inherit_scale = "FULL"

                    if operator_presets.Deform_Move_Bone_to_Layer1:
                        for i, layer in enumerate(bone.layers):
                            if i == 0:
                                bone.layers[i] = True
                            else:
                                bone.layers[i] = False

                    if operator_presets.Deform_Remove_Non_Deform_Bone:
                        if operator_presets.Extract_Mode == "SELECTED":
                            if not bone.select:
                                Edit_Bones.remove(bone)

                        if operator_presets.Extract_Mode == "DEFORM":
                            if not bone.use_deform:
                                Edit_Bones.remove(bone)

                        if operator_presets.Extract_Mode == "SELECTED_DEFORM":
                            if not bone.select:
                                if not bone.use_deform:
                                    Edit_Bones.remove(bone)

                        if operator_presets.Extract_Mode == "DEFORM_AND_SELECTED":
                            if not bone.use_deform and not bone.select:
                                Edit_Bones.remove(bone)
            for bone in Edit_Bones:
                process_bone(bone)

            bpy.ops.object.mode_set(mode = "POSE")
            game_rig.data.bones.update()

            if operator_presets.Remove_Custom_Properties:
                # if game_rig.get("_RNA_UI"):
                #     for property in game_rig["_RNA_UI"]:
                #         del game_rig[property]

                game_rig.id_properties_clear()
                game_rig.data.id_properties_clear()
                # if game_rig.data.get("_RNA_UI"):
                #     for property in game_rig.data["_RNA_UI"]:
                #         del game_rig.data[property]

            Pose_Bones = game_rig.pose.bones

            # @Logging.logged_method
            def process_pose_bone(bone):
                if operator_presets.Remove_Custom_Properties:
                    if bone.get("_RNA_UI"):
                        for property in bone["_RNA_UI"]:
                            del bone[property]

                if operator_presets.Deform_Remove_Shape:
                    bone.custom_shape = None

                if operator_presets.Deform_Unlock_Transform:
                    bone.lock_location[0] = False
                    bone.lock_location[1] = False
                    bone.lock_location[2] = False

                    bone.lock_scale[0] = False
                    bone.lock_scale[1] = False
                    bone.lock_scale[2] = False

                    bone.lock_rotation_w = False
                    bone.lock_rotation[0] = False
                    bone.lock_rotation[1] = False
                    bone.lock_rotation[2] = False

                if operator_presets.Deform_Remove_All_Constraints:
                    for constraint in bone.constraints:
                        bone.constraints.remove(constraint)

                # if self.Deform_Copy_Transform:

                if operator_presets.Constraint_Type == "TRANSFORM":
                    constraint = bone.constraints.new("COPY_TRANSFORMS")
                    constraint.target = object
                    constraint.subtarget = object.data.bones.get(bone.name).name

                if operator_presets.Constraint_Type == "LOTROT":
                    constraint = bone.constraints.new("COPY_LOCATION")
                    constraint.target = object
                    constraint.subtarget = object.data.bones.get(bone.name).name

                    constraint = bone.constraints.new("COPY_ROTATION")
                    constraint.target = object
                    constraint.subtarget = object.data.bones.get(bone.name).name

                    if operator_presets.Copy_Root_Scale:

                        root = None

                        if operator_presets.Auto_Find_Root:
                            root = GRT_Generate_Game_Rig.get_root(object.data.bones.get(bone.name))
                        else:
                            root = object.data.bones.get(operator_presets.Root_Bone_Name)

    
                        if root:
                            constraint = bone.constraints.new("COPY_SCALE")
                            constraint.target = object
                            constraint.subtarget = root.name


                if operator_presets.Constraint_Type == "NONE":
                    pass
            for bone in Pose_Bones:
                process_pose_bone(bone)


            bpy.ops.object.mode_set(mode = "OBJECT")
            if operator_presets.Deform_Bind_to_Deform_Rig:
                for obj in bpy.data.objects:
                    for modifier in obj.modifiers:
                        if modifier.type == "ARMATURE":
                            if modifier.object == object:
                                modifier.object = game_rig
                                if operator_presets.Parent_To_Deform_Rig:
                                    obj.parent = game_rig
                                    obj.matrix_parent_inverse = game_rig.matrix_world.inverted()

            for bone in object.data.bones:
                if operator_presets.Animator_Disable_Deform:

                    bone.use_deform = False



















































# BlenderEX.py
class BlenderEX:
    @staticmethod
    @Logging.logged_method
    def get_root_bone_of_armature(armature):
        return armature.data.edit_bones[armature.data.edit_bones.keys()[0]]

    @staticmethod
    @Logging.logged_method
    def deselect_everything():
        bpy.ops.object.select_all(action="DESELECT")

    @staticmethod
    @Logging.logged_method
    def iter_hierarchy_inclusive(obj):
        yield obj
        for child in obj.children:
            yield from BlenderEX.iter_hierarchy_inclusive(child)

    @staticmethod
    @Logging.logged_method
    def iter_hierarchy_exclusive(obj):
        """iter_hierarchy_exclusive(obj): yields all children of obj, but not obj itself"""
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
    def parent_to_other_object(obj, target_object):
        while obj.parent:
            obj.parent = None
        target_object.objects.link(obj)

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
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

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
        
@Logging.logged_method
def fix_object_normals(obj):
    BlenderEX.force_select_object(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")



@Logging.logged_method
def add_bone_to_armature(armature, bone_name="Bone.001", head=(0, 0, 0), tail=(0, 0, 1), parent_bone=None):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")

    new_bone = armature.data.edit_bones.new(bone_name)
    new_bone.head = head
    new_bone.tail = tail

    if parent_bone is not None:
        new_bone.parent = parent_bone
    else:
        new_bone.parent = BlenderEX.get_root_bone_of_armature(armature)

    bpy.ops.object.mode_set(mode="OBJECT")

    return new_bone

@Logging.logged_method
def fill_object_with_vertex_weight(obj, bone_name, weight=1):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="OBJECT")
    vertex_group = obj.vertex_groups.new(name=bone_name)
    vertex_indices = [v.index for v in obj.data.vertices]
    vertex_group.add(vertex_indices, weight, "REPLACE")

@Logging.logged_method
def has_armature_modifier(obj):
    for mod in obj.modifiers:
        if mod.type == "ARMATURE":
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

    fill_object_with_vertex_weight(obj, bone.name, 1)

    pass

@Logging.logged_method
def apply_render_geometry_modifiers_pass(obj):
    if ConfigLoader.config.passes.apply_render_geometry_modifiers.enabled:
        apply_render_geometry_modifiers(obj)

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

    original_collection_of_the_rig = rig.users_collection[0]
    temporal_export_collection = bpy.data.collections.new(name="Export")
    bpy.context.scene.collection.children.link(temporal_export_collection)

    # add rig and its childs to the "Export" collection
    BlenderEX.move_to_collection_with_nierarchy(rig, temporal_export_collection)


    # create game rig ------------------------------------------------
    gtr_global_settings = bpy.context.scene.GRT_Action_Bakery_Global_Settings
    # Logging.logger.write(f"scn.GRT_Action_Bakery_Global_Settings:\n{Utils.recirsive_to_string(gtr_global_settings)}\n")
    gtr_action_bakery = bpy.context.scene.GRT_Action_Bakery
    # Logging.logger.write(f"scn.GRT_Action_Bakery:\n{Utils.recirsive_to_string(gtr_action_bakery)}\n")

    gtr_global_settings.Source_Armature = rig
    Logging.logger.write(f"Source_Armature {rig.name}")

    # game_rig = bpy.data.objects[rig.name + "_deform"]
    # gtr_global_settings.Target_Armature = game_rig
    # Logging.logger.write(f"Target_Armature {game_rig.name}")










    GRT_Generate_Game_Rig.execute(
        GRT_Generate_Game_Rig.operator_settings, 
        bpy.context
    )










    # # processing meshes and exporting to unreal ------------------------------------------------
    # meshes = []

    # @Logging.logged_method_hight
    # def filter_meshes():
    #     for obj in temporal_export_collection.all_objects:
    #         # only for geometry
    #         if not (
    #             obj is not None
    #             and hasattr(obj, "type") 
    #             and obj.type is not None 
    #             and obj.type == "MESH"
    #         ):
    #             Logging.logger.write(f"Skipped {obj.name if obj else 'deez nust'}")
    #             continue

    #         meshes.append(obj)
    #         Logging.logger.write(f"{obj.name}")
    # filter_meshes()


    # @Logging.logged_method_hight
    # def export_rig():
    #     for obj in meshes:
    #         BlenderEX.force_select_object(obj)

    #         # Make single user and apply visual transform
    #         bpy.ops.object.make_single_user(object=True, obdata=True)
    #         bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


    #         bpy.ops.object.visual_transform_apply()
    #         Logging.logger.write(f"Made single user and applied visual transform to {obj.name}")


    #         fix_object_normal_pass(obj)

    #         # create_micro_bone_pass(obj, rig)
            
    #         obj.data.name = f"{obj.name}__unique_mesh"
    #         Logging.logger.write(f"Renamed object data to {obj.data.name}")

    #         obj.select_set(False)
    #         BlenderEX.deselect_everything()

    #         Logging.logger.write(f"Finished for {obj.name}")
    # export_rig()



    # # Send to Unreal Engine all things from the "Export" collection
    # if ConfigLoader.config.main.is_export_to_ue:
    #     Logging.logger.write(f"Sending to Unreal started")
    #     bpy.ops.wm.send2ue()
    #     Logging.logger.write(f"Sending to Unreal finished")

    # # delete the "Export" collection
    # bpy.data.collections.remove(temporal_export_collection)
    # BlenderEX.move_to_collection_with_nierarchy(rig, original_collection_of_the_rig)
    # Logging.logger.write(f"Moved {rig.name} to {original_collection_of_the_rig.name}")
    # Logging.logger.write(f"Exported rig and its childs {rig.name} finished")

    pass





































@Logging.logged_method
def main():
    # Save the current Blender file
    bpy.ops.wm.save_mainfile()

    Logging.logger.write("Saved the current Blender file")

    BlenderEX.deselect_everything()

    # Get the objects to export
    rigs_to_export = [
            # bpy.data.objects["shum_cloth_rig"],
            bpy.data.objects["shum_control_rig"]
        ]

    for rig in rigs_to_export:
        run_export_pipline_for_rig(rig)

    Logging.logger.write(f"All rigs exported")
    Logging.logger.write(f"SCRIPT FINISHED")

    # Revert all changes to the Blender file
    if ConfigLoader.config.main.is_revert_changes:
        bpy.ops.wm.revert_mainfile()


Logging.clear_log_file()
main()