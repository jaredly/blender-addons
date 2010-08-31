#
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    "name": "Object Property Chart",
    "author": "Campbell Barton (ideasman42)",
    "version": (0,1),
    "blender": (2, 5, 3),
    "api": 31667,
    "location": "Tool Shelf",
    "description": "Edit arbitrary selected properties for objects of the same type",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/3D interaction/Object Property Chart",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22701&group_id=153&atid=469",
    "category": "3D View"}

"""List properties of selected objects"""

import bpy

def _property_chart_data_get(self, context):
    # eg. context.active_object
    obj = eval("context.%s" % self.context_data_path_active)

    if obj is None:
        return None, None
    
    # eg. context.selected_objects[:]
    selected_objects = eval("context.%s" % self.context_data_path_selected)[:]

    if not selected_objects:
        return None, None
    
    return obj, selected_objects


def _property_chart_draw(self, context):
    '''
    This function can run for different types.
    '''
    obj, selected_objects = _property_chart_data_get(self, context)
    
    if not obj:
        return

    # active first
    try:
        active_index = selected_objects.index(obj)
    except ValueError:
        active_index = -1
    
    if active_index > 0: # not the first alredy
        selected_objects[0], selected_objects[active_index] = selected_objects[active_index], selected_objects[0]
    
    id_storage = context.scene
    
    strings = id_storage.get(self._PROP_STORAGE_ID)
    
    if strings is None:
        strings = id_storage[self._PROP_STORAGE_ID] = "data data.name"

    if strings:

        def obj_prop_get(obj, attr_string):
            """return a pair (rna_base, "rna_property") to give to the rna UI property function"""
            attrs = attr_string.split(".")
            val_new = obj
            for i, attr in enumerate(attrs):
                val_old = val_new
                val_new = getattr(val_old, attr, Ellipsis)
                
                if val_new == Ellipsis:
                    return None, None                        
            return val_old, attrs[-1]

        strings = strings.split()

        prop_all = []

        for obj in selected_objects:
            prop_pairs = []
            prop_found = False
            for attr_string in strings:
                prop_pairs.append(obj_prop_get(obj, attr_string))
                if prop_found == False and prop_pairs[-1] != (None, None): 
                    prop_found = True

            if prop_found:
                prop_all.append((obj, prop_pairs))


        # Collected all props, now display them all
        layout = self.layout

        row = layout.row(align=True)

        col = row.column()
        col.label(text="name")
        for obj, prop_pairs in prop_all:
            col.prop(obj, "name", text="")

        for i in range(len(strings)):
            col = row.column()

            # name and copy button
            rowsub = col.row(align=False)
            rowsub.label(text=strings[i].rsplit(".", 1)[-1])
            props = rowsub.operator("wm.chart_copy", text="", icon='PASTEDOWN', emboss=False)
            props.data_path_active = self.context_data_path_active
            props.data_path_selected = self.context_data_path_selected
            props.data_path = strings[i]

            for obj, prop_pairs in prop_all:
                data, attr = prop_pairs[i]
                if data:
                    col.prop(data, attr, text="")# , emboss=obj==active_object
                else:
                    col.label(text="<missing>")

    # edit the display props
    col = layout.column()
    col.label(text="Object Properties")
    col.prop(id_storage, '["%s"]' % self._PROP_STORAGE_ID, text="")


class View3DEditProps(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    bl_label = "Property Chart"
    bl_context = "objectmode"
    
    _PROP_STORAGE_ID = "view3d_edit_props"
    
    # _property_chart_draw needs these
    context_data_path_active = "active_object"
    context_data_path_selected = "selected_objects"

    draw = _property_chart_draw


class SequencerEditProps(bpy.types.Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    
    bl_label = "Property Chart"
    
    _PROP_STORAGE_ID = "sequencer_edit_props"
    
    # _property_chart_draw needs these
    context_data_path_active = "scene.sequence_editor.active_strip"
    context_data_path_selected = "selected_sequences"

    draw = _property_chart_draw

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor is not None

# Operator to copy properties


def _property_chart_copy(self, context):
    obj, selected_objects = _property_chart_data_get(self, context)
    
    if not obj:
        return

    data_path = self.properties.data_path

    # quick & nasty method!
    for obj_iter in selected_objects:
        if obj != obj_iter:
            try:
                exec("obj_iter.%s = obj.%s" % (data_path, data_path))
            except:
                # just incase we need to know what went wrong!
                import traceback
                traceback.print_exc()

from bpy.props import StringProperty


class CopyPropertyChart(bpy.types.Operator):
    "Open a path in a file browser"
    bl_idname = "wm.chart_copy"
    bl_label = "Copy properties from active to selected"

    data_path_active = StringProperty()
    data_path_selected = StringProperty()
    data_path = StringProperty()

    def execute(self, context):
        # so attributes are found for '_property_chart_data_get()'
        self.context_data_path_active = self.properties.data_path_active
        self.context_data_path_selected = self.properties.data_path_selected

        _property_chart_copy(self, context)

        return {'FINISHED'}


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()
