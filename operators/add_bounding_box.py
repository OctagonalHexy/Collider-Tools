import bmesh
import bpy
from bpy.types import Operator
from bpy_extras.object_utils import object_data_add
from mathutils import Vector

from CollisionHelpers.operators.object_functions import alignObjects, get_bounding_box
from .add_bounding_primitive import OBJECT_OT_add_bounding_object


def add_box_object(context, vertices, newName):
    """Generate a new object from the given vertices"""
    verts = vertices
    edges = []
    faces = [[0, 1, 2, 3], [7, 6, 5, 4], [5, 6, 2, 1], [0, 3, 7, 4], [3, 2, 6, 7], [4, 5, 1, 0]]

    mesh = bpy.data.meshes.new(name=newName)
    mesh.from_pydata(verts, edges, faces)

    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    newObj = object_data_add(context, mesh, operator=None, name=None)  # links to object instance

    return newObj


def generate_box(positionsX, positionsY, positionsZ):
    # get the min and max coordinates for the bounding box
    verts = [
        (max(positionsX), max(positionsY), min(positionsZ)),
        (max(positionsX), min(positionsY), min(positionsZ)),
        (min(positionsX), min(positionsY), min(positionsZ)),
        (min(positionsX), max(positionsY), min(positionsZ)),
        (max(positionsX), max(positionsY), max(positionsZ)),
        (max(positionsX), min(positionsY), max(positionsZ)),
        (min(positionsX), min(positionsY), max(positionsZ)),
        (min(positionsX), max(positionsY), max(positionsZ)),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]

    return verts, faces


def add_box_edit_mode(obj, space, mode='EDIT'):
    """ returns vertex and face information for the bounding box based on the given coordinate space (e.g., world or local)"""

    me = obj.data

    # Get a BMesh representation
    bm = bmesh.from_edit_mesh(me)


    if mode != 'EDIT':
        for v in bm.verts: v.select = True

    used_vertives = [v for v in bm.verts if v.select]


    # Modify the BMesh, can do anything here...
    positionsX = []
    positionsY = []
    positionsZ = []

    if space == 'GLOBAL':
        # get world space coordinates of the vertices
        for v in used_vertives:
            v_local = v
            v_global = obj.matrix_world @ v_local.co

            positionsX.append(v_global[0])
            positionsY.append(v_global[1])
            positionsZ.append(v_global[2])

    # space == 'LOCAL'
    else:
        for v in used_vertives:
            positionsX.append(v.co.x)
            positionsY.append(v.co.y)
            positionsZ.append(v.co.z)

    # generate_box is saved into 2 variables and not returned directly to not have them interpreted as a tuple
    verts, faces = generate_box(positionsX, positionsY, positionsZ)
    return verts, faces


def verts_faces_to_bbox_collider(self, context, verts_loc, faces, nameSuf):
    """Create box collider for selected mesh area in edit mode"""

    active_ob = context.object
    root_collection = context.scene.collection

    # add new mesh
    mesh = bpy.data.meshes.new("Box")
    bm = bmesh.new()

    for v_co in verts_loc:
        bm.verts.new(v_co)

    bm.verts.ensure_lookup_table()
    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])

    # update bmesh to draw properly in viewport
    bm.to_mesh(mesh)
    mesh.update()

    # create new object from mesh and link it to collection
    newCollider = bpy.data.objects.new(active_ob.name + nameSuf, mesh)
    root_collection.objects.link(newCollider)

    if self.my_space == 'LOCAL':
        print("entered Local")
        alignObjects(newCollider, active_ob)

    return newCollider


def box_Collider_from_Objectmode(self, context, name, obj, i):
    """Create box collider for every selected object in object mode"""
    colliderOb = []

    if self.my_space == 'LOCAL':
        # create BoundingBox object for collider
        bBox = get_bounding_box(obj)
        newCollider = add_box_object(context, bBox, name)

        # local_bbox_center = 1/8 * sum((Vector(b) for b in obj.bound_box), Vector())
        # global_bbox_center = obj.matrix_world @ local_bbox_center
        centreBase = sum((Vector(b) for b in obj.bound_box), Vector())
        centreBase /= 8

        # newCollider.matrix_world = centreBase
        alignObjects(newCollider, obj)

    # Space == 'Global'
    else:
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        verts_loc, faces = add_box_edit_mode(obj, self.my_space, mode='OBJECT')
        newCollider = verts_faces_to_bbox_collider(self, context, verts_loc, faces, name)
        bpy.ops.object.mode_set(mode='OBJECT')

    return newCollider


def remove_objects(list):
    # Remove previously created collisions
    if len(list) > 0:
        for ob in list:
            objs = bpy.data.objects
            objs.remove(ob, do_unlink=True)


class OBJECT_OT_add_bounding_box(OBJECT_OT_add_bounding_object, Operator):
    """Create a new bounding box object"""
    bl_idname = "mesh.add_bounding_box"
    bl_label = "Add Box Collision"

    def invoke(self, context, event):
        super().invoke(context, event)
        # return self.execute(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        # User Input
        # aboard operator
        if event.type in {'RIGHTMOUSE', 'ESC'}:

            # Remove previously created collisions
            if self.previous_objects != None:
                objs = bpy.data.objects
                objs.remove(self.previous_objects, do_unlink=True)

            context.space_data.shading.color_type = self.color_type
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        # apply operator
        elif event.type in {'LEFTMOUSE', 'NUMPAD_ENTER'}:
            # self.execute(context)
            context.space_data.shading.color_type = self.color_type
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        # change bounding object settings
        elif event.type == 'G' and event.value == 'RELEASE':
            self.my_space = 'GLOBAL'
            self.execute(context)


        elif event.type == 'L' and event.value == 'RELEASE':
            self.my_space = 'LOCAL'
            self.execute(context)


        # passthrough specific events to blenders default behavior
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        nameSuf = self.name_suffix
        matName = self.physics_material_name
        base_obj = self.active_obj

        context.view_layer.objects.active = base_obj

        remove_objects(self.previous_objects)
        self.previous_objects = []

        # Create the bounding geometry, depending on edit or object mode.
        if context.object.mode == "EDIT":
            verts_loc, faces = add_box_edit_mode(base_obj, self.my_space)
            newCollider = verts_faces_to_bbox_collider(self, context, verts_loc, faces, nameSuf)

            # save collision objects to delete when canceling the operation
            self.previous_objects.append(newCollider)

            self.set_viewport_drawing(context, newCollider, matName)

        else:  # mode == "OBJECT":

            for i, obj in enumerate(self.selected_objects):
                newCollider = box_Collider_from_Objectmode(self, context, nameSuf, obj, i)

                # save collision objects to delete when canceling the operation
                self.previous_objects.append(newCollider)

                self.set_viewport_drawing(context, newCollider, matName)

        return {'RUNNING_MODAL'}
