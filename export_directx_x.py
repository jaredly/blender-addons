#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****


#NOTE: ========================================================
#I've begun work on a Full Animation feature to more accurately export 
#FCurve data.  It's going pretty well, but I'm having some trouble with
#axis flipping.  To "enable" the feature, uncomment line #988
#The problem is in the WriteFullAnimationSet function at line #948
# - Chris (2010-7-11)


#One line description for early versions of Blender 2.52.
"Export: DirectX Model Format (.x)"

bl_addon_info = {
    'name': 'Export: DirectX Model Format (.x)',
    'author': 'Chris Foster (Kira Vakaan)',
    'version': '1.1',
    'blender': (2, 5, 3),
    'location': 'File > Export',
    'description': 'Export to the DirectX Model Format',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/File_I-O/DirectX_Exporter',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=22795&group_id=153&atid=469',
    'category': 'Import/Export'}

"""
Name: 'DirectX Exporter'
Blender: 252
Group: 'Export'
Tooltip: 'Exports to the DirectX model file format (.x)'
"""

__author__ = "Chris Foster (Kira Vakaan)"
__url__ = "http://wiki.blender.org/index.php/Extensions:2.5/Py/" \
        "Scripts/File_I-O/DirectX_Exporter"
__version__ = "1.1"
__bpydoc__ = """\
"""

import os
from math import radians

import bpy
from mathutils import *

#Container for the exporter settings
class DirectXExporterSettings:
    def __init__(self,
                 context,
                 FilePath,
                 CoordinateSystem=1,
                 RotateX=True,
                 FlipNormals=False,
                 ApplyModifiers=False,
                 IncludeFrameRate=False,
                 ExportTextures=True,
                 ExportArmatures=False,
                 ExportAnimation=0,
                 ExportMode=1,
                 Verbose=False):
        self.context = context
        self.FilePath = FilePath
        self.CoordinateSystem = int(CoordinateSystem)
        self.RotateX = RotateX
        self.FlipNormals = FlipNormals
        self.ApplyModifiers = ApplyModifiers
        self.IncludeFrameRate = IncludeFrameRate
        self.ExportTextures = ExportTextures
        self.ExportArmatures = ExportArmatures
        self.ExportAnimation = int(ExportAnimation)
        self.ExportMode = int(ExportMode)
        self.Verbose = Verbose


def LegalName(Name):
    NewName = Name.replace(".", "_")
    NewName = NewName.replace(" ", "_")
    if NewName[0].isdigit() or NewName in ["ARRAY",
                                           "DWORD",
                                           "UCHAR",
                                           "BINARY",
                                           "FLOAT",
                                           "ULONGLONG",
                                           "BINARY_RESOURCE",
                                           "SDWORD",
                                           "UNICODE",
                                           "CHAR",
                                           "STRING",
                                           "WORD",
                                           "CSTRING",
                                           "SWORD",
                                           "DOUBLE",
                                           "TEMPLATE"]:
        NewName = "_" + NewName
    return NewName


def ExportDirectX(Config):
    print("----------\nExporting to {}".format(Config.FilePath))
    if Config.Verbose:
        print("Opening File...", end=" ")
    Config.File = open(Config.FilePath, "w")
    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("Generating Object list for export...", end=" ")
    if Config.ExportMode == 1:
        Config.ExportList = [Object for Object in Config.context.scene.objects
                             if Object.type in ("ARMATURE", "EMPTY", "MESH")
                             and Object.parent == None]
    else:
        ExportList = [Object for Object in Config.context.selected_objects
                      if Object.type in ("ARMATURE", "EMPTY", "MESH")]
        Config.ExportList = [Object for Object in ExportList
                             if Object.parent not in ExportList]
    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("Setting up...", end=" ")
    Config.SystemMatrix = Matrix()
    if Config.RotateX:
        Config.SystemMatrix *= RotationMatrix(radians(-90), 4, "X")
    if Config.CoordinateSystem == 1:
        Config.SystemMatrix *= ScaleMatrix(-1, 4, Vector((0, 1, 0)))
    Config.InverseSystemMatrix = Config.SystemMatrix.copy().invert()

    if Config.ExportAnimation:
        CurrentFrame = bpy.context.scene.frame_current
        bpy.context.scene.frame_current = bpy.context.scene.frame_current
    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("Writing Header...", end=" ")
    WriteHeader(Config)
    if Config.Verbose:
        print("Done")

    Config.Whitespace = 0
    Config.ObjectList = []
    if Config.Verbose:
        print("Writing Objects...")
    WriteObjects(Config, Config.ExportList)
    if Config.Verbose:
        print("Done")

    if Config.ExportAnimation:
        if Config.IncludeFrameRate:
            if Config.Verbose:
                print("Writing Frame Rate...", end=" ")
            Config.File.write("{}AnimTicksPerSecond {{\n".format("  " * Config.Whitespace))
            Config.Whitespace += 1
            Config.File.write("{}{};\n".format("  " * Config.Whitespace, int(bpy.context.scene.render.fps / bpy.context.scene.render.fps_base)))
            Config.Whitespace -= 1
            Config.File.write("{}}}\n".format("  " * Config.Whitespace))
            if Config.Verbose:
                print("Done")
        if Config.Verbose:
            print("Writing Animation...")
        if Config.ExportAnimation==1:
            WriteKeyedAnimationSet(Config)
        else:
            WriteFullAnimationSet(Config)
        bpy.context.scene.frame_current = CurrentFrame
        if Config.Verbose:
            print("Done")

    CloseFile(Config)
    print("Finished")


def GetObjectChildren(Parent):
    return [Object for Object in Parent.children
            if Object.type in ("ARMATURE", "EMPTY", "MESH")]

#Returns the vertex count of Mesh, counting each vertex for every face.
def GetMeshVertexCount(Mesh):
    VertexCount = 0
    for Face in Mesh.faces:
        VertexCount += len(Face.verts)
    return VertexCount

#Returns the file path of first image texture from Material.
def GetMaterialTexture(Material):
    if Material:
        #Create a list of Textures that have type "IMAGE"
        ImageTextures = [Material.texture_slots[TextureSlot].texture for TextureSlot in Material.texture_slots.keys() if Material.texture_slots[TextureSlot].texture.type == "IMAGE"]
        #Refine a new list with only image textures that have a file source
        ImageFiles = [os.path.basename(Texture.image.filename) for Texture in ImageTextures if Texture.image.source == "FILE"]
        if ImageFiles:
            return ImageFiles[0]
    return None


def WriteHeader(Config):
    Config.File.write("xof 0303txt 0032\n\n")
    if Config.ExportArmatures:
        Config.File.write("template XSkinMeshHeader {\n\
  <3cf169ce-ff7c-44ab-93c0-f78f62d172e2>\n\
  WORD nMaxSkinWeightsPerVertex;\n\
  WORD nMaxSkinWeightsPerFace;\n\
  WORD nBones;\n\
}\n\n\
template SkinWeights {\n\
  <6f0d123b-bad2-4167-a0d0-80224f25fabb>\n\
  STRING transformNodeName;\n\
  DWORD nWeights;\n\
  array DWORD vertexIndices[nWeights];\n\
  array float weights[nWeights];\n\
  Matrix4x4 matrixOffset;\n\
}\n\n")


def WriteObjects(Config, ObjectList):
    Config.ObjectList += ObjectList

    for Object in ObjectList:
        if Config.Verbose:
            print("  Writing Object: {}...".format(Object.name))
        Config.File.write("{}Frame {} {{\n".format("  " * Config.Whitespace, LegalName(Object.name)))

        Config.Whitespace += 1
        if Config.Verbose:
            print("    Writing Local Matrix...", end=" ")
        WriteLocalMatrix(Config, Object)
        if Config.Verbose:
            print("Done")

        if Config.ExportArmatures and Object.type == "ARMATURE":
            Armature = Object.data
            ParentList = [Bone for Bone in Armature.bones if Bone.parent == None]
            if Config.Verbose:
                print("    Writing Armature Bones...")
            WriteArmatureBones(Config, Object, ParentList)
            if Config.Verbose:
                print("    Done")

        ChildList = GetObjectChildren(Object)
        if Config.Verbose:
            print("    Writing Children...")
        WriteObjects(Config, ChildList)
        if Config.Verbose:
            print("    Done Writing Children")

        if Object.type == "MESH":
            if Config.Verbose:
                print("    Generating Mesh...", end=" ")
            Mesh = Object.create_mesh(bpy.context.scene, (Config.ApplyModifiers | Config.ExportArmatures), "PREVIEW")
            if Config.Verbose:
                print("Done")
            if Config.Verbose:
                print("    Writing Mesh...")
            WriteMesh(Config, Object, Mesh)
            if Config.Verbose:
                print("    Done")
            bpy.data.meshes.remove(Mesh)

        Config.Whitespace -= 1
        Config.File.write("{}}} //End of {}\n".format("  " * Config.Whitespace, LegalName(Object.name)))
        if Config.Verbose:
            print("  Done Writing Object: {}".format(Object.name))


def WriteLocalMatrix(Config, Object):
    if Object.parent:
        LocalMatrix = Object.parent.matrix_world.copy().invert()
    else:
        LocalMatrix = Matrix()
    LocalMatrix *= Object.matrix_world
    LocalMatrix = Config.SystemMatrix * LocalMatrix * Config.InverseSystemMatrix

    Config.File.write("{}FrameTransformMatrix {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, LocalMatrix[0][0], LocalMatrix[0][1], LocalMatrix[0][2], LocalMatrix[0][3]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, LocalMatrix[1][0], LocalMatrix[1][1], LocalMatrix[1][2], LocalMatrix[1][3]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, LocalMatrix[2][0], LocalMatrix[2][1], LocalMatrix[2][2], LocalMatrix[2][3]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, LocalMatrix[3][0], LocalMatrix[3][1], LocalMatrix[3][2], LocalMatrix[3][3]))
    Config.Whitespace -= 1
    Config.File.write("{}}}\n".format("  " * Config.Whitespace))


def WriteArmatureBones(Config, Object, ChildList):
    PoseBones = Object.pose.bones
    for Bone in ChildList:
        if Config.Verbose:
            print("      Writing Bone: {}...".format(Bone.name), end=" ")
        Config.File.write("{}Frame {} {{\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))
        Config.Whitespace += 1

        PoseBone = PoseBones[Bone.name]

        if Bone.parent:
            BoneMatrix = (PoseBone.parent.matrix *
                          RotationMatrix(radians(-90), 4, "X")).invert()
        else:
            BoneMatrix = Matrix()

        BoneMatrix *= PoseBone.matrix * RotationMatrix(radians(-90), 4, "X")
        BoneMatrix = Config.SystemMatrix * BoneMatrix * Config.InverseSystemMatrix

        Config.File.write("{}FrameTransformMatrix {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][0], BoneMatrix[0][1], BoneMatrix[0][2], BoneMatrix[0][3]))
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[1][0], BoneMatrix[1][1], BoneMatrix[1][2], BoneMatrix[1][3]))
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[2][0], BoneMatrix[2][1], BoneMatrix[2][2], BoneMatrix[2][3]))
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, BoneMatrix[3][0], BoneMatrix[3][1], BoneMatrix[3][2], BoneMatrix[3][3]))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))

        if Config.Verbose:
            print("Done")
        WriteArmatureBones(Config, Object, Bone.children)
        Config.Whitespace -= 1

        Config.File.write("{}}} //End of {}\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))


def WriteMesh(Config, Object, Mesh):
    Config.File.write("{}Mesh {{ //{} Mesh\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    if Config.Verbose:
        print("      Writing Mesh Vertices...", end=" ")
    WriteMeshVertices(Config, Mesh)
    if Config.Verbose:
        print("Done\n      Writing Mesh Normals...", end=" ")
    WriteMeshNormals(Config, Mesh)
    if Config.Verbose:
        print("Done\n      Writing Mesh Materials...", end=" ")
    WriteMeshMaterials(Config, Mesh)
    if Config.Verbose:
        print("Done")
    if Mesh.uv_textures:
        if Config.Verbose:
            print("      Writing Mesh UV Coordinates...", end=" ")
        WriteMeshUVCoordinates(Config, Mesh)
        if Config.Verbose:
            print("Done")
    if Config.ExportArmatures:
        if Config.Verbose:
            print("      Writing Mesh Skin Weights...", end=" ")
        WriteMeshSkinWeights(Config, Object, Mesh)
        if Config.Verbose:
            print("Done")

    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} Mesh\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMeshVertices(Config, Mesh):
    Index = 0
    VertexCount = GetMeshVertexCount(Mesh)
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, VertexCount))

    for Face in Mesh.faces:
        Vertices = list(Face.verts)

        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]
        for Vertex in [Mesh.verts[Vertex] for Vertex in Vertices]:
            Position = Config.SystemMatrix * Vertex.co
            Config.File.write("{}{:9f};{:9f};{:9f};".format("  " * Config.Whitespace, Position[0], Position[1], Position[2]))
            Index += 1
            if Index == VertexCount:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")

    Index = 0
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, len(Mesh.faces)))

    for Face in Mesh.faces:
        Config.File.write("{}{};".format("  " * Config.Whitespace, len(Face.verts)))
        for Vertex in Face.verts:
            Config.File.write("{};".format(Index))
            Index += 1
        if Index == VertexCount:
            Config.File.write(";\n")
        else:
            Config.File.write(",\n")


def WriteMeshNormals(Config, Mesh):
    Config.File.write("{}MeshNormals {{ //{} Normals\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    Index = 0
    VertexCount = GetMeshVertexCount(Mesh)
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, VertexCount))

    for Face in Mesh.faces:
        Vertices = list(Face.verts)

        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]
        for Vertex in [Mesh.verts[Vertex] for Vertex in Vertices]:
            if Face.smooth:
                Normal = Config.SystemMatrix * Vertex.normal
            else:
                Normal = Config.SystemMatrix * Face.normal
            if Config.FlipNormals:
                Normal = -Normal
            Config.File.write("{}{:9f};{:9f};{:9f};".format("  " * Config.Whitespace, Normal[0], Normal[1], Normal[2]))
            Index += 1
            if Index == VertexCount:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")

    Index = 0
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, len(Mesh.faces)))

    for Face in Mesh.faces:
        Config.File.write("{}{};".format("  " * Config.Whitespace, len(Face.verts)))
        for Vertex in Face.verts:
            Config.File.write("{};".format(Index))
            Index += 1
        if Index == VertexCount:
            Config.File.write(";\n")
        else:
            Config.File.write(",\n")
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} Normals\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMeshMaterials(Config, Mesh):
    Config.File.write("{}MeshMaterialList {{ //{} Material List\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    Materials = Mesh.materials
    if Materials.keys():
        MaterialIndexes = {}
        for Face in Mesh.faces:
            if Materials[Face.material_index] not in MaterialIndexes:
                MaterialIndexes[Materials[Face.material_index]] = len(MaterialIndexes)

        FaceCount = len(Mesh.faces)
        Index = 0
        Config.File.write("{}{};\n{}{};\n".format("  " * Config.Whitespace, len(MaterialIndexes), "  " * Config.Whitespace, FaceCount))
        for Face in Mesh.faces:
            Config.File.write("{}{}".format("  " * Config.Whitespace, MaterialIndexes[Materials[Face.material_index]]))
            Index += 1
            if Index == FaceCount:
                Config.File.write(";;\n")
            else:
                Config.File.write(",\n")

        Materials = [Item[::-1] for Item in MaterialIndexes.items()]
        Materials.sort()
        for Material in Materials:
            WriteMaterial(Config, Material[1])
    else:
        Config.File.write("{}1;\n{}1;\n{}0;;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, "  " * Config.Whitespace))
        WriteMaterial(Config)

    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} Material List\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMaterial(Config, Material=None):
    if Material:
        Config.File.write("{}Material {} {{\n".format("  " * Config.Whitespace, LegalName(Material.name)))
        Config.Whitespace += 1

        Diffuse = list(Material.diffuse_color)
        Diffuse.append(Material.alpha)
        Specularity = Material.specular_intensity
        Specular = list(Material.specular_color)

        Config.File.write("{}{:9f};{:9f};{:9f};{:9f};;\n".format("  " * Config.Whitespace, Diffuse[0], Diffuse[1], Diffuse[2], Diffuse[3]))
        Config.File.write("{}{:9f};\n".format("  " * Config.Whitespace, 2 * (1.0 - Specularity)))
        Config.File.write("{}{:9f};{:9f};{:9f};;\n".format("  " * Config.Whitespace, Specular[0], Specular[1], Specular[2]))
    else:
        Config.File.write("{}Material Default_Material {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{} 1.000000; 1.000000; 1.000000; 1.000000;;\n".format("  " * Config.Whitespace))
        Config.File.write("{} 1.500000;\n".format("  " * Config.Whitespace))
        Config.File.write("{} 1.000000; 1.000000; 1.000000;;\n".format("  " * Config.Whitespace))
    Config.File.write("{} 0.000000; 0.000000; 0.000000;;\n".format("  " * Config.Whitespace))
    if Config.ExportTextures:
        Texture = GetMaterialTexture(Material)
        if Texture:
            Config.File.write("{}TextureFilename {{\"{}\";}}\n".format("  " * Config.Whitespace, Texture))
    Config.Whitespace -= 1
    Config.File.write("{}}}\n".format("  " * Config.Whitespace))


def WriteMeshUVCoordinates(Config, Mesh):
    Config.File.write("{}MeshTextureCoords {{ //{} UV Coordinates\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    UVCoordinates = None
    for UV in Mesh.uv_textures:
        if UV.active_render:
            UVCoordinates = UV.data
            break

    Index = 0
    VertexCount = GetMeshVertexCount(Mesh)
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, VertexCount))

    for Face in UVCoordinates:
        Vertices = []
        for Vertex in Face.uv:
            Vertices.append(tuple(Vertex))
        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]
        for Vertex in Vertices:
            Config.File.write("{}{:9f};{:9f};".format("  " * Config.Whitespace, Vertex[0], 1 - Vertex[1]))
            Index += 1
            if Index == VertexCount:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} UV Coordinates\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMeshSkinWeights(Config, Object, Mesh):
    ArmatureList = [Modifier for Modifier in Object.modifiers if Modifier.type == "ARMATURE"]
    if ArmatureList:
        ArmatureObject = ArmatureList[0].object
        Armature = ArmatureObject.data

        PoseBones = ArmatureObject.pose.bones

        MaxInfluences = 0
        UsedBones = set()
        #Maps bones to a list of vertices they affect
        VertexGroups = {}
        
        for Vertex in Mesh.verts:
            #BoneInfluences contains the bones of the armature that affect the current vertex
            BoneInfluences = [PoseBones[Object.vertex_groups[Group.group].name] for Group in Vertex.groups if Object.vertex_groups[Group.group].name in PoseBones]
            if len(BoneInfluences) > MaxInfluences:
                MaxInfluences = len(BoneInfluences)
            for Bone in BoneInfluences:
                UsedBones.add(Bone)
                if Bone not in VertexGroups:
                    VertexGroups[Bone] = [Vertex]
                else:
                    VertexGroups[Bone].append(Vertex)
        BoneCount = len(UsedBones)

        Config.File.write("{}XSkinMeshHeader {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}{};\n{}{};\n{}{};\n".format("  " * Config.Whitespace, MaxInfluences, "  " * Config.Whitespace, MaxInfluences * 3, "  " * Config.Whitespace, BoneCount))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))

        for Bone in UsedBones:
            VertexCount = 0
            VertexIndexes = [Vertex.index for Vertex in VertexGroups[Bone]]
            for Face in Mesh.faces:
                for Vertex in Face.verts:
                    if Vertex in VertexIndexes:
                        VertexCount += 1

            Config.File.write("{}SkinWeights {{\n".format("  " * Config.Whitespace))
            Config.Whitespace += 1
            Config.File.write("{}\"{}\";\n{}{};\n".format("  " * Config.Whitespace, LegalName(ArmatureObject.name) + "_" + LegalName(Bone.name), "  " * Config.Whitespace, VertexCount))

            VertexWeights = []
            Index = 0
            WrittenIndexes = 0
            for Face in Mesh.faces:
                FaceVertices = list(Face.verts)
                if Config.CoordinateSystem == 1:
                    FaceVertices = FaceVertices[::-1]
                for Vertex in FaceVertices:
                    if Vertex in VertexIndexes:
                        Config.File.write("{}{}".format("  " * Config.Whitespace, Index))

                        GroupIndexes = {Object.vertex_groups[Group.group].name: Index for Index, Group in enumerate(Mesh.verts[Vertex].groups) if Object.vertex_groups[Group.group].name in PoseBones}

                        WeightTotal = 0.0
                        for Weight in [Group.weight for Group in Mesh.verts[Vertex].groups if Object.vertex_groups[Group.group].name in PoseBones]:
                            WeightTotal += Weight

                        if WeightTotal:
                            VertexWeights.append(Mesh.verts[Vertex].groups[GroupIndexes[Bone.name]].weight / WeightTotal)
                        else:
                            VertexWeights.append(0.0)

                        WrittenIndexes += 1
                        if WrittenIndexes == VertexCount:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                    Index += 1

            for Index, Weight in enumerate(VertexWeights):
                Config.File.write("{}{:8f}".format("  " * Config.Whitespace, Weight))
                if Index == (VertexCount - 1):
                    Config.File.write(";\n")
                else:
                    Config.File.write(",\n")

            PoseBone = PoseBones[Bone.name]

            BoneMatrix = (PoseBone.matrix * RotationMatrix(radians(-90), 4, "X")).invert()
            BoneMatrix *= ArmatureObject.matrix_world.copy().invert()

            if Object.parent and Object.parent != ArmatureObject:
                BoneMatrix *= Object.parent.matrix_world.copy().invert()

            BoneMatrix *= Object.matrix_world

            BoneMatrix = Config.SystemMatrix * BoneMatrix * Config.InverseSystemMatrix

            Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][0], BoneMatrix[0][1], BoneMatrix[0][2], BoneMatrix[0][3]))
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[1][0], BoneMatrix[1][1], BoneMatrix[1][2], BoneMatrix[1][3]))
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[2][0], BoneMatrix[2][1], BoneMatrix[2][2], BoneMatrix[2][3]))
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, BoneMatrix[3][0], BoneMatrix[3][1], BoneMatrix[3][2], BoneMatrix[3][3]))
            Config.Whitespace -= 1
            Config.File.write("{}}}  //End of {} Skin Weights\n".format("  " * Config.Whitespace, LegalName(ArmatureObject.name) + "_" + LegalName(Bone.name)))


def WriteKeyedAnimationSet(Config):
    Config.File.write("{}AnimationSet {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    for Object in [Object for Object in Config.ObjectList if Object.animation_data]:
        if Config.Verbose:
            print("  Writing Animation Data for Object: {}".format(Object.name))
        Action = Object.animation_data.action
        if Action:
            PositionFCurves = [None, None, None]
            RotationFCurves = [None, None, None]
            ScaleFCurves = [None, None, None]
            for FCurve in Action.fcurves:
                if FCurve.data_path == "location":
                    PositionFCurves[FCurve.array_index] = FCurve
                elif FCurve.data_path == "rotation_euler":
                    RotationFCurves[FCurve.array_index] = FCurve
                elif FCurve.data_path == "scale":
                    ScaleFCurves[FCurve.array_index] = FCurve
            if [FCurve for FCurve in PositionFCurves + RotationFCurves + ScaleFCurves if FCurve]:
                Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name)))

                #Position
                if Config.Verbose:
                    print("    Writing Position...", end=" ")
                AllKeyframes = set()
                for Index, FCurve in enumerate(PositionFCurves):
                    if FCurve:
                        Keyframes = []
                        for Keyframe in FCurve.keyframe_points:
                            Keyframes.append(Keyframe.co)
                            AllKeyframes.add(int(Keyframe.co[0]))
                        PositionFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                AllKeyframes = list(AllKeyframes)
                AllKeyframes.sort()
                if len(AllKeyframes):
                    Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.set_frame(Keyframe)
                        Position = Vector()
                        Position[0] = ((PositionFCurves[0][Keyframe] if Keyframe in PositionFCurves[0] else Object.location[0]) if PositionFCurves[0] else Object.location[0])
                        Position[1] = ((PositionFCurves[1][Keyframe] if Keyframe in PositionFCurves[1] else Object.location[1]) if PositionFCurves[1] else Object.location[1])
                        Position[2] = ((PositionFCurves[2][Keyframe] if Keyframe in PositionFCurves[2] else Object.location[2]) if PositionFCurves[2] else Object.location[2])
                        Position = Config.SystemMatrix * Position
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
                else:
                    Config.File.write("{}2;\n{}1;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace))
                    bpy.context.scene.set_frame(bpy.context.scene.frame_start)
                    Position = Config.SystemMatrix * Object.location
                    Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, ("0;3;").ljust(8), Position[0], Position[1], Position[2]))
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("Done")

                #Rotation
                if Config.Verbose:
                    print("    Writing Rotation...", end=" ")
                AllKeyframes = set()
                for Index, FCurve in enumerate(RotationFCurves):
                    if FCurve:
                        Keyframes = []
                        for Keyframe in FCurve.keyframe_points:
                            Keyframes.append(Keyframe.co)
                            AllKeyframes.add(int(Keyframe.co[0]))
                        RotationFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                AllKeyframes = list(AllKeyframes)
                AllKeyframes.sort()
                if len(AllKeyframes):
                    Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.set_frame(Keyframe)
                        Rotation = Euler()
                        Rotation[0] = ((RotationFCurves[0][Keyframe] if Keyframe in RotationFCurves[0] else Object.rotation_euler[0]) if RotationFCurves[0] else Object.rotation_euler[0])
                        Rotation[1] = ((RotationFCurves[1][Keyframe] if Keyframe in RotationFCurves[1] else Object.rotation_euler[1]) if RotationFCurves[1] else Object.rotation_euler[1])
                        Rotation[2] = ((RotationFCurves[2][Keyframe] if Keyframe in RotationFCurves[2] else Object.rotation_euler[2]) if RotationFCurves[2] else Object.rotation_euler[2])
                        Rotation = (Config.SystemMatrix * (Rotation.to_matrix().to_4x4()) * Config.InverseSystemMatrix).to_quat()
                        Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";4;").ljust(8), - Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                else:
                    Config.File.write("{}0;\n{}1;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace))
                    bpy.context.scene.set_frame(bpy.context.scene.frame_start)
                    Rotation = (Config.SystemMatrix * (Object.rotation_euler.to_matrix().to_4x4()) * Config.InverseSystemMatrix).to_quat()
                    Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, ("0;4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("Done")

                #Scale
                if Config.Verbose:
                    print("    Writing Scale...", end=" ")
                AllKeyframes = set()
                for Index, FCurve in enumerate(ScaleFCurves):
                    if FCurve:
                        Keyframes = []
                        for Keyframe in FCurve.keyframe_points:
                            Keyframes.append(Keyframe.co)
                            AllKeyframes.add(int(Keyframe.co[0]))
                        ScaleFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                AllKeyframes = list(AllKeyframes)
                AllKeyframes.sort()
                if len(AllKeyframes):
                    Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.set_frame(Keyframe)
                        Scale = Vector()
                        Scale[0] = ((ScaleFCurves[0][Keyframe] if Keyframe in ScaleFCurves[0] else Object.scale[0]) if ScaleFCurves[0] else Object.scale[0])
                        Scale[1] = ((ScaleFCurves[1][Keyframe] if Keyframe in ScaleFCurves[1] else Object.scale[1]) if ScaleFCurves[1] else Object.scale[1])
                        Scale[2] = ((ScaleFCurves[2][Keyframe] if Keyframe in ScaleFCurves[2] else Object.scale[2]) if ScaleFCurves[2] else Object.scale[2])
                        Scale = Config.SystemMatrix * Scale
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                else:
                    Config.File.write("{}1;\n{}1;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace))
                    bpy.context.scene.set_frame(bpy.context.scene.frame_start)
                    Scale = Config.SystemMatrix * Object.scale
                    Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, ("0;3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("Done")

                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
            else:
                if Config.Verbose:
                    print("    Object has no useable animation data.")

            if Config.ExportArmatures and Object.type == "ARMATURE":
                if Config.Verbose:
                    print("    Writing Armature Bone Animation Data...")
                PoseBones = Object.pose.bones
                for Bone in PoseBones:
                    if Config.Verbose:
                        print("      Writing Bone: {}...".format(Bone.name))
                    PositionFCurves = [None, None, None]
                    RotationFCurves = [None, None, None, None]
                    ScaleFCurves = [None, None, None]
                    for FCurve in Action.fcurves:
                        if FCurve.data_path == "pose.bones[\"{}\"].location".format(Bone.name):
                            PositionFCurves[FCurve.array_index] = FCurve
                        elif FCurve.data_path == "pose.bones[\"{}\"].rotation_quaternion".format(Bone.name):
                            RotationFCurves[FCurve.array_index] = FCurve
                        elif FCurve.data_path == "pose.bones[\"{}\"].scale".format(Bone.name):
                            ScaleFCurves[FCurve.array_index] = FCurve
                    if not [FCurve for FCurve in PositionFCurves + RotationFCurves + ScaleFCurves if FCurve]:
                        if Config.Verbose:
                            print("        Bone has no useable animation data.\n      Done")
                        continue

                    Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))

                    #Position
                    if Config.Verbose:
                        print("        Writing Position...", end=" ")
                    AllKeyframes = set()
                    for Index, FCurve in enumerate(PositionFCurves):
                        if FCurve:
                            Keyframes = []
                            for Keyframe in FCurve.keyframe_points:
                                Keyframes.append(Keyframe.co)
                                AllKeyframes.add(int(Keyframe.co[0]))
                            PositionFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                    Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    AllKeyframes = list(AllKeyframes)
                    AllKeyframes.sort()
                    if not len(AllKeyframes):
                        AllKeyframes = [bpy.context.scene.frame_start]
                    Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.set_frame(Keyframe)

                        if Bone.parent:
                            PoseMatrix = (Bone.parent.matrix * RotationMatrix(radians(-90), 4, "X")).invert()
                        else:
                            PoseMatrix = Matrix()
                        PoseMatrix *= Bone.matrix * RotationMatrix(radians(-90), 4, "X")

                        PoseMatrix = Config.SystemMatrix * PoseMatrix * Config.InverseSystemMatrix

                        Position = PoseMatrix.translation_part()
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("Done")

                    #Rotation
                    if Config.Verbose:
                        print("        Writing Rotation...", end=" ")
                    AllKeyframes = set()
                    for Index, FCurve in enumerate(RotationFCurves):
                        if FCurve:
                            Keyframes = []
                            for Keyframe in FCurve.keyframe_points:
                                Keyframes.append(Keyframe.co)
                                AllKeyframes.add(int(Keyframe.co[0]))
                            RotationFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                    Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    AllKeyframes = list(AllKeyframes)
                    AllKeyframes.sort()
                    if not len(AllKeyframes):
                        AllKeyframes = [bpy.context.scene.frame_start]
                    Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.set_frame(Keyframe)

                        if Bone.parent:
                            PoseMatrix = (Bone.parent.matrix * RotationMatrix(radians(-90), 4, "X")).invert()
                        else:
                            PoseMatrix = Matrix()
                        PoseMatrix *= Bone.matrix * RotationMatrix(radians(-90), 4, "X")

                        PoseMatrix = Config.SystemMatrix * PoseMatrix * Config.InverseSystemMatrix

                        Rotation = PoseMatrix.rotation_part().to_quat()
                        Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("Done")

                    #Scale
                    if Config.Verbose:
                        print("        Writing Scale...", end=" ")
                    AllKeyframes = set()
                    for Index, FCurve in enumerate(ScaleFCurves):
                        if FCurve:
                            Keyframes = []
                            for Keyframe in FCurve.keyframe_points:
                                Keyframes.append(Keyframe.co)
                                AllKeyframes.add(int(Keyframe.co[0]))
                            ScaleFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                    Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    AllKeyframes = list(AllKeyframes)
                    AllKeyframes.sort()
                    if not len(AllKeyframes):
                        AllKeyframes = [bpy.context.scene.frame_start]
                    Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.set_frame(Keyframe)

                        if Bone.parent:
                            PoseMatrix = (Bone.parent.matrix * RotationMatrix(radians(-90), 4, "X")).invert()
                        else:
                            PoseMatrix = Matrix()
                        PoseMatrix *= Bone.matrix * RotationMatrix(radians(-90), 4, "X")

                        PoseMatrix = Config.SystemMatrix * PoseMatrix * Config.InverseSystemMatrix

                        Scale = PoseMatrix.scale_part()
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("Done")

                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("      Done")
                if Config.Verbose:
                    print("    Done")
        if Config.Verbose:
            print("  Done")

    Config.Whitespace -= 1
    Config.File.write("{}}} //End of AnimationSet\n".format("  " * Config.Whitespace))
    
    
def WriteFullAnimationSet(Config):
    Config.File.write("{}AnimationSet {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    
    KeyframeCount = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
    
    for Object in Config.ObjectList:
        Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name)))
        
        #Position
        Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace,"  " * Config.Whitespace,KeyframeCount))
        for Frame in range(0, KeyframeCount):
            bpy.context.scene.set_frame(Frame)
            Position = Config.SystemMatrix * Object.location
            Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, (str(Frame) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        
        #Rotation
        Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
        for Frame in range(0, KeyframeCount):
            bpy.context.scene.set_frame(Frame)
            #Works pretty well, but causes a slightly noticeable axis flip at 180*
            Rotation = (Config.SystemMatrix * (Object.rotation_euler.to_matrix().to_4x4()) * Config.InverseSystemMatrix).to_quat()
            Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace,(str(Frame) + ";4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        
        #Scale
        Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
        for Frame in range(0, KeyframeCount):
            bpy.context.scene.set_frame(Frame)
            Scale = Config.SystemMatrix * Object.scale
            Config.File.write("{}{}{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace,(str(Frame) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        
        if Config.ExportArmatures and Object.type == "ARMATURE":
            pass
    
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of AnimationSet\n".format("  " * Config.Whitespace))


def CloseFile(Config):
    if Config.Verbose:
        print("Closing File...", end=" ")
    Config.File.close()
    if Config.Verbose:
        print("Done")

CoordinateSystems = []
CoordinateSystems.append(("1", "Left-Handed", ""))
CoordinateSystems.append(("2", "Right-Handed", ""))

AnimationModes = []
AnimationModes.append(("0", "None", ""))
AnimationModes.append(("1", "Keyframes Only", ""))
#AnimationModes.append(("2", "Full Animation", ""))

ExportModes = []
ExportModes.append(("1", "All Objects", ""))
ExportModes.append(("2", "Selected Objects", ""))

from bpy.props import *


class DirectXExporter(bpy.types.Operator):
    """Export to the DirectX model format (.x)"""

    bl_idname = "export.directx"
    bl_label = "Export DirectX"

    filepath = StringProperty()
    filename = StringProperty()
    directory = StringProperty()

    #Coordinate System
    CoordinateSystem = EnumProperty(name="System", description="Select a coordinate system to export to", items=CoordinateSystems, default="1")

    #General Options
    RotateX = BoolProperty(name="Rotate X 90 Degrees", description="Rotate the entire scene 90 degrees around the X axis so Y is up", default=True)
    FlipNormals = BoolProperty(name="Flip Normals", description="", default=False)
    ApplyModifiers = BoolProperty(name="Apply Modifiers", description="Apply all object modifiers before export.", default=False)
    IncludeFrameRate = BoolProperty(name="Include Frame Rate", description="Include the AnimTicksPerSecond template which is used by some engines to control animation speed.", default=False)
    ExportTextures = BoolProperty(name="Export Textures", description="Reference external image files to be used by the model", default=True)
    ExportArmatures = BoolProperty(name="Export Armatures", description="Export the bones of any armatures to deform meshes.  Warning: This option also applies all modifiers.", default=False)
    ExportAnimation = EnumProperty(name="Animations", description="Select the type of animations to export.  Only object and armature bone animations can be exported.", items=AnimationModes, default="0")

    #Export Mode
    ExportMode = EnumProperty(name="Export", description="Select which objects to export.  Only Mesh, Empty, and Armature objects will be exported.", items=ExportModes, default="1")

    Verbose = BoolProperty(name="Verbose", description="Run the exporter in debug mode.  Check the console for output.", default=False)

    def execute(self, context):
        #Append .x if needed
        FilePath = self.properties.filepath
        if not FilePath.lower().endswith(".x"):
            FilePath += ".x"

        Config = DirectXExporterSettings(context,
                                         FilePath,
                                         CoordinateSystem=self.properties.CoordinateSystem,
                                         RotateX=self.properties.RotateX,
                                         FlipNormals=self.properties.FlipNormals,
                                         ApplyModifiers=self.properties.ApplyModifiers,
                                         IncludeFrameRate=self.properties.IncludeFrameRate,
                                         ExportTextures=self.properties.ExportTextures,
                                         ExportArmatures=self.properties.ExportArmatures,
                                         ExportAnimation=self.properties.ExportAnimation,
                                         ExportMode=self.properties.ExportMode,
                                         Verbose=self.properties.Verbose)
        ExportDirectX(Config)
        return {"FINISHED"}

    def invoke(self, context, event):
        WindowManager = context.manager
        WindowManager.add_fileselect(self)
        return {"RUNNING_MODAL"}


def menu_func(self, context):
    DefaultPath = bpy.data.filepath
    if DefaultPath.endswith(".blend"):
        DefaultPath = DefaultPath[:-6] + ".x"
    self.layout.operator(DirectXExporter.bl_idname, text="DirectX (.x)").filepath = DefaultPath


def register():
    bpy.types.register(DirectXExporter)
    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.types.unregister(DirectXExporter)
    bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()