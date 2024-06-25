
import bpy
from Utils import Utils as u
from Logging import LoggingH


class BEX:
    @staticmethod
    def deselect_everything():
        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    def iter_hierarchy_inclusive(obj):
        yield obj
        for child in obj.children:
            yield from BEX.iter_hierarchy_inclusive(child)

    @staticmethod
    def move_to_collection(obj, target_collection):
        for col in obj.users_collection:
            col.objects.unlink(obj)
        target_collection.objects.link(obj)

    @staticmethod
    def move_to_collection_with_nierarchy(obj, target_collection):
        u.map_action(
            BEX.iter_hierarchy_inclusive(obj), 
            lambda x: BEX.move_to_collection(x, target_collection)
        )

    @staticmethod
    def update_view():
        bpy.context.view_layer.update()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    @staticmethod
    def update_view_print(message):
        BEX.update_view()
        print(message)
        LoggingH.log_to_file(message)

    # Select the object. I SAD: SELECT THE OBJECT
    @staticmethod
    def force_select_object(obj):
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        else:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
