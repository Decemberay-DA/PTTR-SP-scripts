import bpy
import datetime
import traceback



# constants ------------------------------------------------------------------
DONT_FIX_NORMALS = "dont_fix_normals"




# functions ------------------------------------------------------------------

def tab():
    return " " * 3

def clear_log_file():
    with open("export_to_ue__custom_pipline.log", "w") as f:
        pass

def log_to_file(message):
    time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    stack_depth = len(traceback.extract_stack()) - 1 - 10
    indentation = tab() * stack_depth
    log_message = f"{time_written}: {indentation}{message}"
    
    with open("export_to_ue__custom_pipline.log", "a") as f:
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

def force_rename_collection(collection, name):
    collection.name = name

# Select the object. I SAD: SELECT THE OBJECT
def force_select_object(obj):
    if obj.name in bpy.context.view_layer.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

def fix_object_normals(obj):
    force_select_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')




def export_armature_with_its_geometry_to_ue(rig):
    update_view_print(f"Exporting {rig.name} started")

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
            update_view_print(f"{tab()}Skipping {obj.name if obj else 'deez nust'}")
            continue

        meshes.append(obj)
        update_view_print(f"{tab()}{obj.name}")


    for obj in meshes:
        force_select_object(obj)

        update_view_print(f"Selected {obj.name}")

        # Make single user and apply visual transform
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.visual_transform_apply()
        update_view_print(f"{tab()}Made single user and applied visual transform to {obj.name}")

        if DONT_FIX_NORMALS not in obj.keys() or obj[DONT_FIX_NORMALS] is False:
            fix_object_normals(obj)
            update_view_print(f"{tab()}Normals fixed for {obj.name}")
        
        obj.data.name = f"{obj.name}__unique_mesh"
        update_view_print(f"{tab()}Renamed object data to {obj.data.name}")

        obj.select_set(False)
        deselect_everything()

        update_view_print(f"{tab()}Finished for {obj.name}")



    # # Send to Unreal Engine all things from the "Export" collection
    # bpy.ops.wm.send2ue()

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

    # # Revert all changes to the Blender file
    # bpy.ops.wm.revert_mainfile()

    update_view_print(f"SCRIPT FINISHED")



# Running the async function
main()


