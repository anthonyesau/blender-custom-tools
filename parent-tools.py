import bpy
import mathutils


class Converter:
    def __init__(self, ob, logging=False):
        self.ob = ob
        self.action = ob.animation_data.action
        self.rot_mode = ob.rotation_mode

        self.logging = logging
        if self.logging:
            print("\n"*2 + "-"*80)
            print("Converting", ob.name)

        # apply parent inverse to rest pose
        self.parent_inv = ob.matrix_parent_inverse.copy()
        if self.rot_mode == "AXIS_ANGLE":
            mat = self.build_matrix(ob.location, ob.rotation_axis_angle, ob.scale)
            mat = ob.matrix_parent_inverse * mat
            loc, rot, scale = mat.decompose()

            rot = rot.to_axis_angle()
            rot = (rot[1], rot[0][0], rot[0][1], rot[0][2])

            ob.location = loc
            ob.rotation_axis_angle = rot
            ob.scale = scale
        else:
            ob.matrix_basis = ob.matrix_parent_inverse * ob.matrix_basis
        ob.matrix_parent_inverse.identity()

        self.vec3_fs = "{: 8.4f} " * 3
        self.vec4_fs = "{: 8.4f} " * 4

        # gather fcurve channels
        self.location = [None] * 3
        self.rotation = [None] * (3 if self.rot_mode not in ("QUATERNION", "AXIS_ANGLE") else 4)
        self.scale    = [None] * 3

        self.frames = set()
        prop_rot = ("rotation_quaternion" if self.rot_mode == "QUATERNION" else
                    "rotation_axis_angle" if self.rot_mode == "AXIS_ANGLE" else
                    "rotation_euler")

        prop_to_attr = (
            ("location", self.location),
            (  prop_rot, self.rotation),
            (   "scale", self.scale)
        )

        for fcu in self.action.fcurves:
            for prop, attr in prop_to_attr:
                if fcu.data_path == prop:
                    attr[fcu.array_index] = fcu

        for prop, attr in prop_to_attr:
            for index, item in enumerate(attr):
                # use constant float if no fcurve is present or fcurve is empty
                if item is None or len(item.keyframe_points) == 0:
                    attr[index] = getattr(ob, prop)[index]

                # timeline
                else:
                    for kfp in item.keyframe_points:
                        self.frames.add(kfp.co.x)

    def eval_prop(self, prop, frame):
        return tuple(elem.evaluate(frame) if isinstance(elem, bpy.types.FCurve) else
                     elem for elem in prop)

    def build_matrix(self, loc, rot, scale):
        rot = (mathutils.Quaternion(rot)              if self.rot_mode == "QUATERNION" else
               mathutils.Quaternion(rot[1:4], rot[0]) if self.rot_mode == "AXIS_ANGLE" else
               mathutils.Euler(rot, self.rot_mode))

        mat_loc = mathutils.Matrix.Translation(loc)
        mat_rot = rot.to_matrix().to_4x4()
        mat_sca = mathutils.Matrix.Identity(4)
        for i in range(3):
            mat_sca[i][i] = scale[i]

        return mat_loc * mat_rot * mat_sca

    def insert_keyframe(self, prop, frame, value):
        for index, elem in enumerate(prop):
            if isinstance(elem, bpy.types.FCurve):
                elem.keyframe_points.insert(frame, value[index], {'REPLACE', 'FAST'})

    def convert(self):
        for frame in self.frames:
            loc   = self.eval_prop(self.location, frame)
            rot   = self.eval_prop(self.rotation, frame)
            scale = self.eval_prop(self.scale,    frame)

            if self.logging:
                rot_fs = self.vec3_fs if self.rot_mode not in ("QUATERNION", "AXIS_ANGLE") else self.vec4_fs
                print("frame %03d" % frame)
                print("location before:" + self.vec3_fs.format(*loc))
                print("rotation before:" +       rot_fs.format(*rot))
                print("scale    before:" + self.vec3_fs.format(*scale))

            mat_basis = self.build_matrix(loc, rot, scale)
            mat_basis = self.parent_inv * mat_basis

            loc, rot, scale = mat_basis.decompose()

            if self.rot_mode == "AXIS_ANGLE":
                rot = rot.to_axis_angle()
                rot = (rot[1], rot[0][0], rot[0][1], rot[0][2])
            elif not self.rot_mode == "QUATERNION":
                rot = rot.to_euler(self.rot_mode)

            if self.logging:
                print("location after :" + self.vec3_fs.format(*loc))
                print("rotation after :" +       rot_fs.format(*rot))
                print("scale    after :" + self.vec3_fs.format(*scale))
                print("-"*40)

            self.insert_keyframe(self.location, frame, loc)
            self.insert_keyframe(self.rotation, frame, rot)
            self.insert_keyframe(self.scale,    frame, scale)


class NeutralizeParentInverseOperator(bpy.types.Operator):
    """Clear the parent inverse matrix while maintaining objects' current transforms"""
    bl_idname = "object.neutralize_parent_inverse"
    bl_label = "Neutralize Parent Inverse"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for ob in context.selected_objects:
            if ob.parent and ob.animation_data:
                converter = Converter(ob, logging=True)
                converter.convert()
            elif ob.parent:
                # Merge the inverse into the object's transforms
                ob.matrix_basis = ob.matrix_parent_inverse * ob.matrix_basis
                # Clear the parent inverse matrix
                ob.matrix_parent_inverse.identity()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(NeutralizeParentInverseOperator)

def unregister():
    bpy.utils.unregister_class(NeutralizeParentInverseOperator)

if __name__ == "__main__":
    register()


class NeutralizeTransformsOperator(bpy.types.Operator):
    """Set the parent inverse matrix to current object transforms then clear all transforms"""
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
