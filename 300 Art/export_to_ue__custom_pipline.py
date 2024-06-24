import bpy
import datetime
import traceback



# constants ------------------------------------------------------------------
# main settings
IS_REVERT_CHANGES = False
IS_EXPORT_TO_UE = False
# logging
TAB_SIZE = 3
THIS_FILE_NAME = "export_to_ue__custom_pipline.py"
LOG_FILE_NAME = f"{THIS_FILE_NAME}.log" 



# optional passes pr object settings ------------------------------------------------------------------
# normals
DONT_FIX_NORMALS = "dont_fix_normals"
# create a bone for this object that will be used like its transform origin
# currently depends on having a parent armature and an armature modifier and having no vertex groups
CREATE_MICRO_BONE = "create_micro_bone" # optional
MICRO_BONE_NAME = "micro_bone_name" # optional name of the bone
MICRO_BONE_PARENT = "micro_bone_parent" # optional name of the bone that will be parent of this bone to
#
IS_APPLY_RENDER_OR_VIEW_MODIFIERS = False


# utils ------------------------------------------------------------------

def map_action(iterator, func):
    for item in iterator:
        func(item)

def map_iter(iterator, func):
    for item in iterator:
        yield func(item)

def map_iter_pipe(iterator, *funcs):
    for item in iterator:
        for func in funcs:
            item = func(item)
        yield item

def execute_pass_queue(obj, *fn):
    for fn in fn:
        fn(obj)

def do(obj, fn):
    fn()
    return obj

def btw(fn):
    fn()
    return lambda obj: obj

class Deco:
    @staticmethod
    def returns_self(method):
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            return self
        return wrapper


# logging ------------------------------------------------------------------

class LoggingH:
    @staticmethod
    def tab():
        return " " * TAB_SIZE
    
    @staticmethod
    def clear_log_file():
        with open(LOG_FILE_NAME, "w") as f:
            pass

    @staticmethod
    def log_to_file(message):
        time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        stack_depth = len(traceback.extract_stack()) - 1 - 10
        indentation = LoggingH.tab() * stack_depth
        log_message = f"{time_written}: {indentation}{message}"
        
        with open(LOG_FILE_NAME, "a") as f:
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

    @Deco.returns_self
    def clear_log_file(self):
        LoggingH.clear_log_file()

    @Deco.returns_self
    def write(self, message):
        LoggingH.log_to_file(message)
    
    @Deco.returns_self 
    def up(self):
        self.current_intent += 1
    
    @Deco.returns_self    
    def down(self):
        self.current_intent -= 1



# blender functions ------------------------------------------------------------------

def deselect_everything():
    bpy.ops.object.select_all(action='DESELECT')


def iter_hierarchy_inclusive(obj):
    yield obj
    for child in obj.children:
        yield from iter_hierarchy_inclusive(child)

def move_to_collection(obj, target_collection):
    for col in obj.users_collection:
        col.objects.unlink(obj)
    target_collection.objects.link(obj)

def move_to_collection_with_nierarchy(obj, target_collection):
    map_action(
        iter_hierarchy_inclusive(obj), 
        lambda x: move_to_collection(x, target_collection)
    )

def update_view():
    bpy.context.view_layer.update()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def update_view_print(message):
    update_view()
    print(message)
    LoggingH.log_to_file(message)

# def force_rename_collection(collection, name):
#     collection.name = name

# Select the object. I SAD: SELECT THE OBJECT
def force_select_object(obj):
    if obj.name in bpy.context.view_layer.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

# def temporal_select_object(obj, fn):
#     old_active = bpy.context.view_layer.objects.active
#     old_selected = bpy.context.selected_objects

#     force_select_object(obj)
#     fn()

#     bpy.context.view_layer.objects.active = old_active
#     for ob in old_selected:
#         ob.select_set(True)



# passes ------------------------------------------------------------------

def fix_object_normal_pass(obj):
    if DONT_FIX_NORMALS not in obj.keys() or obj[DONT_FIX_NORMALS] is False:
        fix_object_normals(obj)
        update_view_print(f"Normals fixed for {obj.name}")

def fix_object_normals(obj):
    force_select_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def get_root_bone_of_armature(armature):
    return armature.data.edit_bones[armature.data.edit_bones.keys()[0]]

def add_bone_to_armature(armature, bone_name="Bone.001", head=(0, 0, 0), tail=(0, 0, 1), parent_bone=None):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    new_bone = armature.data.edit_bones.new(bone_name)
    new_bone.head = head
    new_bone.tail = tail

    if parent_bone is not None:
        new_bone.parent = parent_bone
    else:
        new_bone.parent = get_root_bone_of_armature(armature)

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
    # wants_implicitly = obj.parent and obj.parent.type == "ARMATURE" and has_armature_modifier(obj) and len(obj.vertex_groups) == 0
    # wants_explicitly = hasattr(obj, CREATE_MICRO_BONE) and obj[CREATE_MICRO_BONE]
    # if wants_implicitly or wants_explicitly:
    #     return

    parent_bone = None
    if MICRO_BONE_PARENT in obj.keys():
        parent_bone = rig.data.edit_bones[obj[MICRO_BONE_PARENT]]

    name = f"{obj.name}__micro_bone"
    if MICRO_BONE_NAME in obj.keys():
        name = obj[MICRO_BONE_NAME]

    bone = add_bone_to_armature(rig, name, obj.location, obj.location, parent_bone)
    update_view_print(f"Created micro bone {bone.name} for {obj.name}")

    fill_object_with_vertex_weight(obj, bone.name, 1)
    update_view_print(f"Filled vertex weight for {obj.name}")

    pass

def apply_render_geometry_modifiers_pass(obj):
    if IS_APPLY_RENDER_OR_VIEW_MODIFIERS:
        apply_render_geometry_modifiers(obj)
        update_view_print(f"{LoggingH.tab()}Applied render modifiers to {obj.name}")

def apply_render_geometry_modifiers(obj):
    if obj.modifiers:
        for modifier in obj.modifiers:
            if modifier.show_render:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            else:
                print(f"Skipping modifier '{modifier.name}' (cz not enabled for render)")


def export_armature_with_its_geometry_to_ue(rig):
    update_view_print(f"Exporting for {rig.name} started")

    original_collection_of_the_rig = rig.users_collection[0]
    temporal_export_collection = bpy.data.collections.new(name="Export")
    bpy.context.scene.collection.children.link(temporal_export_collection)
    update_view_print(f"Created collection {temporal_export_collection.name}")

    # add rig and its childs to the "Export" collection
    move_to_collection_with_nierarchy(rig, temporal_export_collection)
    update_view_print(f"Hierarchy of {rig.name} moved to {temporal_export_collection.name}")


    meshes = []
    update_view_print(f"Collecting meshes of {rig.name}:")
    for obj in temporal_export_collection.all_objects:
        # only for geometry
        if not (
            obj is not None
            and hasattr(obj, 'type') 
            and obj.type is not None 
            and obj.type == "MESH"
        ):
            update_view_print(f"{LoggingH.tab()}Skipped {obj.name if obj else 'deez nust'}")
            continue

        meshes.append(obj)
        update_view_print(f"{LoggingH.tab()}{obj.name}")



    # map_iter_pipe( # no needs really to use it on root level, maybe inside other functions is ok
    #     meshes,
    #     lambda x: (update_view_print(f"Selected {x.name}"), x),
    #     # Make single user and apply visual transform
    #     lambda x: (bpy.ops.object.make_single_user(object=True, obdata=True), x),
    #     lambda x: (bpy.ops.object.transform_apply(location=True, rotation=True, scale=True), x),
    #     # lambda x: (x.data.name = f"{x.name}__unique_mesh", x),
    #     apply_render_geometry_modifiers_pass,
    #     lambda x: (bpy.ops.object.visual_transform_apply(), x),
    #     fix_object_normal_pass,
    #     btw(lambda x: fill_object_with_vertex_weight(x, "__micro_bone", 1)),
    #     lambda x: create_micro_bone_pass(x, rig),
    #     lambda x: (x.select_set(False), x)
    # )



    for obj in meshes:
        force_select_object(obj)

        # execute_pass_queue(
        #     obj, 
        #     lambda o: fix_object_normal_pass(o),  
        #     create_micro_bone_pass, 
        #     apply_render_geometry_modifiers_pass
        # )

        update_view_print(f"Selected {obj.name}")

        # Make single user and apply visual transform
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


        # apply_render_geometry_modifiers_pass(obj)


        bpy.ops.object.visual_transform_apply()
        update_view_print(f"{LoggingH.tab()}Made single user and applied visual transform to {obj.name}")


        fix_object_normal_pass(obj)

        # create_micro_bone_pass(obj, rig)

        
        obj.data.name = f"{obj.name}__unique_mesh"
        update_view_print(f"{LoggingH.tab()}Renamed object data to {obj.data.name}")

        obj.select_set(False)
        deselect_everything()

        update_view_print(f"{LoggingH.tab()}Finished for {obj.name}")



    # Send to Unreal Engine all things from the "Export" collection
    if IS_EXPORT_TO_UE:
        update_view_print(f"Sending to Unreal started")
        bpy.ops.wm.send2ue()
        update_view_print(f"Sending to Unreal finished")

    # delete the "Export" collection
    bpy.data.collections.remove(temporal_export_collection)
    move_to_collection_with_nierarchy(rig, original_collection_of_the_rig)
    update_view_print(f"Moved {rig.name} to {original_collection_of_the_rig.name}")
    update_view_print(f"Exported rig and its childs {rig.name} finished")

    pass






def main():
    # Save the current Blender file
    bpy.ops.wm.save_mainfile()

    LoggingH.clear_log_file()

    update_view_print("Saved the current Blender file")

    deselect_everything()

    # Get the objects to export
    rigs_to_export = [
            bpy.data.objects["shum_cloth_rig"],
            bpy.data.objects["shum_control_rig"]
        ]

    for rig in rigs_to_export:
        export_armature_with_its_geometry_to_ue(rig)

    update_view_print(f"All rigs exported")
    update_view_print(f"SCRIPT FINISHED")

    # Revert all changes to the Blender file
    if IS_REVERT_CHANGES:
        bpy.ops.wm.revert_mainfile()




# Running the sync function
main()


