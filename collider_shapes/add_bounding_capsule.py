import bpy
from bpy.types import Operator
from . import capsule_generation as Capsule

from .add_bounding_primitive import OBJECT_OT_add_bounding_object

tmp_name = 'capsule_collider'

class OBJECT_OT_add_bounding_capsule(OBJECT_OT_add_bounding_object, Operator):
    """Create bounding capsule collider based on the selection"""
    bl_idname = "mesh.add_bounding_capsule"
    bl_label = "Add Capsule"
    bl_description = 'Create bounding capsule colliders based on the selection'

    def __init__(self):
        super().__init__()
        self.use_space = True
        self.use_modifier_stack = True
        self.use_global_local_switches = True
        self.shape = 'capsule_shape'


    def invoke(self, context, event):
        super().invoke(context, event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        status = super().modal(context, event)

        if status == {'FINISHED'}:
            return {'FINISHED'}
        if status == {'CANCELLED'}:
            return {'CANCELLED'}
        if status == {'PASS_THROUGH'}:
            return {'PASS_THROUGH'}

        # change bounding object settings
        if event.type == 'G' and event.value == 'RELEASE':
            self.my_space = 'GLOBAL'
            self.execute(context)

        elif event.type == 'L' and event.value == 'RELEASE':
            self.my_space = 'LOCAL'
            self.execute(context)

        # change bounding object settings
        if event.type == 'P' and event.value == 'RELEASE':
            self.my_use_modifier_stack = not self.my_use_modifier_stack
            self.execute(context)
            
        return {'RUNNING_MODAL'}

    def execute(self, context):
        super().execute(context)

        # List for storing dictionaries of data used to generate the collision meshes
        collider_data = []
        verts_co = []

        # Create the bounding geometry, depending on edit or object mode.
        for obj in self.selected_objects:

            # skip if invalid object
            if not self.is_valid_object(obj):
                continue

            context.view_layer.objects.active = obj
            bounding_capsule_data = {}

            if self.obj_mode == "EDIT":
                used_vertices = self.get_vertices_Edit(obj, use_modifiers=self.my_use_modifier_stack)

            else:  # self.obj_mode  == "OBJECT":
                used_vertices = self.get_vertices_Object(obj, use_modifiers=self.my_use_modifier_stack)

            if used_vertices is None:  # Skip object if there is no Mesh data to create the collider
                continue

            if self.creation_mode[self.creation_mode_idx] == 'INDIVIDUAL':
                # used_vertices uses local space.
                co = self.get_point_positions(obj, self.my_space, used_vertices)

                # store data needed to generate a bounding box in a dictionary
                bounding_capsule_data['parent'] = obj
                bounding_capsule_data['verts_loc'] = co

                collider_data.append(bounding_capsule_data)

        bpy.ops.object.mode_set(mode='OBJECT')

        for bounding_capsule_data in collider_data:
            # get data from dictionary
            parent = bounding_capsule_data['parent']
            verts_loc = bounding_capsule_data['verts_loc']

            # Calculate the radius and height of the bounding capsule
            radius, height = Capsule.calculate_radius_height(verts_loc)
            data = Capsule.create_capsule(radius=radius, depth=height, uv_profile="FIXED")
            bm = Capsule.mesh_data_to_bmesh(
                vs=data["vs"],
                vts=data["vts"],
                vns=data["vns"],
                v_indices=data["v_indices"],
                vt_indices=data["vt_indices"],
                vn_indices=data["vn_indices"])

            mesh_data = bpy.data.meshes.new("Capsule")
            bm.to_mesh(mesh_data)
            bm.free()
            new_collider = bpy.data.objects.new(mesh_data.name, mesh_data)
            #context.scene.collection.objects.link(new_collider)

            # Get the combined object
            #new_collider = bpy.context.object

            # Move the bounding capsule to the same location as the original object
            #new_collider.location = parent.location

            # Align the bounding capsule with the original object's rotation
            #new_collider.rotation_euler = parent.rotation_euler

            # save collision objects to delete when canceling the operation
            self.new_colliders_list.append(new_collider)
            collections = parent.users_collection
            self.primitive_postprocessing(context, new_collider, collections)

            parent_name = parent.name
            super().set_collider_name(new_collider, parent_name)

        # Initial state has to be restored for the modal operator to work. If not, the result will break once changing the parameters
        super().reset_to_initial_state(context)
        elapsed_time = self.get_time_elapsed()
        super().print_generation_time("Capsule Collider", elapsed_time)
        self.report({'INFO'}, f"Capsule Collider: {float(elapsed_time)}")

        return {'RUNNING_MODAL'}

