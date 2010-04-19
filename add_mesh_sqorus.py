# add_mesh_sqorus.py Copyright (C) 2008-2009, FourMadMen.com
#
# add sqorus to the blender 2.50 add->mesh menu
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    'name': 'Add Mesh: Sqorus',
    'author': 'fourmadmen',
    'version': '1.2',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Squorus to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Sqorus',
    'category': 'Add Mesh'}

# blender Extensions menu registration (in user Prefs)
"Add Sqorus (View3D > Add > Mesh > Sqorus)"

"""
Name: 'Sqorus'
Blender: 250
Group: 'AddMesh'
Tip: 'Add Sqorus Object...'
__author__ = ["Four Mad Men", "FourMadMen.com"]
__version__ = '1.0'
__url__ = [""]
email__=["bwiki {at} fourmadmen {dot} com"]

Usage:

* Launch from Add Mesh menu

* Modify parameters as desired or keep defaults

"""


import bpy
from mathutils import *
from bpy.props import FloatProperty, BoolProperty


# Stores the values of a list of properties and the
# operator id in a property group ('recall_op') inside the object.
# Could (in theory) be used for non-objects.
# Note: Replaces any existing property group with the same name!
# ob ... Object to store the properties in.
# op ... The operator that should be used.
# op_args ... A dictionary with valid Blender
#             properties (operator arguments/parameters).
def store_recall_properties(ob, op, op_args):
    if ob and op and op_args:
        recall_properties = {}

        # Add the operator identifier and op parameters to the properties.
        recall_properties['op'] = op.bl_idname
        recall_properties['args'] = op_args

        # Store new recall properties.
        ob['recall'] = recall_properties


# Apply view rotation to objects if "Align To" for
# new objects was set to "VIEW" in the User Preference.
def apply_object_align(context, ob):
    obj_align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit):
    scene = context.scene
    obj_act = scene.objects.active

    # Can't edit anything, unless we have an active obj.
    if edit and not obj_act:
        return None

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    if edit:
        # Replace geometry of existing object

        # Use the active obj and select it.
        ob_new = obj_act
        ob_new.selected = True

        if obj_act.mode == 'OBJECT':
            # Get existing mesh datablock.
            old_mesh = ob_new.data

            # Set object data to nothing
            ob_new.data = None

            # Clear users of existing mesh datablock.
            old_mesh.user_clear()

            # Remove old mesh datablock if no users are left.
            if (old_mesh.users == 0):
                bpy.data.meshes.remove(old_mesh)

            # Assign new mesh datablock.
            ob_new.data = mesh

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.selected = True

        # Place the object at the 3D cursor location.
        ob_new.location = scene.cursor_location

        apply_object_align(context, ob_new)

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.selected = True

            # Apply location of new object.
            scene.update()

            # Join new object into the active.
            bpy.ops.object.join()

            # Switching back to EditMode.
            bpy.ops.object.mode_set(mode='EDIT')

            ob_new = obj_act

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new

    return ob_new


# @todo Simplify the face creation code (i.e. remove all that hardcoded
# stuff if possible)
def add_sqorus(sqorus_width, sqorus_height, sqorus_depth):
    verts = []
    faces = []

    half_depth = sqorus_depth / 2.0

    for i in range(4):
        y = float(i) / 3.0 * sqorus_height

        for j in range(4):
            x = float(j) / 3.0 * sqorus_width

            verts.append(Vector(x, y, half_depth))
            verts.append(Vector(x, y, -half_depth))

    for i in (0, 2, 4, 8, 12, 16, 18, 20):
        faces.append([i, i + 2, i + 10, i + 8])
        faces.append([i + 1, i + 9, i + 11, i + 3])

    for i in (0, 8, 16):
        faces.append([i, i + 8, i + 9, i + 1])

    for i in (6, 14, 22):
        faces.append([i, i + 1, i + 9, i + 8])

    for i in (0, 2, 4):
        faces.append([i, i + 1, i + 3, i + 2])

    for i in (24, 26, 28):
        faces.append([i, i + 2, i + 3, i + 1])

    i = 10
    faces.append([i, i + 1, i + 9, i + 8])

    i = 12
    faces.append([i, i + 8, i + 9, i + 1])

    i = 18
    faces.append([i, i + 1, i + 3, i + 2])

    i = 10
    faces.append([i, i + 2, i + 3, i + 1])

    return verts, faces


class AddSqorus(bpy.types.Operator):
    '''Add a sqorus mesh.'''
    bl_idname = "mesh.primitive_sqorus_add"
    bl_label = "Add Sqorus"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    width = FloatProperty(name="Width",
        description="Width of Sqorus",
        min=0.01,
        max=9999.0,
        default=2.0)
    height = FloatProperty(name="Height",
        description="Height of Sqorus",
        min=0.01,
        max=9999.0,
        default=2.0)
    depth = FloatProperty(name="Depth",
        description="Depth of Sqorus",
        min=0.01,
        max=9999.0,
        default=2.0)

    def execute(self, context):
        props = self.properties

        # Create mesh geometry
        verts, faces = add_sqorus(
            props.width,
            props.height,
            props.depth)

        # Create mesh object (and meshdata)
        obj = create_mesh_object(context, verts, [], faces, "Sqorus",
            props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "width": props.width,
            "height": props.height,
            "depth": props.depth}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


# Register the operator
menu_func = (lambda self, context: self.layout.operator(AddSqorus.bl_idname,
            text="Add Sqorus", icon='PLUGIN'))


def register():
    bpy.types.register(AddSqorus)

    # Add "Sqorus" menu to the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddSqorus)

    # Remove "Sqorus" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
