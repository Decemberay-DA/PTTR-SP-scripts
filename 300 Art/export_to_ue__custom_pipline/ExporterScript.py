import bpy
import Utils as U
import Logging
from types import *
import BlenderEX as b
import ConfigLoader

config = ConfigLoader.load_config().logging

# passes ------------------------------------------------------------------

def fix_object_normal_pass(obj):
    if config.passes.fix_normals.attribute_name not in obj.keys() or obj[config.passes.fix_normals.attribute_name] is False:
        fix_object_normals(obj)
        b.update_view_print(f"Normals fixed for {obj.name}")

def fix_object_normals(obj):
    b.force_select_object(obj)
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
        new_bone.parent = b.get_root_bone_of_armature(armature)

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
    b.update_view_print(f"Created micro bone {bone.name} for {obj.name}")

    fill_object_with_vertex_weight(obj, bone.name, 1)
    b.update_view_print(f"Filled vertex weight for {obj.name}")

    pass

def apply_render_geometry_modifiers_pass(obj):
    if config.passes.apply_render_geometry_modifiers.enabled:
        apply_render_geometry_modifiers(obj)
        b.update_view_print(f"{Logging.tab()}Applied render modifiers to {obj.name}")

def apply_render_geometry_modifiers(obj):
    if obj.modifiers:
        for modifier in obj.modifiers:
            if modifier.show_render:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            else:
                print(f"Skipping modifier '{modifier.name}' (cz not enabled for render)")
















def run_export_pipline_for_rig(rig):
    b.update_view_print(f"Exporting for {rig.name} started")

    original_collection_of_the_rig = rig.users_collection[0]
    temporal_export_collection = bpy.data.collections.new(name="Export")
    bpy.context.scene.collection.children.link(temporal_export_collection)
    b.update_view_print(f"Created collection {temporal_export_collection.name}")

    # add rig and its childs to the "Export" collection
    b.move_to_collection_with_nierarchy(rig, temporal_export_collection)
    b.update_view_print(f"Hierarchy of {rig.name} moved to {temporal_export_collection.name}")


    # processing meshes and exporting to unreal ------------------------------------------------
    # processing meshes and exporting to unreal ------------------------------------------------
    # processing meshes and exporting to unreal ------------------------------------------------

    meshes = []
    b.update_view_print(f"Collecting meshes of {rig.name}:")
    for obj in temporal_export_collection.all_objects:
        # only for geometry
        if not (
            obj is not None
            and hasattr(obj, 'type') 
            and obj.type is not None 
            and obj.type == "MESH"
        ):
            b.update_view_print(f"{Logging.tab()}Skipped {obj.name if obj else 'deez nust'}")
            continue

        meshes.append(obj)
        b.update_view_print(f"{Logging.tab()}{obj.name}")




    for obj in meshes:
        b.force_select_object(obj)

        b.update_view_print(f"Selected {obj.name}")

        # Make single user and apply visual transform
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


        # apply_render_geometry_modifiers_pass(obj)


        bpy.ops.object.visual_transform_apply()
        b.update_view_print(f"{Logging.tab()}Made single user and applied visual transform to {obj.name}")


        fix_object_normal_pass(obj)

        # create_micro_bone_pass(obj, rig)

        
        obj.data.name = f"{obj.name}__unique_mesh"
        b.update_view_print(f"{Logging.tab()}Renamed object data to {obj.data.name}")

        obj.select_set(False)
        b.deselect_everything()

        b.update_view_print(f"{Logging.tab()}Finished for {obj.name}")



    # Send to Unreal Engine all things from the "Export" collection
    if config.main.is_export_to_ue:
        b.update_view_print(f"Sending to Unreal started")
        bpy.ops.wm.send2ue()
        b.update_view_print(f"Sending to Unreal finished")

    # delete the "Export" collection
    bpy.data.collections.remove(temporal_export_collection)
    b.move_to_collection_with_nierarchy(rig, original_collection_of_the_rig)
    b.update_view_print(f"Moved {rig.name} to {original_collection_of_the_rig.name}")
    b.update_view_print(f"Exported rig and its childs {rig.name} finished")

    pass















def main():
    # Save the current Blender file
    bpy.ops.wm.save_mainfile()

    Logging.clear_log_file()

    b.update_view_print("Saved the current Blender file")

    b.deselect_everything()

    # Get the objects to export
    rigs_to_export = [
            bpy.data.objects["shum_cloth_rig"],
            bpy.data.objects["shum_control_rig"]
        ]


    for rig in rigs_to_export:
        run_export_pipline_for_rig(rig)

    b.update_view_print(f"All rigs exported")
    b.update_view_print(f"SCRIPT FINISHED")

    # Revert all changes to the Blender file
    if config.main.is_revert_changes:
        bpy.ops.wm.revert_mainfile()




main()