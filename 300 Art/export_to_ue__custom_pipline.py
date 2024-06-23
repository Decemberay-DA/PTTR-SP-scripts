import bpy
import asyncio

def deselect_everything():
    bpy.ops.object.select_all(action='DESELECT')


def map(iterator, func):
    for item in iterator:
        func(item)

# def pipe(value, *funcs):
#     for fn in funcs:
#         value = fn(value)
#     return value

def iter_hierarchy_inclusive(obj):
    yield obj
    for child in obj.children:
        yield from iter_hierarchy_inclusive(child)

def move_to_collection(obj, target_collection):
    for col in obj.users_collection:
        col.objects.unlink(obj)
    target_collection.objects.link(obj)

def update_view():
    bpy.context.view_layer.update()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def update_view_print(message):
    update_view()
    print(message)



async def export_armature_with_its_geometry_to_ue(rig):

    update_view_print(f"Exporting {rig.name}")

    temporal_export_collection = bpy.data.collections.new(name="Export")
    bpy.context.scene.collection.children.link(temporal_export_collection)

    update_view_print(f"Created collection {temporal_export_collection.name}")

    # add rig and its childs to the "Export" collection
    map(
        iter_hierarchy_inclusive(rig), 
        lambda obj: move_to_collection(obj, temporal_export_collection)
    )

    for obj in temporal_export_collection.all_objects:
        # only for geometry
        if (
            hasattr(obj, 'type') 
            and obj.type is not None 
            and obj.type != "MESH"
        ):
            continue



        # Select the object
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Make single user and apply visual transform
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.visual_transform_apply()

        # Deselect the object
        deselect_everything()

        update_view_print(f"Made unique user and applied visual transform to {obj.name}")


    # Send to Unreal Engine
    bpy.ops.wm.send2ue()

    # delete the "Export" collection
    bpy.data.collections.remove(temporal_export_collection)

    update_view_print(f"Exported rig and its childs {rig.name}")

    pass




async def main():
    # Save the current Blender file
    bpy.ops.wm.save_mainfile()
    update_view_print("Saved the current Blender file")

    deselect_everything()

    # Get the objects to export
    rigs_to_export = [
            bpy.data.objects["shum_cloth_rig"],
            bpy.data.objects["shum_control_rig"]
        ]

    for rig in rigs_to_export:
        await asyncio.sleep(1)
        await export_armature_with_its_geometry_to_ue(rig)

    update_view_print("All rigs exported")

    # Revert all changes to the Blender file
    bpy.ops.wm.revert_mainfile()



# Running the async function
asyncio.run(main())


