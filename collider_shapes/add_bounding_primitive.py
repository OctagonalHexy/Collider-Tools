import blf
import bmesh
import bpy
import numpy
import time
import mathutils

from mathutils import Vector, Matrix, Quaternion

from ..groups.user_groups import get_groups_identifier, get_groups_name, set_groups_object_color
from ..pyshics_materials.material_functions import remove_materials, set_physics_material

collider_groups = ['USER_01', 'USER_02', 'USER_03']


def alignObjects(new, old):
    """Align two objects"""
    new.matrix_world = old.matrix_world


def draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=None, type='default', key='',
                    highlight=False):
    """Draw label in the 3D Viewport"""

    # get colors from preferences
    col_default = self.prefs.modal_color_default
    color_title = self.prefs.modal_color_title
    color_ignore_input = [0.5, 0.5, 0.5, 0.5]

    # operator colors
    color_enum = self.prefs.modal_color_enum
    color_modal = self.prefs.modal_color_modal
    color_bool = self.prefs.modal_color_bool
    color_highlight = self.prefs.modal_color_highlight
    color_error = self.prefs.modal_color_error

    # padding bottom
    font_size = self.prefs.modal_font_size

    # padding_bottom = self.prefs.padding_bottom
    padding_bottom = 0

    blf.size(font_id, 20, font_size)

    if type == 'error':
        blf.color(font_id, color_error[0], color_error[1], color_error[2], color_error[3])
    elif type == 'key_title':
        if self.ignore_input or self.navigation:
            blf.color(font_id, color_highlight[0], color_highlight[1], color_highlight[2], color_highlight[3])
    elif self.ignore_input or self.navigation:
        blf.color(font_id, color_ignore_input[0], color_ignore_input[1], color_ignore_input[2], color_ignore_input[3])
    elif type == 'title':
        blf.color(font_id, color_title[0], color_title[1], color_title[2], color_title[3])
    else:  # type == 'default'
        if highlight:
            blf.color(font_id, color_highlight[0], color_highlight[1], color_highlight[2], color_highlight[3])
        else:
            blf.color(font_id, col_default[0], col_default[1], col_default[2], col_default[3])

    blf.position(font_id, left_margin, padding_bottom + (i * vertical_px_offset), 0)
    blf.draw(font_id, label)

    if key:
        if self.ignore_input or self.navigation:
            blf.color(font_id, color_ignore_input[0], color_ignore_input[1], color_ignore_input[2],
                      color_ignore_input[3])
        elif highlight:
            blf.color(font_id, color_highlight[0], color_highlight[1], color_highlight[2], color_highlight[3])
        elif type == 'bool':
            blf.color(font_id, color_bool[0], color_bool[1], color_bool[2], color_bool[3])
        elif type == 'enum':
            blf.color(font_id, color_enum[0], color_enum[1], color_enum[2], color_enum[3])
        elif type == 'modal':
            blf.color(font_id, color_modal[0], color_modal[1], color_modal[2], color_modal[3])
        else:  # type == 'default':
            blf.color(font_id, col_default[0], col_default[1], col_default[2], col_default[3])

        blf.position(font_id, left_margin + 220 / 72 * font_size, padding_bottom + (i * vertical_px_offset), 0)
        blf.draw(font_id, key)

    if value:

        if self.ignore_input or self.navigation:
            blf.color(font_id, color_ignore_input[0], color_ignore_input[1], color_ignore_input[2],
                      color_ignore_input[3])
        elif highlight:
            blf.color(font_id, color_highlight[0], color_highlight[1], color_highlight[2], color_highlight[3])
        else:  # type == 'default':
            blf.color(font_id, col_default[0], col_default[1], col_default[2], col_default[3])

        blf.position(font_id, left_margin + 290 / 72 * font_size, padding_bottom + (i * vertical_px_offset), 0)
        blf.draw(font_id, value)

    i += 1
    return i


def create_name_number(name, nr):
    nr = str('_{num:{fill}{width}}'.format(num=(nr), fill='0', width=3))
    return name + nr


def draw_viewport_overlay(self, context):
    """Draw 3D viewport overlay for the modal operator"""
    scene = context.scene

    font_id = 0  # XXX, need to find out how best to get this.
    font_size = self.prefs.modal_font_size
    vertical_px_offset = 30 / 72 * font_size
    left_margin = bpy.context.area.width / 2 - 190 / 72 * font_size
    i = 1

    self.valid_input_selection = True if len(self.new_colliders_list) > 0 else False

    if self.use_space:
        label = "Global/Local"
        value = "GLOBAL" if scene.my_space == 'GLOBAL' else "LOCAL"
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(G/L)',
                            type='enum')

    label = "Display Wireframe "
    value = str(scene.wireframe_mode)
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(W)', type='enum')

    label = "Hide After Creation "
    value = str(scene.my_hide)
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(H)', type='bool')

    label = 'Persistent Settings'
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, type='title')

    label = "Collider Group"
    value = str(get_groups_name(self.collision_groups[self.collision_group_idx]))
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(T)', type='enum')

    label = "Creation Mode "
    value = self.creation_mode[self.creation_mode_idx]
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(M)', type='enum')

    if context.space_data.shading.type == 'SOLID':
        label = "Preview View "
        value = self.shading_modes[self.shading_idx]
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(V)',
                            type='enum')

    if self.use_shape_change:
        label = "Collider Shape"
        value = self.get_shape_name()
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(Q)',
                            type='enum')

    if self.use_cylinder_axis:
        label = "Cylinder Axis"
        value = str(self.cylinder_axis)
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(X/Y/Z)',
                            type='enum')

    if self.use_modifier_stack:
        label = "Use Modifiers "
        value = str(self.my_use_modifier_stack)
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(P)',
                            type='bool')

    label = "Toggle X Ray "
    value = str(self.x_ray)
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(C)', type='bool')

    label = "Opacity"
    value = self.current_settings_dic['alpha']
    value = '{initial_value:.3f}'.format(initial_value=value)
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(A)', type='modal',
                        highlight=self.opacity_active)

    label = "Shrink/Inflate"
    value = self.current_settings_dic['discplace_offset']
    value = '{initial_value:.3f}'.format(initial_value=value)
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(S)', type='modal',
                        highlight=self.displace_active)

    if self.use_sphere_segments:
        label = "Sphere Segments "
        value = str(self.current_settings_dic['sphere_segments'])
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(R)',
                            type='modal', highlight=self.sphere_segments_active)

    if self.use_decimation:
        label = "Decimate Ratio"
        value = self.current_settings_dic['decimate']
        value = '{initial_value:.3f}'.format(initial_value=value)
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(D)',
                            type='modal', highlight=self.decimate_active)

    if self.use_vertex_count:
        label = "Segments"
        value = str(self.current_settings_dic['cylinder_segments'])
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, value=value, key='(E)',
                            type='modal', highlight=self.vertex_count_active)

    label = 'Operator Settings'
    i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, type='title')

    if self.valid_input_selection:
        if self.navigation:
            label = 'VIEWPORT NAVIGATION'
            i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, type='key_title',
                                highlight=True)

        elif self.ignore_input:
            label = 'IGNORE INPUT (ALT)'
            i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, type='key_title',
                                highlight=True)

    else:  # Invalid selection (No colliders to be generated)
        label = 'Selection Invalid'
        i = draw_modal_item(self, font_id, i, vertical_px_offset, left_margin, label, type='error')


def get_loc_matrix(location):
    """get location matrix"""
    return Matrix.Translation(location)


def get_rot_matrix(rotation):
    """get rotation matrix"""
    return rotation.to_matrix().to_4x4()


def get_sca_matrix(scale):
    """get scale matrix"""
    scale_mx = Matrix()
    for i in range(3):
        scale_mx[i][i] = scale[i]
    return scale_mx


class OBJECT_OT_add_bounding_object():
    """Abstract parent class for modal collider_shapes contain common methods and properties for all add bounding object collider_shapes"""
    bl_options = {'REGISTER', 'UNDO'}
    bm = []

    @staticmethod
    def calculate_center_of_mass(obj):
        """calculate center of mass. """
        x, y, z = [sum([(obj.matrix_world.inverted() @ v.co)[i] for v in obj.data.vertices]) for i
                   in range(3)]
        count = float(len(obj.data.vertices))
        center = obj.matrix_world @ (Vector((x, y, z)) / count)

        return center

    @staticmethod
    def set_custom_origin_location(obj, center_point):
        """Set the origin of an object to the custom origin location. Only works if the object is not rotated or scalced at the moment"""
        # https://blender.stackexchange.com/questions/35825/changing-object-origin-to-arbitrary-point-without-origin-set
        obj.data.transform(mathutils.Matrix.Translation(-center_point))
        obj.location += center_point

    @staticmethod
    def apply_transform(obj, rotation=False, scale=True):
        """Apply transformations to object"""
        mx = obj.matrix_world
        loc, rot, sca = mx.decompose()

        # apply the current transformations on the mesh level
        if scale and rotation:
            meshmx = get_rot_matrix(rot) @ get_sca_matrix(sca)
            applymx = get_loc_matrix(loc) @ get_rot_matrix(Quaternion()) @ get_sca_matrix(Vector.Fill(3, 1))
        elif rotation:
            meshmx = get_rot_matrix(rot)
            applymx = get_loc_matrix(loc) @ get_rot_matrix(Quaternion()) @ get_sca_matrix(sca)
        elif scale:
            meshmx = get_sca_matrix(sca)
            applymx = get_loc_matrix(loc) @ get_rot_matrix(rot) @ get_sca_matrix(Vector.Fill(3, 1))

        obj.data.transform(meshmx)
        obj.matrix_world = applymx

    @staticmethod
    def set_custom_rotation(obj, rotation_matrix):
        """Rotate the origin based on a custom rotation matrix"""
        #
        ob_loc = obj.location.copy()

        # decompose the object matrix into it's location, rotation, scale components
        mx = obj.matrix_world
        loc, rot, sca = mx.decompose()

        # apply the current transformations on the mesh level
        meshmx = rotation_matrix.inverted()
        applymx = get_loc_matrix(loc) @ rotation_matrix @ get_sca_matrix(sca)

        # Apply matrices to mesh and object
        obj.data.transform(meshmx)
        obj.matrix_world = applymx

        # set the location back to the old location
        obj.location = ob_loc

    @classmethod
    def split_coordinates_xyz(cls, v_co_list):
        """Split a list of vertex locations into lists for the X Y Z component """
        positionsX = []
        positionsY = []
        positionsZ = []

        # generate a lists of all x, y and z coordinates to find the mins and max
        for co in v_co_list:
            positionsX.append(co[0])
            positionsY.append(co[1])
            positionsZ.append(co[2])

        return positionsX, positionsY, positionsZ

    @classmethod
    def generate_bounding_box(cls, v_co):
        '''get the min and max coordinates for the bounding box'''

        positionsX, positionsY, positionsZ = cls.split_coordinates_xyz(v_co)

        minX = min(positionsX)
        minY = min(positionsY)
        minZ = min(positionsZ)

        maxX = max(positionsX)
        maxY = max(positionsY)
        maxZ = max(positionsZ)

        verts = [
            (maxX, maxY, minZ),
            (maxX, minY, minZ),
            (minX, minY, minZ),
            (minX, maxY, minZ),
            (maxX, maxY, maxZ),
            (maxX, minY, maxZ),
            (minX, minY, maxZ),
            (minX, maxY, maxZ),
        ]

        center_point = Vector(((minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2))

        return verts, center_point

    @staticmethod
    def set_data_name(obj, new_name, data_suffix):
        """name object data based on object name"""
        data_name = new_name + data_suffix
        if data_name in bpy.data.meshes:
            bpy.data.meshes[data_name].name = 'deprecated_' + data_name

        obj.data.name = data_name

    @staticmethod
    def unique_name(name):
        '''recursive function to find unique name'''
        count = 1
        new_name = name

        while new_name in bpy.data.objects:
            new_name = create_name_number(name, count)
            count = count + 1
        return new_name

    @staticmethod
    def custom_set_parent(context, parent, child):
        '''Custom set parent'''
        for obj in context.selected_objects.copy():
            obj.select_set(False)

        context.view_layer.objects.active = parent
        parent.select_set(True)
        child.select_set(True)

        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

    @classmethod
    def bmesh(cls, bm):
        # append bmesh to class for it not to be deleted
        cls.bm.append(bm)

    @classmethod
    def class_collider_name(cls, shape_identifier, user_group, basename='Basename'):
        prefs = bpy.context.preferences.addons[__package__.split('.')[0]].preferences
        separator = prefs.separator

        if prefs.replace_name:
            name = prefs.obj_basename
        else:
            name = basename

        if prefs.collider_groups_enabled:
            pre_suffix_componetns = [
                prefs.collision_string_prefix,
                cls.get_shape_pre_suffix(prefs, shape_identifier),
                get_groups_identifier(user_group),
                prefs.collision_string_suffix
            ]
        else:  # prefs.collider_groups_enabled == False:
            pre_suffix_componetns = [
                prefs.collision_string_prefix,
                cls.get_shape_pre_suffix(prefs, shape_identifier),
                prefs.collision_string_suffix
            ]

        name_pre_suffix = ''
        if prefs.naming_position == 'SUFFIX':
            for comp in pre_suffix_componetns:
                if comp:
                    name_pre_suffix = name_pre_suffix + separator + comp
            new_name = name + name_pre_suffix

        else:  # prefs.naming_position == 'PREFIX'
            for comp in pre_suffix_componetns:
                if comp:
                    name_pre_suffix = name_pre_suffix + comp + separator
            new_name = name_pre_suffix + name

        return cls.unique_name(new_name)

    def collider_name(self, basename='Basename'):
        self.basename = basename
        user_group = self.collision_groups[self.collision_group_idx]
        return self.class_collider_name(shape_identifier=self.shape, user_group=user_group, basename=basename)

    def collision_dictionary(self, alpha, offset, decimate, sphere_segments, cylinder_segments):
        dict = {}
        dict['alpha'] = alpha
        dict['discplace_offset'] = offset
        dict['decimate'] = decimate
        dict['sphere_segments'] = sphere_segments
        dict['cylinder_segments'] = cylinder_segments

        return dict

    def get_shape_name(self):
        """ Return Shape String """
        if self.shape == 'box_shape':
            return 'BOX'
        elif self.shape == 'sphere_shape':
            return 'SPHERE'
        elif self.shape == 'convex_shape':
            return 'CONVEX'
        else:  # identifier == 'mesh_shape':
            return 'MESH'

    @staticmethod
    def get_shape_pre_suffix(prefs, identifier):
        # Hack. prefs.get('box_shape') does not work before the value is once changed.
        if identifier == 'box_shape':
            return prefs.box_shape
        elif identifier == 'sphere_shape':
            return prefs.sphere_shape
        elif identifier == 'convex_shape':
            return prefs.convex_shape
        else:  # identifier == 'mesh_shape':
            return prefs.mesh_shape

    @staticmethod
    def force_redraw():
        """Hack to redraw UI"""
        bpy.context.space_data.overlay.show_text = not bpy.context.space_data.overlay.show_text
        bpy.context.space_data.overlay.show_text = not bpy.context.space_data.overlay.show_text
        pass

    def set_collisions_wire_preview(self, mode):
        """Show wireframe for colliders"""
        if mode in ['PREVIEW', 'ALWAYS']:
            for obj in self.new_colliders_list:
                obj.show_wire = True
        else:
            for obj in self.new_colliders_list:
                obj.show_wire = False

    @staticmethod
    def remove_objects(list):
        '''Remove previously created collisions'''
        if len(list) > 0:
            for ob in list:
                objs = bpy.data.objects
                objs.remove(ob, do_unlink=True)

    @staticmethod
    def get_delta_value(delta, event, sensibility=0.05, tweak_amount=10, round_precission=0):

        delta = delta * sensibility

        if event.ctrl:  # snap
            delta = round(delta, round_precission)
        if event.shift:  # tweak
            delta /= tweak_amount

        return delta

    @staticmethod
    def get_mesh_Edit(obj, use_modifiers=False):
        ''' Get vertices from the bmesh. Returns a list of all or selected vertices. Returns None if there are no vertices to return '''
        me = obj.data
        me.update()  # update mesh data. This is needed to get the current mesh data after editing the mesh (adding, deleting, transforming)

        new_mesh = bpy.data.meshes.new('')

        if use_modifiers:  # self.my_use_modifier_stack == True
            # Get mesh information with the modifiers applied
            depsgraph = bpy.context.evaluated_depsgraph_get()
            bm = bmesh.new()
            bm.from_object(obj, depsgraph)

        else:  # use_modifiers == False
            # Get a BMesh representation
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()

        vertices_select = [v for v in bm.verts if not v.select]
        bmesh.ops.delete(bm, geom=vertices_select)

        bm.verts.ensure_lookup_table()
        bm.to_mesh(new_mesh)

        if len(bm.faces) < 1:
            return None

        return new_mesh

    @staticmethod
    def get_vertices_Edit(obj, use_modifiers=False):
        ''' Get vertices from the bmesh. Returns a list of all or selected vertices. Returns None if there are no vertices to return '''
        me = obj.data
        me.update()  # update mesh data. This is needed to get the current mesh data after editing the mesh (adding, deleting, transforming)

        # len(obj.modifiers) has to be bigger than 0. If there are no modifiers are assigned to the object the simple mesh can be used.
        # If len(obj.modifiers) == 0, the vertices are not selected and used_vertices is empty for some reason.
        if use_modifiers and len(obj.modifiers) > 0:
            # Get mesh information with the modifiers applied
            depsgraph = bpy.context.evaluated_depsgraph_get()
            bm = bmesh.new()
            bm.from_object(obj, depsgraph)
            bm.verts.ensure_lookup_table()

        else:  # use_modifiers == False
            # Get a BMesh representation
            bm = bmesh.from_edit_mesh(me)

        used_vertices = [v for v in bm.verts if v.select]
        print('used_vertices: ' + str(used_vertices))

        if len(used_vertices) == 0:
            return None

        # This is needed for the bmesh not bo be destroyed, even if the variable isn't used later.
        OBJECT_OT_add_bounding_object.bmesh(bm)
        return used_vertices

    @staticmethod
    def get_vertices_Object(obj, use_modifiers=False):
        ''' Get vertices from the bmesh. Returns a list of all or selected vertices. Returns None if there are no vertices to return '''
        # bpy.ops.object.mode_set(mode='EDIT')
        me = obj.data
        me.update()  # update mesh data. This is needed to get the current mesh data after editing the mesh (adding, deleting, transforming)

        if use_modifiers:
            # Get mesh information with the modifiers applied
            depsgraph = bpy.context.evaluated_depsgraph_get()
            bm = bmesh.new()
            bm.from_object(obj, depsgraph)
            bm.verts.ensure_lookup_table()
            used_vertices = bm.verts

            # This is needed for the bmesh not bo be destroyed, even if the variable isn't used later.
            OBJECT_OT_add_bounding_object.bmesh(bm)

        else:
            # Get a BMesh representation
            used_vertices = me.vertices

        if len(used_vertices) == 0:
            return None

        return used_vertices

    @staticmethod
    def transform_vertex_space(vertex_co, obj):
        # iterate over vertex coordinates to transform the positions to the appropriate space
        ws_vertex_co = []
        for i in range(len(vertex_co)):
            co = vertex_co[i]
            ws_vertex_co.append(obj.matrix_world.inverted() @ co)

        return ws_vertex_co

    @staticmethod
    def get_point_positions(obj, space, used_vertices):
        """ returns vertex and face information for the bounding box based on the given coordinate space (e.g., world or local)"""

        # Modify the BMesh, can do anything here...
        co = []

        if space == 'GLOBAL':
            # get world space coordinates of the vertices
            for v in used_vertices:
                v_local = v
                v_global = obj.matrix_world @ v_local.co

                co.append(v_global)

        else:  # space == 'LOCAL'
            for v in used_vertices:
                co.append(v.co)

        return co

    @staticmethod
    def mesh_from_selection(obj, use_modifiers=False):
        mesh = obj.data.copy()
        mesh.update()  # update mesh data. This is needed to get the current mesh data after editing the mesh (adding, deleting, transforming)

        bm = bmesh.new()

        if use_modifiers:
            # Get mesh information with the modifiers applied
            depsgraph = bpy.context.evaluated_depsgraph_get()
            bm = bmesh.new()
            bm.from_object(obj, depsgraph)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        else:  # self.my_use_modifier_stack == False:
            bm.from_mesh(mesh)

        bm.to_mesh(mesh)
        bm.free()

        return mesh

    @staticmethod
    def is_valid_object(obj):
        """Is the object valid to be used as a base mesh for collider generation"""
        if obj is None or obj.type != "MESH":
            return False
        return True

    # Collections
    @staticmethod
    def add_to_collections(obj, collection_name):
        """Add an object to a collection"""
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)

        col = bpy.data.collections[collection_name]

        try:
            col.objects.link(obj)
        except RuntimeError as err:
            pass

    @staticmethod
    def set_collections(obj, collections):
        """link an object to a collection"""
        old_collection = obj.users_collection

        for col in collections:
            try:
                col.objects.link(obj)
            except RuntimeError:
                pass

        for col in old_collection:
            if col not in collections:
                col.objects.unlink(obj)

    # Modifiers
    @staticmethod
    def apply_all_modifiers(context, obj):
        """apply all modifiers to an object"""
        context.view_layer.objects.active = obj
        for mod in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=mod.name)

    @staticmethod
    def remove_all_modifiers(context, obj):
        """Remove all modifiers of an object"""
        context.view_layer.objects.active = obj
        if obj:
            for mod in obj.modifiers:
                obj.modifiers.remove(mod)

    @staticmethod
    def del_displace_modifier(bounding_object):
        """Delete displace modifiers called 'Collision_displace'"""
        if bounding_object.modifiers.get('Collision_displace'):
            mod = bounding_object.modifiers['Collision_displace']
            bounding_object.modifiers.remove(mod)

    @staticmethod
    def del_decimate_modifier(bounding_object):
        """Delete modifiers called 'Collision_decimate'"""
        if bounding_object.modifiers.get('Collision_decimate'):
            mod = bounding_object.modifiers['Collision_decimate']
            bounding_object.modifiers.remove(mod)

    # Time classes
    @staticmethod
    def print_generation_time(shape, time):
        print(shape)
        print("Time elapsed: ", str(time))

    def primitive_postprocessing(self, context, bounding_object, base_object_collections):
        self.set_viewport_drawing(context, bounding_object)
        self.add_displacement_modifier(context, bounding_object)
        self.set_collections(bounding_object, base_object_collections)

        if self.prefs.use_col_collection:
            collection_name = self.prefs.col_collection_name
            self.add_to_collections(bounding_object, collection_name)

        if self.use_decimation:
            self.add_decimate_modifier(context, bounding_object)

        mat_name = ''
        if bpy.data.materials[context.scene.material_list_index]:
            mat_name = bpy.data.materials[context.scene.material_list_index].name
        else:  # No default material is selected
            mat_name = self.prefs.physics_material_name

        set_physics_material(bounding_object, mat_name)

        bounding_object['isCollider'] = True
        bounding_object['collider_group'] = self.collision_groups[self.collision_group_idx]
        bounding_object['collider_shape'] = self.shape

        scene = context.scene

        if scene.wireframe_mode in ['PREVIEW', 'ALWAYS']:
            bounding_object.show_wire = True
        else:
            bounding_object.show_wire = False

    def set_viewport_drawing(self, context, bounding_object):
        ''' Assign material to the bounding object and set the visibility settings of the created object.'''
        bounding_object.display_type = 'SOLID'
        set_groups_object_color(bounding_object, self.collision_groups[self.collision_group_idx])

    def set_object_collider_group(self, obj):
        obj['collider_group'] = self.collision_groups[self.collision_group_idx]

    def set_collider_name(self, new_collider, parent_name):
        new_name = self.collider_name(basename=parent_name)
        new_collider.name = new_name
        self.set_data_name(new_collider, new_name, self.data_suffix)

    def update_names(self):
        for obj in self.new_colliders_list:
            new_name = self.collider_name(basename=self.basename)
            obj.name = new_name
            self.set_data_name(obj, new_name, self.data_suffix)

    def reset_to_initial_state(self, context):
        for obj in bpy.data.objects:
            obj.select_set(False)
        for obj in self.selected_objects:
            obj.select_set(True)
        context.view_layer.objects.active = self.active_obj
        bpy.ops.object.mode_set(mode=self.obj_mode)

    def add_displacement_modifier(self, context, bounding_object):
        scene = context.scene

        # add displacement modifier and safe it to manipulate the strenght in the modal operator
        modifier = bounding_object.modifiers.new(name="Collision_displace", type='DISPLACE')
        modifier.strength = self.current_settings_dic['discplace_offset']

        self.displace_modifiers.append(modifier)

    def add_decimate_modifier(self, context, bounding_object):
        scene = context.scene

        # add decimation modifier and safe it to manipulate the strenght in the modal operator
        modifier = bounding_object.modifiers.new(name="Collision_decimate", type='DECIMATE')
        modifier.ratio = self.current_settings_dic['decimate']
        self.decimate_modifiers.append(modifier)

    def get_time_elapsed(self):
        t1 = time.time() - self.t0
        return t1

    def cancel_cleanup(self, context):
        if not self.is_mesh_to_collider:
            # Remove previously created collisions
            if self.new_colliders_list != None:
                for obj in self.new_colliders_list:
                    objs = bpy.data.objects
                    objs.remove(obj, do_unlink=True)

        # Reset Convert Mesh to Collider
        else:
            if self.new_colliders_list != None:
                for obj, data in zip(self.new_colliders_list, self.original_obj_data):
                    if self.prefs.col_collection_name in bpy.data.collections:
                        col = bpy.data.collections[self.prefs.col_collection_name]
                        if obj.name in col.objects:
                            col.objects.unlink(obj)

                    obj.color = data['color']
                    obj.show_wire = data['show_wire']
                    obj.name = data['name']

                    remove_materials(obj)
                    for mat in data['material_slots']:
                        set_physics_material(obj, mat)

                    self.del_displace_modifier(obj)
                    self.del_decimate_modifier(obj)

        context.space_data.shading.color_type = self.color_type

        try:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        except ValueError:
            pass

    def __init__(self):
        # has to be in --init
        self.is_mesh_to_collider = False
        self.use_decimation = False

        self.use_vertex_count = False
        self.vertex_count = 8
        self.use_modifier_stack = False

        self.use_space = False
        self.use_cylinder_axis = False
        self.use_global_local_switches = False
        self.use_sphere_segments = False
        self.shape = ''
        self.use_shape_change = False

        # UI/UX
        self.ignore_input = False

        self.use_recenter_origin = False
        self.use_custom_rotation = False

    @classmethod
    def poll(cls, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                count = count + 1
        return count > 0

    def invoke(self, context, event):
        global collider_groups

        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

        # get collision suffix from preferences
        self.prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        scene = context.scene

        # Active object
        if context.object is None:
            context.view_layer.objects.active = context.selected_objects[0]
        context.object.select_set(True)

        # INITIAL STATE
        self.navigation = False
        self.selected_objects = context.selected_objects.copy()
        self.active_obj = context.view_layer.objects.active
        self.obj_mode = context.object.mode
        self.prev_decimate_time = time.time()
        self.data_suffix = "_data"
        self.valid_input_selection = True

        # Mouse
        self.mouse_initial_x = event.mouse_x

        # Modal Settings
        self.my_use_modifier_stack = False
        self.x_ray = context.space_data.shading.show_xray

        # Modal MODIFIERS
        # Displace
        self.displace_active = False
        self.displace_modifiers = []

        # Decimate
        self.decimate_active = False
        self.decimate_modifiers = []

        # Opacity
        self.opacity_active = False
        self.opacity_ref = 0.5

        self.cylinder_axis = 'Z'

        self.vertex_count_active = False

        self.sphere_segments_active = False
        segments = 16

        self.color_type = context.space_data.shading.color_type
        self.shading_idx = 0
        self.shading_modes = ['OBJECT', 'MATERIAL', 'SINGLE']
        self.wireframe_idx = 1

        self.creation_mode = ['INDIVIDUAL', 'SELECTION']
        self.creation_mode_idx = 0

        # self.wireframe_mode = ['OFF', 'PREVIEW', 'ALWAYS']
        self.collision_group_idx = 0
        self.collision_groups = collider_groups

        self.new_colliders_list = []
        self.col_rotation_matrix_list = []
        self.col_center_loc_list = []

        self.name_count = 0

        # Set up scene
        if context.space_data.shading.type == 'SOLID':
            context.space_data.shading.color_type = self.shading_modes[self.shading_idx]

        dict = self.collision_dictionary(0.5, 0, 1.0, segments, self.vertex_count)
        self.current_settings_dic = dict.copy()
        self.ref_settings_dic = dict.copy()

        # the arguments we pass the the callback
        args = (self, context)
        # Add the region OpenGL drawing callback
        # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_viewport_overlay, args, 'WINDOW', 'POST_PIXEL')
        # add modal handler
        context.window_manager.modal_handler_add(self)
        self.execute(context)

    def modal(self, context, event):
        scene = context.scene
        self.navigation = False

        # Ignore if Alt is pressed
        if event.alt:
            self.ignore_input = True
            self.force_redraw()
            return {'RUNNING_MODAL'}

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            self.navigation = True

            self.opacity_active = False
            self.displace_active = False
            self.decimate_active = False
            self.vertex_count_active = False
            self.sphere_segments_active = False

            return {'PASS_THROUGH'}

        # User Input
        # aboard operator
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_cleanup(context)
            return {'CANCELLED'}

        # apply operator
        elif event.type in {'LEFTMOUSE', 'NUMPAD_ENTER', 'RET'}:
            # self.execute(context)
            if bpy.context.space_data.shading.color_type:
                context.space_data.shading.color_type = self.color_type

            for i, obj in enumerate(self.new_colliders_list):
                if self.use_recenter_origin:
                    # set origin causes issues. Does not work properly
                    center = self.calculate_center_of_mass(obj)
                    self.set_custom_origin_location(obj, center)

                if self.use_custom_rotation:
                    if len(self.col_rotation_matrix_list) > 0:
                        self.set_custom_rotation(obj, self.col_rotation_matrix_list[i])

                # remove modifiers if they have the default value
                if self.current_settings_dic['discplace_offset'] == 0.0:
                    self.del_displace_modifier(obj)
                if self.current_settings_dic['decimate'] == 1.0:
                    self.del_decimate_modifier(obj)

                # set the display settings for the collider objects
                obj.display_type = scene.display_type
                obj.hide_render = True

                if scene.my_hide:
                    obj.hide_viewport = scene.my_hide

                if scene.wireframe_mode == 'ALWAYS':
                    obj.show_wire = True
                else:
                    obj.show_wire = False

            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            except ValueError:
                pass

            bpy.ops.object.mode_set(mode='OBJECT')

            return {'FINISHED'}

        # Set ref values when switching mode to avoid jumping of field of view.
        elif event.type in ['LEFT_SHIFT', 'LEFT_CTRL'] and event.value in ['PRESS', 'RELEASE']:
            self.ref_settings_dic = self.current_settings_dic.copy()

            # update ref mouse position to current
            self.mouse_initial_x = event.mouse_x
            # Alt is not pressed anymore after release
            self.ignore_input = False

            return {'RUNNING_MODAL'}

        # Ignore Mouse Movement. The Operator will behave as starting it newly
        elif event.type == 'LEFT_ALT' and event.value == 'RELEASE':
            self.ref_settings_dic = self.current_settings_dic.copy()

            # update ref mouse position to current
            self.mouse_initial_x = event.mouse_x

            # Alt is not pressed anymore after release
            self.ignore_input = False
            self.force_redraw()
            return {'RUNNING_MODAL'}

        # hide after creation
        elif event.type == 'H' and event.value == 'RELEASE':
            scene.my_hide = not scene.my_hide
            # Another function needs to be called for the modal UI to update :(
            self.set_collisions_wire_preview(scene.wireframe_mode)

        elif event.type == 'W' and event.value == 'RELEASE':
            self.wireframe_idx = (self.wireframe_idx + 1) % len(
                bpy.types.Scene.bl_rna.properties['wireframe_mode'].enum_items)
            scene.wireframe_mode = bpy.types.Scene.bl_rna.properties['wireframe_mode'].enum_items[
                self.wireframe_idx].identifier
            # Another function needs to be called for the modal UI to update :(
            self.set_collisions_wire_preview(scene.wireframe_mode)

        elif event.type == 'C' and event.value == 'RELEASE':
            self.x_ray = not self.x_ray
            context.space_data.shading.show_xray = self.x_ray
            # Another function needs to be called for the modal UI to update :(
            self.set_collisions_wire_preview(scene.wireframe_mode)

        elif event.type == 'M' and event.value == 'RELEASE':

            self.creation_mode_idx = (self.creation_mode_idx + 1) % len(self.creation_mode)
            self.execute(context)

        elif event.type == 'S' and event.value == 'RELEASE':
            self.displace_active = not self.displace_active
            self.opacity_active = False
            self.decimate_active = False
            self.vertex_count_active = False
            self.sphere_segments_active = False
            self.mouse_initial_x = event.mouse_x

        elif event.type == 'D' and event.value == 'RELEASE':
            self.decimate_active = not self.decimate_active
            self.opacity_active = False
            self.displace_active = False
            self.vertex_count_active = False
            self.sphere_segments_active = False
            self.mouse_initial_x = event.mouse_x

        elif event.type == 'A' and event.value == 'RELEASE':
            self.opacity_active = not self.opacity_active
            self.displace_active = False
            self.decimate_active = False
            self.vertex_count_active = False
            self.sphere_segments_active = False
            self.mouse_initial_x = event.mouse_x

        elif event.type == 'E' and event.value == 'RELEASE':
            self.vertex_count_active = not self.vertex_count_active
            self.displace_active = False
            self.decimate_active = False
            self.opacity_active = False
            self.sphere_segments_active = False
            self.mouse_initial_x = event.mouse_x

        elif event.type == 'V' and event.value == 'RELEASE':
            # toggle through display modes
            self.shading_idx = (self.shading_idx + 1) % len(self.shading_modes)
            context.space_data.shading.color_type = self.shading_modes[self.shading_idx]

        elif event.type == 'T' and event.value == 'RELEASE':
            # toggle through display modes
            self.collision_group_idx = (self.collision_group_idx + 1) % len(self.collision_groups)
            for obj in self.new_colliders_list:
                set_groups_object_color(obj, self.collision_groups[self.collision_group_idx])
                self.set_object_collider_group(obj)
                self.update_names()

        elif event.type == 'MOUSEMOVE':
            # calculate mouse movement and offset camera
            delta = int(self.mouse_initial_x - event.mouse_x)

            # Ignore if Alt is pressed
            if event.alt:
                self.ignore_input = True
                return {'RUNNING_MODAL'}

            if self.displace_active:
                offset = self.get_delta_value(delta, event, sensibility=0.002, tweak_amount=10, round_precission=1)
                strenght = self.ref_settings_dic['discplace_offset'] - offset

                for mod in self.displace_modifiers:
                    mod.strength = strenght
                    mod.show_on_cage = True
                    mod.show_in_editmode = True

                self.current_settings_dic['discplace_offset'] = strenght

            if self.decimate_active:
                delta = self.get_delta_value(delta, event, sensibility=0.002, tweak_amount=10, round_precission=1)
                dec_amount = (self.ref_settings_dic['decimate'] + delta)
                dec_amount = numpy.clip(dec_amount, 0.01, 1.0)

                if self.current_settings_dic['decimate'] != dec_amount:
                    self.current_settings_dic['decimate'] = dec_amount

                    # I had to iterate over all object because it crashed when just iterating over the modifiers.
                    for obj in self.new_colliders_list:
                        for mod in obj.modifiers:
                            if mod in self.decimate_modifiers:
                                mod.ratio = dec_amount

            if self.opacity_active:
                delta = self.get_delta_value(delta, event, sensibility=0.002, tweak_amount=10, round_precission=1)
                color_alpha = self.ref_settings_dic['alpha'] - delta
                color_alpha = numpy.clip(color_alpha, 0.00, 1.0)

                for obj in self.new_colliders_list:
                    obj.color[3] = color_alpha

                self.prefs.user_group_01_color[3] = color_alpha
                self.current_settings_dic['alpha'] = color_alpha

            if self.vertex_count_active:
                delta = self.get_delta_value(delta, event, sensibility=0.02, tweak_amount=10)
                vertex_count = int(abs(self.ref_settings_dic['cylinder_segments'] - delta))

                # check if value changed to avoid regenerating collisions for the same value
                if vertex_count != int(round(self.vertex_count)):
                    self.vertex_count = vertex_count
                    self.current_settings_dic['cylinder_segments'] = vertex_count
                    self.execute(context)

            if self.sphere_segments_active:
                delta = self.get_delta_value(delta, event, sensibility=0.02, tweak_amount=10)
                segments = int(abs(self.ref_settings_dic['sphere_segments'] - delta))

                # check if value changed to avoid regenerating collisions for the same value
                if segments != int(round(self.current_settings_dic['sphere_segments'])):
                    self.current_settings_dic['sphere_segments'] = segments
                    self.execute(context)

        # passthrough specific events to blenders default behavior
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        # get current time to calculate time elapsed
        self.t0 = time.time()
        # reset naming count:
        self.name_count = 0

        self.obj_mode = context.object.mode

        # Remove objects from previous generation
        self.remove_objects(self.new_colliders_list)
        self.new_colliders_list = []

        # reset previously stored displace modifiers when creating a new object
        self.displace_modifiers = []

        # Create the bounding geometry, depending on edit or object mode.
        self.old_objs = set(context.scene.objects)