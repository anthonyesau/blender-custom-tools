import bpy


class NeutralizeParentInverseOperator(bpy.types.Operator):
    """Clear the parent inverse matrix while maintaining objects' current transforms"""
    bl_idname = "object.neutralize_parent_inverse"
    bl_label = "Neutralize Parent Inverse"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        for ob in bpy.context.selected_objects: # Repeat for each selected object
            if ob.parent:   # Only alter objects that have a parent

                # Store the parent inverse matrix in separate location, rotation, and scale variables
                parent_location_inverse, parent_rotation_inverse, parent_scale_inverse = ob.matrix_parent_inverse.decompose()

                # Convert rotation quaternion to euler
                parent_rotation_inverse = parent_rotation_inverse.to_euler()

                # Apply the parent inverse matrix to the object's transforms
                ob.matrix_basis = ob.matrix_parent_inverse * ob.matrix_basis

                # Clear the parent inverse matrix
                ob.matrix_parent_inverse.identity()

                print() # Blank lines for legibility
                print()
                print()
                print()
                print ("Location Inverse: " + str(list(parent_location_inverse)))
                print ("Rotation Inverse: " + str(list(parent_rotation_inverse)))
                print ("Scale Inverse: " + str(list(parent_scale_inverse)))

                if ob.animation_data: # Check if object is animated
                    action = ob.animation_data.action

                    for fcu in action.fcurves: # Iterate through every f-curve

                        print()
                        print("Animated Property: " + fcu.data_path)
                        print("Channel: " + str(fcu.array_index))
                        # array_index of the f-curve is used as the index of the inverse that relates to the key frame
                        # For example: if the data_path is 'location' and the array_index is 1
                        # then the proper parent inverse to apply is parent_location_inverse[1]


                        for i in range(len(fcu.keyframe_points)): # Iterate through all key frames

                            print("Frame: " + str(fcu.keyframe_points[i].co.x))
                            print("Original Value:" + str(fcu.keyframe_points[i].co.y))

                            # Apply the parent inverse into the key frame values
                            # Different operations for location, rotation, and scale
                            if fcu.data_path == 'location':
                                print("Specific Inverse: " + str(parent_location_inverse[fcu.array_index]))
                                fcu.keyframe_points[i].co.y = fcu.keyframe_points[i].co.y + parent_location_inverse[fcu.array_index]

                            elif fcu.data_path == 'rotation_euler':
                                print("Specific Inverse: " + str(parent_rotation_inverse[fcu.array_index]))
                                fcu.keyframe_points[i].co.y = parent_rotation_inverse[fcu.array_index] * fcu.keyframe_points[i].co.y

                            elif fcu.data_path == 'scale':
                                print("Specific Inverse: " + str(parent_scale_inverse[fcu.array_index]))
                                fcu.keyframe_points[i].co.y = fcu.keyframe_points[i].co.y * parent_scale_inverse[fcu.array_index]

                            print("New Value: " + str(fcu.keyframe_points[i].co.y))

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
