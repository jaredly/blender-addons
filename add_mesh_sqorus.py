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
    'version': '1.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Squorus to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Sqorus',
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
import mathutils


def add_sqorus(sqorus_width, sqorus_height, sqorus_depth):

    Vector = mathutils.Vector
    verts = []
    faces = []
    half_depth = sqorus_depth * .5

    for i in range(4):
        y = float(i) / 3 * sqorus_height

        for j in range(4):
            x = float(j) / 3 * sqorus_width

            verts.extend(Vector(x, y, half_depth))
            verts.extend(Vector(x, y, -half_depth))

    for i in (0, 2, 4, 8, 12, 16, 18, 20):
        faces.extend([i, i + 2, i + 10, i + 8])
        faces.extend([i + 1, i + 9, i + 11, i + 3])

    for i in (0, 8, 16):
        faces.extend([i, i + 8, i + 9, i + 1])

    for i in (6, 14, 22):
        faces.extend([i, i + 1, i + 9, i + 8])

    for i in (0, 2, 4):
        faces.extend([i, i + 1, i + 3, i + 2])

    for i in (24, 26, 28):
        faces.extend([i, i + 2, i + 3, i + 1])

    i = 10
    faces.extend([i, i + 1, i + 9, i + 8])

    i = 12
    faces.extend([i, i + 8, i + 9, i + 1])

    i = 18
    faces.extend([i, i + 1, i + 3, i + 2])

    i = 10
    faces.extend([i, i + 2, i + 3, i + 1])

    return verts, faces

from bpy.props import FloatProperty


class AddSqorus(bpy.types.Operator):
    '''Add a sqorus mesh.'''
    bl_idname = "mesh.sqorus_add"
    bl_label = "Add Sqorus"
    bl_options = {'REGISTER', 'UNDO'}

    sqorus_width = FloatProperty(name="Width",
        description="Width of Sqorus",
        default=2.00, min=0.01, max=100.00)
    sqorus_height = FloatProperty(name="Height",
        description="Height of Sqorus",
        default=2.00, min=0.01, max=100.00)
    sqorus_depth = FloatProperty(name="Depth",
        description="Depth of Sqorus",
        default=2.00, min=0.01, max=100.00)

    def execute(self, context):

        verts_loc, faces = add_sqorus(self.properties.sqorus_width,
                                    self.properties.sqorus_height,
                                    self.properties.sqorus_depth)

        mesh = bpy.data.meshes.new("Sqorus")

        mesh.add_geometry(int(len(verts_loc) / 3), 0, int(len(faces) / 4))
        mesh.verts.foreach_set("co", verts_loc)
        mesh.faces.foreach_set("verts_raw", faces)
        mesh.faces.foreach_set("smooth", [False] * len(mesh.faces))

        scene = context.scene

        # ugh
        for ob in scene.objects:
            ob.selected = False

        mesh.update()
        ob_new = bpy.data.objects.new("Sqorus", mesh)
        ob_new.data = mesh
        scene.objects.link(ob_new)
        scene.objects.active = ob_new
        ob_new.selected = True

        ob_new.location = tuple(context.scene.cursor_location)

        return {'FINISHED'}


# Register the operator
# Add to a menu, reuse an icon used elsewhere that happens to have fitting name
# unfortunately, the icon shown is the one I expected from looking at the
# blenderbuttons file from the release/datafiles directory

menu_func = (lambda self, context: self.layout.operator(AddSqorus.bl_idname,
            text="Add Sqorus", icon='PLUGIN'))


def register():
    bpy.types.register(AddSqorus)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddSqorus)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

# Remove "Sqorus" menu from the "Add Mesh" menu.
#space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
