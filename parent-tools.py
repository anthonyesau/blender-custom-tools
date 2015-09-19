import bpy


class NeutralizeParentInverseOperator(bpy.types.Operator):
    """Clear the parent inverse matrix while maintaining objects' current transforms"""
    bl_idname = "object.neutralize_parent_inverse"
    bl_label = "Neutralize Parent Inverse"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # based off code by ideasman42
        # found originally at: http://blender.stackexchange.com/questions/28896/how-to-clear-parent-inverse-without-actually-moving-the-object
        for ob in context.selected_objects:
            if ob.parent:
                # store a copy of the objects final transformation
                # so we can read from it later.
                ob_matrix_orig = ob.matrix_world.copy()

                # reset parent inverse matrix
                # (relationship created when parenting)
                ob.matrix_parent_inverse.identity()

                # re-apply the difference between parent/child
                # (this writes directly into the loc/scale/rot) via a matrix.
                ob.matrix_basis = ob.parent.matrix_world.inverted() * ob_matrix_orig
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NeutralizeParentInverseOperator)

def unregister():
    bpy.utils.unregister_class(NeutralizeParentInverseOperator)

if __name__ == "__main__":
    register()


# Create Parent Tools UI in the Tool Shelf of the 3D View
class ParentToolsUI(bpy.types.Panel):
    """Better Parenting"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Parent Tools"
    bl_context = "objectmode"
    bl_category = "Parent Tools"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("object.neutralize_parent_inverse")


def register():
    bpy.utils.register_class(ParentToolsUI)

def unregister():
    bpy.utils.unregister_class(ParentToolsUI)

if __name__ == "__main__":
    register()
