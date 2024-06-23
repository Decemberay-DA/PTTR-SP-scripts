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
CREATE_MICRO_BONE = "create_micro_bone" # optional
MICRO_BONE_NAME = "micro_bone_name" # optional name of the bone
MICRO_BONE_PARENT = "micro_bone_parent" # optional name of the bone that will be parent of this bone to
#
IS_APPLY_RENDER_OR_VIEW_MODIFIERS = False


# functions ------------------------------------------------------------------

def tab():
    return " " * TAB_SIZE

def clear_log_file():
    with open(LOG_FILE_NAME, "w") as f:
        pass

def log_to_file(message):
    time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    stack_depth = len(traceback.extract_stack()) - 1 - 10
    indentation = tab() * stack_depth
    log_message = f"{time_written}: {indentation}{message}"
    
    with open(LOG_FILE_NAME, "a") as f:
        f.write(f"{log_message}\n")

def deselect_everything():
    bpy.ops.object.select_all(action='DESELECT')

def map_action(iterator, func):
    for item in iterator:
        func(item)

def map_iter(iterator, func):
    for item in iterator:
        yield func(item)

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
    log_to_file(message)

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



def execute_pass_queue(obj, *fn):
    for fn in fn:
        fn(obj)




# def temporal_select_object(obj, fn):
#     old_active = bpy.context.view_layer.objects.active
#     old_selected = bpy.context.selected_objects

#     force_select_object(obj)
#     fn()

#     bpy.context.view_layer.objects.active = old_active
#     for ob in old_selected:
#         ob.select_set(True)

def add_bone_to_armature(armature, bone_name="Bone.001", head=(0, 0, 0), tail=(0, 0, 1), parent_bone=None):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    new_bone = armature.data.edit_bones.new(bone_name)
    new_bone.head = head
    new_bone.tail = tail

    if parent_bone is not None:
        new_bone.parent = parent_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    return new_bone

def fill_object_with_vertex_weight(obj, bone_name, weight=1):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    vertex_group = obj.vertex_groups.new(name=bone_name)
    vertex_indices = [v.index for v in obj.data.vertices]
    vertex_group.add(vertex_indices, weight, 'REPLACE')

def create_micro_bone_pass(obj, rig):
    if (
        # implicitly wants to have a micro bone
        obj.parent.type == "ARMATURE" # have parent armature
        and obj.modifiers.contains("Armature") # have armature modifier
        # explicitly wants to have a micro bone
        or hasattr(obj, CREATE_MICRO_BONE) 
        and obj[CREATE_MICRO_BONE] is True # have explicit setting
    ):
        return

    parent_bone = None
    if MICRO_BONE_PARENT in obj.keys():
        parent_bone = rig.data.edit_bones[obj[MICRO_BONE_PARENT]]

    name = f"{obj.name}__micro_bone"
    if MICRO_BONE_NAME in obj.keys():
        name = obj[MICRO_BONE_NAME]

    new_bone = add_bone_to_armature(rig, name, obj.location, obj.location, parent_bone)

    fill_object_with_vertex_weight(obj, new_bone.name, 1)

    pass

def apply_render_geometry_modifiers_pass(obj):
    if IS_APPLY_RENDER_OR_VIEW_MODIFIERS:
        apply_render_geometry_modifiers(obj)
        update_view_print(f"{tab()}Applied render modifiers to {obj.name}")

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
            update_view_print(f"{tab()}Skipped {obj.name if obj else 'deez nust'}")
            continue

        meshes.append(obj)
        update_view_print(f"{tab()}{obj.name}")


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

        apply_render_geometry_modifiers_pass(obj)

        bpy.ops.object.visual_transform_apply()
        update_view_print(f"{tab()}Made single user and applied visual transform to {obj.name}")


        fix_object_normal_pass(obj)

        create_micro_bone_pass(obj, rig)

        
        
        obj.data.name = f"{obj.name}__unique_mesh"
        update_view_print(f"{tab()}Renamed object data to {obj.data.name}")

        obj.select_set(False)
        deselect_everything()

        update_view_print(f"{tab()}Finished for {obj.name}")



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

    clear_log_file()

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


