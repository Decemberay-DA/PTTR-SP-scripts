import bpy
import Utils as u
import Logging as L


def get_root_bone_of_armature(armature):
    return armature.data.edit_bones[armature.data.edit_bones.keys()[0]]

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
    u.map_action(
        iter_hierarchy_inclusive(obj), 
        lambda x: move_to_collection(x, target_collection)
    )

def update_view():
    bpy.context.view_layer.update()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def update_view_print(message):
    update_view()
    print(message)
    L.LoggingH.log_to_file(message)

# Select the object. I SAD: SELECT THE OBJECT
def force_select_object(obj):
    if obj.name in bpy.context.view_layer.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)


