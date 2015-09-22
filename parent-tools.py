import bpy


class NeutralizeParentInverseOperator(bpy.types.Operator):
    """Clear the parent inverse matrix while maintaining objects' current transforms"""
    bl_idname = "object.neutralize_parent_inverse"
    bl_label = "Neutralize Parent Inverse"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for ob in context.selected_objects:
            if ob.parent:
                # Merge the inverse into the object's transforms
                ob.matrix_basis = ob.matrix_parent_inverse * ob.matrix_basis
                # Nullify the vestigial inverse matrix
                ob.matrix_parent_inverse.identity()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NeutralizeParentInverseOperator)

def unregister():
    bpy.utils.unregister_class(NeutralizeParentInverseOperator)

if __name__ == "__main__":
    register()


class NeutralizeTransformsOperator(bpy.types.Operator):
    """Set the parent inverse matrix to current object transforms then clear all transforms. """
    bl_idname = "object.neutralize_transforms"
    bl_label = "Neutralize Transforms"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for ob in context.selected_objects:
            if ob.parent:
                # Merge the inverse into the object's transforms
                ob.matrix_parent_inverse = ob.matrix_parent_inverse * ob.matrix_basis
                # Nullify the vestigial inverse matrix
                ob.matrix_basis.identity()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NeutralizeTransformsOperator)

def unregister():
    bpy.utils.unregister_class(NeutralizeTransformsOperator)

if __name__ == "__main__":
    register()


class RelateDriversOperator(bpy.types.Operator):
    """Set driver variable targets to relative objects (based on variable names containing 'self' and/or 'parent')"""
    bl_idname = "object.relate_drivers"
    bl_label = "Relate Drivers"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for ob in bpy.context.selected_objects:
            if ob.animation_data is not None and ob.animation_data.drivers is not None:
                for driver in ob.animation_data.drivers:
                    for variable in driver.driver.variables:
                        name = variable.name
                        print(type(variable.targets))
                        for t in range(len(variable.targets)):
                            print("name: " + name)
                            print("iteration: " + str(t))
                            print("index of 'self': " + str(name.find('self')))
                            print("index of 'parent': " + str(name.find('parent')))
                            self_index = name.find('self')
                            parent_index = name.find('parent')
                            print(self_index != -1)
                            if (self_index < parent_index and self_index != -1) or (self_index > parent_index and parent_index == -1):
                                    variable.targets[t].id = ob
                                    name = name[self_index+4:len(name)]
                            elif (parent_index < self_index and parent_index != - 1) or (parent_index > self_index and self_index == - 1):
                                    variable.targets[t].id = ob.parent
                                    name = name[parent_index+6:len(name)]
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RelateDriversOperator)

def unregister():
    bpy.utils.unregister_class(RelateDriversOperator)

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

        row = layout.row()
        row.operator("object.neutralize_transforms")

        row = layout.row()
        row.operator("object.relate_drivers")


def register():
    bpy.utils.register_class(ParentToolsUI)

def unregister():
    bpy.utils.unregister_class(ParentToolsUI)

if __name__ == "__main__":
    register()
