﻿# add_mesh_bolt.py Copyright (C) 2010, Aaron Keith (Spudmn)
#
# add bolt or Nut mesh blender 2.50 Found in the TOOLS panel 
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK ***** 

bl_addon_info = {
    'name': 'Add Mesh: Bolt',
    'author': 'Aaron Keith',
    'version': '3.00',
    'blender': (2, 5, 3),
    'location': 'View3D > Tools ',
    'url': 'http://sourceforge.net/projects/boltfactory/',
    'category': 'Add Mesh'}

import os  #remove this
import bpy

try: 
    import mathutils
    MATHUTILS = mathutils
except:
    import Mathutils
    MATHUTILS = Mathutils



from math import *
from bpy.props import IntProperty, FloatProperty ,EnumProperty
from itertools import * 

NARROW_UI = 180
MAX_INPUT_NUMBER = 50

#Global_Scale = 0.001    #1 blender unit = X mm
GLOBAL_SCALE = 0.1    #1 blender unit = X mm
#Global_Scale = 1.0    #1 blender unit = X mm




# next two utility functions are stolen from import_obj.py

def unpack_list(list_of_tuples):
    l = []
    for t in list_of_tuples:
        l.extend(t)
    return l

def unpack_face_list(list_of_tuples):
    l = []
    for t in list_of_tuples:
        face = [i for i in t]

        if len(face) != 3 and len(face) != 4:
            raise RuntimeError("{0} vertices in face.".format(len(face)))
        
        # rotate indices if the 4th is 0
        if len(face) == 4 and face[3] == 0:
            face = [face[3], face[0], face[1], face[2]]

        if len(face) == 3:
            face.append(0)
            
        l.extend(face)

    return l

'''
Remove Doubles takes a list on Verts and a list of Faces and
removes the doubles, much like Blender does in edit mode.
It doesn’t have the range function  but it will round the corrdinates
and remove verts that are very close togther.  The function
is useful because you can perform a “Remove Doubles” with out
having to enter Edit Mode. Having to enter edit mode has the
disadvantage of not being able to interactively change the properties.
'''


def RemoveDoubles(verts,faces,Decimal_Places = 4):

        new_verts = []
        new_faces = []
        dict_verts = {}
        Rounded_Verts = []
        
        for v in verts:
            Rounded_Verts.append([round(v[0],Decimal_Places),round(v[1],Decimal_Places),round(v[2],Decimal_Places)])
 
        for face in faces:
            new_face = []
            for vert_index in face:
                Real_co = tuple(verts[vert_index])
                Rounded_co = tuple(Rounded_Verts[vert_index])
                                
                if Rounded_co not in dict_verts:
                    dict_verts[Rounded_co] = len(dict_verts)
                    new_verts.append(Real_co)
                if dict_verts[Rounded_co] not in new_face: 
                    new_face.append(dict_verts[Rounded_co])
            if len(new_face) == 3 or len(new_face) == 4:
                new_faces.append(new_face)

        return new_verts,new_faces 




def Scale_Mesh_Verts(verts,scale_factor):
    Ret_verts = []
    for v in verts:
        Ret_verts.append([v[0]*scale_factor,v[1]*scale_factor,v[2]*scale_factor])
    return Ret_verts





#Create a matrix representing a rotation.
#
#Parameters:
#
#        * angle (float) - The angle of rotation desired.
#        * matSize (int) - The size of the rotation matrix to construct. Can be 2d, 3d, or 4d.
#        * axisFlag (string (optional)) - Possible values:
#              o "x - x-axis rotation"
#              o "y - y-axis rotation"
#              o "z - z-axis rotation"
#              o "r - arbitrary rotation around vector"
#        * axis (Vector object. (optional)) - The arbitrary axis of rotation used with "R"
#
#Returns: Matrix object.
#    A new rotation matrix. 
def Simple_RotationMatrix(angle, matSize, axisFlag):
    if matSize != 4 :
        print ("Simple_RotationMatrix can only do 4x4")
        
    q = radians(angle)  #make the rotation go clockwise
    
    if axisFlag == 'x':
        matrix = MATHUTILS.Matrix([1,0,0,0],[0,cos(q),sin(q),0],[0,-sin(q),cos(q),0],[0,0,0,1])
    elif  axisFlag == 'y':
        matrix = MATHUTILS.Matrix([cos(q),0,-sin(q),0],[0,1,0,0],[sin(q),0,cos(q),0],[0,0,0,1])  
    elif axisFlag == 'z':
        matrix = MATHUTILS.Matrix([cos(q),sin(q),0,0],[-sin(q),cos(q),0,0],[0,0,1,0],[0,0,0,1])  
    else:
        print   ("Simple_RotationMatrix can only do x y z axis")
    return matrix


##########################################################################################
##########################################################################################
##                    Converter Functions For Bolt Factory 
##########################################################################################
##########################################################################################


def Flat_To_Radius(FLAT):
    h = (float(FLAT)/2)/cos(radians(30))
    return h

def Get_Phillips_Bit_Height(Bit_Dia):
    Flat_Width_half = (Bit_Dia*(0.5/1.82))/2.0
    Bit_Rad = Bit_Dia / 2.0
    x = Bit_Rad - Flat_Width_half
    y = tan(radians(60))*x
    return y 


##########################################################################################
##########################################################################################
##                    Miscellaneous Utilities
##########################################################################################
##########################################################################################

# Returns a list of verts rotated by the given matrix. Used by SpinDup
def Rot_Mesh(verts,matrix):
        ret = []
        #print ("rot mat",matrix)
        for v in verts:
            vec = MATHUTILS.Vector(v) * matrix
            ret.append([vec.x,vec.y,vec.z])
        return ret

# Returns a list of faces that has there index incremented by offset 
def Copy_Faces(faces,offset):        
    ret = []
    for f in faces:
        fsub = []
        for i in range(len(f)):
            fsub.append(f[i]+ offset)
        ret.append(fsub)
    return ret


# Much like Blenders built in SpinDup.
def SpinDup(VERTS,FACES,DEGREE,DIVISIONS,AXIS):
    verts=[]
    faces=[]
    
    if DIVISIONS == 0:
       DIVISIONS = 1  
  
    step = DEGREE/DIVISIONS # set step so pieces * step = degrees in arc
    
    for i in range(int(DIVISIONS)):
        rotmat = Simple_RotationMatrix(step*i, 4, AXIS) # 4x4 rotation matrix, 30d about the x axis.
        Rot = Rot_Mesh(VERTS,rotmat)
        faces.extend(Copy_Faces(FACES,len(verts)))    
        verts.extend(Rot)
    return verts,faces



# Returns a list of verts that have been moved up the z axis by DISTANCE
def Move_Verts_Up_Z(VERTS,DISTANCE):        
    ret = []
    for v in VERTS:
        ret.append([v[0],v[1],v[2]+DISTANCE])
    return ret


# Returns a list of verts and faces that has been mirrored in the AXIS 
def Mirror_Verts_Faces(VERTS,FACES,AXIS,FLIP_POINT =0):
    ret_vert = []
    ret_face = []
    offset = len(VERTS)    
    if AXIS == 'y':
        for v in VERTS:
            Delta = v[0] - FLIP_POINT
            ret_vert.append([FLIP_POINT-Delta,v[1],v[2]]) 
    if AXIS == 'x':
        for v in VERTS:
            Delta = v[1] - FLIP_POINT
            ret_vert.append([v[0],FLIP_POINT-Delta,v[2]]) 
    if AXIS == 'z':
        for v in VERTS:
            Delta = v[2] - FLIP_POINT
            ret_vert.append([v[0],v[1],FLIP_POINT-Delta]) 
            
    for f in FACES:
        fsub = []
        for i in range(len(f)):
            fsub.append(f[i]+ offset)
        fsub.reverse() # flip the order to make norm point out
        ret_face.append(fsub)
            
    return ret_vert,ret_face



# Returns a list of faces that 
# make up an array of 4 point polygon. 
def Build_Face_List_Quads(OFFSET,COLUM,ROW,FLIP = 0):
    Ret =[]
    RowStart = 0;
    for j in range(ROW):
        for i in range(COLUM):
            Res1 = RowStart + i;
            Res2 = RowStart + i + (COLUM +1)
            Res3 = RowStart + i + (COLUM +1) +1
            Res4 = RowStart+i+1
            if FLIP:
                Ret.append([OFFSET+Res1,OFFSET+Res2,OFFSET+Res3,OFFSET+Res4])
            else:
                Ret.append([OFFSET+Res4,OFFSET+Res3,OFFSET+Res2,OFFSET+Res1])
        RowStart += COLUM+1
    return Ret


# Returns a list of faces that makes up a fill pattern for a 
# circle
def Fill_Ring_Face(OFFSET,NUM,FACE_DOWN = 0):
    Ret =[]
    Face = [1,2,0]
    TempFace = [0,0,0]
    A = 0
    B = 1
    C = 2
    if NUM < 3:
        return None
    for i in range(NUM-2):
        if (i%2):
            TempFace[0] = Face[C];
            TempFace[1] = Face[C] + 1;
            TempFace[2] = Face[B];
            if FACE_DOWN:
                Ret.append([OFFSET+Face[2],OFFSET+Face[1],OFFSET+Face[0]])
            else:
                Ret.append([OFFSET+Face[0],OFFSET+Face[1],OFFSET+Face[2]])
        else:
            TempFace[0] =Face[C];
            if Face[C] == 0:
                TempFace[1] = NUM-1; 
            else:
                TempFace[1] = Face[C] - 1;
            TempFace[2] = Face[B];
            if FACE_DOWN:
                Ret.append([OFFSET+Face[0],OFFSET+Face[1],OFFSET+Face[2]])
            else:
                Ret.append([OFFSET+Face[2],OFFSET+Face[1],OFFSET+Face[0]])
        
        Face[0] = TempFace[0]
        Face[1] = TempFace[1]
        Face[2] = TempFace[2]
    return Ret
    
######################################################################################
##########################################################################################
##########################################################################################
##                    Create Allen Bit
##########################################################################################
##########################################################################################


def Allen_Fill(OFFSET,FLIP= 0):
    faces = []
    Lookup = [[19,1,0],
              [19,2,1],
              [19,3,2],
              [19,20,3],
              [20,4,3],
              [20,5,4],
              [20,6,5],
              [20,7,6],
              [20,8,7],
              [20,9,8],
              
              [20,21,9],
              
              [21,10,9],
              [21,11,10],
              [21,12,11],
              [21,13,12],
              [21,14,13],
              [21,15,14],
              
              [21,22,15],
              [22,16,15],
              [22,17,16],
              [22,18,17]
              ]
    for i in Lookup:
        if FLIP:
            faces.append([OFFSET+i[2],OFFSET+i[1],OFFSET+i[0]])
        else:
            faces.append([OFFSET+i[0],OFFSET+i[1],OFFSET+i[2]])
            
    return faces

def Allen_Bit_Dia(FLAT_DISTANCE):
    Flat_Radius = (float(FLAT_DISTANCE)/2.0)/cos(radians(30))
    return (Flat_Radius * 1.05) * 2.0
    
def Allen_Bit_Dia_To_Flat(DIA):
    Flat_Radius = (DIA/2.0)/1.05
    return (Flat_Radius * cos (radians(30)))* 2.0
    
    

def Create_Allen_Bit(FLAT_DISTANCE,HEIGHT):
    Div = 36
    verts = []
    faces = []
    
    Flat_Radius = (float(FLAT_DISTANCE)/2.0)/cos(radians(30))
    OUTTER_RADIUS = Flat_Radius * 1.05
    Outter_Radius_Height = Flat_Radius * (0.1/5.77)
    FaceStart_Outside = len(verts)
    Deg_Step = 360.0 /float(Div)
    
    for i in range(int(Div/2)+1):    # only do half and mirror later
        x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
        y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
        verts.append([x,y,0])
    
    FaceStart_Inside = len(verts)
        
    Deg_Step = 360.0 /float(6) 
    for i in range(int(6/2)+1): 
        x = sin(radians(i*Deg_Step))* Flat_Radius
        y = cos(radians(i*Deg_Step))* Flat_Radius
        verts.append([x,y,0-Outter_Radius_Height])     
     
    faces.extend(Allen_Fill(FaceStart_Outside,0))
    
    
    FaceStart_Bottom = len(verts)
    
    Deg_Step = 360.0 /float(6) 
    for i in range(int(6/2)+1): 
        x = sin(radians(i*Deg_Step))* Flat_Radius
        y = cos(radians(i*Deg_Step))* Flat_Radius
        verts.append([x,y,0-HEIGHT])     
        
    faces.extend(Build_Face_List_Quads(FaceStart_Inside,3,1,True))
    faces.extend(Fill_Ring_Face(FaceStart_Bottom,4))
    
    
    M_Verts,M_Faces = Mirror_Verts_Faces(verts,faces,'y')
    verts.extend(M_Verts)
    faces.extend(M_Faces)
    
    return verts,faces,OUTTER_RADIUS * 2.0


##########################################################################################
##########################################################################################
##                    Create Phillips Bit
##########################################################################################
##########################################################################################


def Phillips_Fill(OFFSET,FLIP= 0):
    faces = []
    Lookup = [[0,1,10],
              [1,11,10],
              [1,2,11],
              [2,12,11],
              
              [2,3,12],
              [3,4,12],
              [4,5,12],
              [5,6,12],
              [6,7,12],
              
              [7,13,12],
              [7,8,13],
              [8,14,13],
              [8,9,14],
              
              
              [10,11,16,15],
              [11,12,16],
              [12,13,16],
              [13,14,17,16],
              [15,16,17,18]
              
              
              ]
    for i in Lookup:
        if FLIP:
            if len(i) == 3:
                faces.append([OFFSET+i[2],OFFSET+i[1],OFFSET+i[0]])
            else:    
                faces.append([OFFSET+i[3],OFFSET+i[2],OFFSET+i[1],OFFSET+i[0]])
        else:
            if len(i) == 3:
                faces.append([OFFSET+i[0],OFFSET+i[1],OFFSET+i[2]])
            else:
                faces.append([OFFSET+i[0],OFFSET+i[1],OFFSET+i[2],OFFSET+i[3]])
    return faces



def Create_Phillips_Bit(FLAT_DIA,FLAT_WIDTH,HEIGHT):
    Div = 36
    verts = []
    faces = []
    
    FLAT_RADIUS = FLAT_DIA * 0.5
    OUTTER_RADIUS = FLAT_RADIUS * 1.05
    
    Flat_Half = float(FLAT_WIDTH)/2.0
        
    FaceStart_Outside = len(verts)
    Deg_Step = 360.0 /float(Div)
    for i in range(int(Div/4)+1):    # only do half and mirror later
        x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
        y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
        verts.append([x,y,0])
    
        
    FaceStart_Inside = len(verts)
    verts.append([0,FLAT_RADIUS,0]) #10
    verts.append([Flat_Half,FLAT_RADIUS,0]) #11
    verts.append([Flat_Half,Flat_Half,0])     #12
    verts.append([FLAT_RADIUS,Flat_Half,0])    #13
    verts.append([FLAT_RADIUS,0,0])            #14

 
    verts.append([0,Flat_Half,0-HEIGHT])        #15
    verts.append([Flat_Half,Flat_Half,0-HEIGHT])    #16
    verts.append([Flat_Half,0,0-HEIGHT])            #17
    
    verts.append([0,0,0-HEIGHT])            #18
    
    faces.extend(Phillips_Fill(FaceStart_Outside,True))

    Spin_Verts,Spin_Face = SpinDup(verts,faces,360,4,'z')
   
    return Spin_Verts,Spin_Face,OUTTER_RADIUS * 2
    

##########################################################################################
##########################################################################################
##                    Create Head Types
##########################################################################################
##########################################################################################

def Max_Pan_Bit_Dia(HEAD_DIA):
    HEAD_RADIUS = HEAD_DIA * 0.5
    XRad = HEAD_RADIUS * 1.976
    return (sin(radians(10))*XRad) * 2.0


def Create_Pan_Head(HOLE_DIA,HEAD_DIA,SHANK_DIA,HEIGHT,RAD1,RAD2,FACE_OFFSET):

    DIV = 36
    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5

    verts = []
    faces = []
    Row = 0
    BEVEL = HEIGHT * 0.01
    #Dome_Rad =  HEAD_RADIUS * (1.0/1.75)
    
    Dome_Rad = HEAD_RADIUS * 1.12
    RAD_Offset = HEAD_RADIUS * 0.96
    OtherRad = HEAD_RADIUS * 0.16
    OtherRad_X_Offset = HEAD_RADIUS * 0.84
    OtherRad_Z_Offset = HEAD_RADIUS * 0.504
    XRad = HEAD_RADIUS * 1.976
    ZRad = HEAD_RADIUS * 1.768
    EndRad = HEAD_RADIUS * 0.284
    EndZOffset = HEAD_RADIUS * 0.432
    HEIGHT = HEAD_RADIUS * 0.59
    
#    Dome_Rad =  5.6
#    RAD_Offset = 4.9
#    OtherRad = 0.8
#    OtherRad_X_Offset = 4.2
#    OtherRad_Z_Offset = 2.52
#    XRad = 9.88
#    ZRad = 8.84
#    EndRad = 1.42
#    EndZOffset = 2.16
#    HEIGHT = 2.95
    
    FaceStart = FACE_OFFSET

    z = cos(radians(10))*ZRad
    verts.append([HOLE_RADIUS,0.0,(0.0-ZRad)+z])
    Start_Height = 0 - ((0.0-ZRad)+z)
    Row += 1

    #for i in range(0,30,10):  was 0 to 30 more work needed to make this look good.
    for i in range(10,30,10):
        x = sin(radians(i))*XRad
        z = cos(radians(i))*ZRad
        verts.append([x,0.0,(0.0-ZRad)+z])
        Row += 1

    for i in range(20,140,10):
        x = sin(radians(i))*EndRad
        z = cos(radians(i))*EndRad
        if ((0.0 - EndZOffset)+z) < (0.0-HEIGHT):
            verts.append([(HEAD_RADIUS -EndRad)+x,0.0,0.0 - HEIGHT])
        else:
            verts.append([(HEAD_RADIUS -EndRad)+x,0.0,(0.0 - EndZOffset)+z])
        Row += 1
        
        
    verts.append([SHANK_RADIUS,0.0,(0.0-HEIGHT)])
    Row += 1
    
    verts.append([SHANK_RADIUS,0.0,(0.0-HEIGHT)-Start_Height])
    Row += 1


    sVerts,sFaces = SpinDup(verts,faces,360,DIV,'z')
    sVerts.extend(verts)        #add the start verts to the Spin verts to complete the loop
    
    faces.extend(Build_Face_List_Quads(FaceStart,Row-1,DIV))

    Global_Head_Height = HEIGHT ;

    
    return Move_Verts_Up_Z(sVerts,Start_Height),faces,HEIGHT



def Create_Dome_Head(HOLE_DIA,HEAD_DIA,SHANK_DIA,HEIGHT,RAD1,RAD2,FACE_OFFSET):
    DIV = 36
    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5
    
    verts = []
    faces = []
    Row = 0
    BEVEL = HEIGHT * 0.01
    #Dome_Rad =  HEAD_RADIUS * (1.0/1.75)
    
    Dome_Rad =  HEAD_RADIUS * 1.12
    #Head_Height = HEAD_RADIUS * 0.78
    RAD_Offset = HEAD_RADIUS * 0.98
    Dome_Height = HEAD_RADIUS * 0.64
    OtherRad = HEAD_RADIUS * 0.16
    OtherRad_X_Offset = HEAD_RADIUS * 0.84
    OtherRad_Z_Offset = HEAD_RADIUS * 0.504
    
    
#    Dome_Rad =  5.6
#    RAD_Offset = 4.9
#    Dome_Height = 3.2
#    OtherRad = 0.8
#    OtherRad_X_Offset = 4.2
#    OtherRad_Z_Offset = 2.52
#    
    
    FaceStart = FACE_OFFSET
    
    verts.append([HOLE_RADIUS,0.0,0.0])
    Row += 1


    for i in range(0,60,10):
        x = sin(radians(i))*Dome_Rad
        z = cos(radians(i))*Dome_Rad
        if ((0.0-RAD_Offset)+z) <= 0:
            verts.append([x,0.0,(0.0-RAD_Offset)+z])
            Row += 1


    for i in range(60,160,10):
        x = sin(radians(i))*OtherRad
        z = cos(radians(i))*OtherRad
        z = (0.0-OtherRad_Z_Offset)+z
        if z < (0.0-Dome_Height):
            z = (0.0-Dome_Height)
        verts.append([OtherRad_X_Offset+x,0.0,z])
        Row += 1
        
    verts.append([SHANK_RADIUS,0.0,(0.0-Dome_Height)])
    Row += 1


    sVerts,sFaces = SpinDup(verts,faces,360,DIV,'z')
    sVerts.extend(verts)        #add the start verts to the Spin verts to complete the loop
    
    faces.extend(Build_Face_List_Quads(FaceStart,Row-1,DIV))

    return sVerts,faces,Dome_Height



def Create_Cap_Head(HOLE_DIA,HEAD_DIA,SHANK_DIA,HEIGHT,RAD1,RAD2):
    DIV = 36
    
    HOLE_RADIUS = HOLE_DIA * 0.5
    HEAD_RADIUS = HEAD_DIA * 0.5
    SHANK_RADIUS = SHANK_DIA * 0.5
    
    verts = []
    faces = []
    Row = 0
    BEVEL = HEIGHT * 0.01
    
    
    FaceStart = len(verts)

    verts.append([HOLE_RADIUS,0.0,0.0])
    Row += 1

    #rad
    
    for i in range(0,100,10):
        x = sin(radians(i))*RAD1
        z = cos(radians(i))*RAD1
        verts.append([(HEAD_RADIUS-RAD1)+x,0.0,(0.0-RAD1)+z])
        Row += 1
    
    
    verts.append([HEAD_RADIUS,0.0,0.0-HEIGHT+BEVEL])
    Row += 1

    verts.append([HEAD_RADIUS-BEVEL,0.0,0.0-HEIGHT])
    Row += 1

    #rad2
   
    for i in range(0,100,10):
        x = sin(radians(i))*RAD2
        z = cos(radians(i))*RAD2
        verts.append([(SHANK_RADIUS+RAD2)-x,0.0,(0.0-HEIGHT-RAD2)+z])
        Row += 1
    

    sVerts,sFaces = SpinDup(verts,faces,360,DIV,'z')
    sVerts.extend(verts)        #add the start verts to the Spin verts to complete the loop
    

    faces.extend(Build_Face_List_Quads(FaceStart,Row-1,DIV))
    
    return sVerts,faces,HEIGHT+RAD2



def Create_Hex_Head(FLAT,HOLE_DIA,SHANK_DIA,HEIGHT):
    
    verts = []
    faces = []
    HOLE_RADIUS = HOLE_DIA * 0.5
    Half_Flat = FLAT/2
    TopBevelRadius = Half_Flat - (Half_Flat* (0.05/8))
    Undercut_Height = (Half_Flat* (0.05/8))
    Shank_Bevel = (Half_Flat* (0.05/8)) 
    Flat_Height = HEIGHT - Undercut_Height - Shank_Bevel
    #Undercut_Height = 5
    SHANK_RADIUS = SHANK_DIA/2
    Row = 0;

    verts.append([0.0,0.0,0.0])
    
    
    FaceStart = len(verts)
    #inner hole
    
    x = sin(radians(0))*HOLE_RADIUS
    y = cos(radians(0))*HOLE_RADIUS
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/6))*HOLE_RADIUS
    y = cos(radians(60/6))*HOLE_RADIUS
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/3))*HOLE_RADIUS
    y = cos(radians(60/3))*HOLE_RADIUS
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/2))*HOLE_RADIUS
    y = cos(radians(60/2))*HOLE_RADIUS
    verts.append([x,y,0.0])
    Row += 1
    
    #bevel
    
    x = sin(radians(0))*TopBevelRadius
    y = cos(radians(0))*TopBevelRadius
    vec1 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/6))*TopBevelRadius
    y = cos(radians(60/6))*TopBevelRadius
    vec2 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/3))*TopBevelRadius
    y = cos(radians(60/3))*TopBevelRadius
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/2))*TopBevelRadius
    y = cos(radians(60/2))*TopBevelRadius
    vec4 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    Row += 1
    
    #Flats
    
    x = tan(radians(0))*Half_Flat
    dvec = vec1 - MATHUTILS.Vector([x,Half_Flat,0.0])
    verts.append([x,Half_Flat,-dvec.length])
    
    
    x = tan(radians(60/6))*Half_Flat
    dvec = vec2 - MATHUTILS.Vector([x,Half_Flat,0.0])
    verts.append([x,Half_Flat,-dvec.length])
    

    x = tan(radians(60/3))*Half_Flat
    dvec = vec3 - MATHUTILS.Vector([x,Half_Flat,0.0])
    Lowest_Point = -dvec.length
    verts.append([x,Half_Flat,-dvec.length])
    

    x = tan(radians(60/2))*Half_Flat
    dvec = vec4 - MATHUTILS.Vector([x,Half_Flat,0.0])
    Lowest_Point = -dvec.length
    verts.append([x,Half_Flat,-dvec.length])
    Row += 1
    
    #down Bits Tri
    x = tan(radians(0))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    
    x = tan(radians(60/6))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])

    x = tan(radians(60/3))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    
    x = tan(radians(60/2))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    Row += 1

    #down Bits
    
    x = tan(radians(0))*Half_Flat
    verts.append([x,Half_Flat,-Flat_Height])
    
    x = tan(radians(60/6))*Half_Flat
    verts.append([x,Half_Flat,-Flat_Height])

    x = tan(radians(60/3))*Half_Flat
    verts.append([x,Half_Flat,-Flat_Height])
    
    x = tan(radians(60/2))*Half_Flat
    verts.append([x,Half_Flat,-Flat_Height])
    Row += 1
    
    
    #under cut 
       
    x = sin(radians(0))*Half_Flat
    y = cos(radians(0))*Half_Flat
    vec1 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height])
    
    x = sin(radians(60/6))*Half_Flat
    y = cos(radians(60/6))*Half_Flat
    vec2 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height])
    
    x = sin(radians(60/3))*Half_Flat
    y = cos(radians(60/3))*Half_Flat
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height])
    
    x = sin(radians(60/2))*Half_Flat
    y = cos(radians(60/2))*Half_Flat
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height])
    Row += 1
    
    #under cut down bit
    x = sin(radians(0))*Half_Flat
    y = cos(radians(0))*Half_Flat
    vec1 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    
    x = sin(radians(60/6))*Half_Flat
    y = cos(radians(60/6))*Half_Flat
    vec2 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    
    x = sin(radians(60/3))*Half_Flat
    y = cos(radians(60/3))*Half_Flat
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    
    x = sin(radians(60/2))*Half_Flat
    y = cos(radians(60/2))*Half_Flat
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    Row += 1
    
    #under cut to Shank BEVEAL
    x = sin(radians(0))*(SHANK_RADIUS+Shank_Bevel)
    y = cos(radians(0))*(SHANK_RADIUS+Shank_Bevel)
    vec1 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    
    x = sin(radians(60/6))*(SHANK_RADIUS+Shank_Bevel)
    y = cos(radians(60/6))*(SHANK_RADIUS+Shank_Bevel)
    vec2 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    
    x = sin(radians(60/3))*(SHANK_RADIUS+Shank_Bevel)
    y = cos(radians(60/3))*(SHANK_RADIUS+Shank_Bevel)
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    
    x = sin(radians(60/2))*(SHANK_RADIUS+Shank_Bevel)
    y = cos(radians(60/2))*(SHANK_RADIUS+Shank_Bevel)
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height])
    Row += 1
    
    #under cut to Shank BEVEAL
    x = sin(radians(0))*SHANK_RADIUS
    y = cos(radians(0))*SHANK_RADIUS
    vec1 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height-Shank_Bevel])
    
    x = sin(radians(60/6))*SHANK_RADIUS
    y = cos(radians(60/6))*SHANK_RADIUS
    vec2 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height-Shank_Bevel])
    
    x = sin(radians(60/3))*SHANK_RADIUS
    y = cos(radians(60/3))*SHANK_RADIUS
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height-Shank_Bevel])
    
    x = sin(radians(60/2))*SHANK_RADIUS
    y = cos(radians(60/2))*SHANK_RADIUS
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,-Flat_Height-Undercut_Height-Shank_Bevel])
    Row += 1
    
    
    #Global_Head_Height = 0 - (-HEIGHT-0.1)
    faces.extend(Build_Face_List_Quads(FaceStart,3,Row - 1))
       
    
    Mirror_Verts,Mirror_Faces = Mirror_Verts_Faces(verts,faces,'y')
    verts.extend(Mirror_Verts)
    faces.extend(Mirror_Faces)
    
    Spin_Verts,Spin_Faces = SpinDup(verts,faces,360,6,'z')
    
    
    return Spin_Verts,Spin_Faces,0 - (-HEIGHT)
   

##########################################################################################
##########################################################################################
##                    Create External Thread
##########################################################################################
##########################################################################################



def Thread_Start3(verts,INNER_RADIUS,OUTTER_RADIUS,PITCH,DIV,CREST_PERCENT,ROOT_PERCENT,Height_Offset):
    
    
    Ret_Row = 0;
    
    Half_Pitch = float(PITCH)/2
    Height_Start = Height_Offset - PITCH
    Height_Step = float(PITCH)/float(DIV)
    Deg_Step = 360.0 /float(DIV)
    
    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0
   
#theard start

    Rank = float(OUTTER_RADIUS - INNER_RADIUS)/float(DIV)
    for j in range(4):
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z])
        Height_Offset -= Crest_Height
        Ret_Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z ])
        Height_Offset -= Crest_to_Root_Height
        Ret_Row += 1
    
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            if j == 0:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
            verts.append([x,y,z ])
        Height_Offset -= Root_Height
        Ret_Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS

            if j == 0:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
            verts.append([x,y,z ])
        Height_Offset -= Root_to_Crest_Height
        Ret_Row += 1
   
    return Ret_Row,Height_Offset


def Create_Shank_Verts(START_DIA,OUTTER_DIA,LENGTH,Z_LOCATION = 0):

    verts = []
    DIV = 36
    
    START_RADIUS = START_DIA/2
    OUTTER_RADIUS = OUTTER_DIA/2
    
    Opp = abs(START_RADIUS - OUTTER_RADIUS)
    Taper_Lentgh = Opp/tan(radians(31));
    
    if Taper_Lentgh > LENGTH:
        Taper_Lentgh = 0
    
    Stright_Length = LENGTH - Taper_Lentgh
    
    Deg_Step = 360.0 /float(DIV)
    
    Row = 0
    
    Lowest_Z_Vert = 0;    
    
    Height_Offset = Z_LOCATION


        #ring
    for i in range(DIV+1): 
        x = sin(radians(i*Deg_Step))*START_RADIUS
        y = cos(radians(i*Deg_Step))*START_RADIUS
        z =  Height_Offset - 0
        verts.append([x,y,z])
        Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Height_Offset -= Stright_Length
    Row += 1

    for i in range(DIV+1): 
        x = sin(radians(i*Deg_Step))*START_RADIUS
        y = cos(radians(i*Deg_Step))*START_RADIUS
        z =  Height_Offset - 0
        verts.append([x,y,z])
        Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Height_Offset -= Taper_Lentgh
    Row += 1


    return verts,Row,Height_Offset


def Create_Thread_Start_Verts(INNER_DIA,OUTTER_DIA,PITCH,CREST_PERCENT,ROOT_PERCENT,Z_LOCATION = 0):
    
    verts = []
    DIV = 36
    
    INNER_RADIUS = INNER_DIA/2
    OUTTER_RADIUS = OUTTER_DIA/2
    
    Half_Pitch = float(PITCH)/2
    Deg_Step = 360.0 /float(DIV)
    Height_Step = float(PITCH)/float(DIV)

    Row = 0
    
    Lowest_Z_Vert = 0;    
    
    Height_Offset = Z_LOCATION
        
    Height_Start = Height_Offset 
    
    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0

    Rank = float(OUTTER_RADIUS - INNER_RADIUS)/float(DIV)
    
    Height_Offset = Z_LOCATION + PITCH 
    Cut_off = Z_LOCATION
  
    
    for j in range(1):
        
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            z = Height_Offset - (Height_Step*i)
            if z > Cut_off : z = Cut_off
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_Height
        Row += 1
    
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            z = Height_Offset - (Height_Step*i)
            if z > Cut_off : z = Cut_off
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1
        
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            z = Height_Offset - (Height_Step*i)
            if z > Cut_off : z = Cut_off 
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_Height
        Row += 1
    
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            z = Height_Offset - (Height_Step*i)
            if z > Cut_off : z = Cut_off 
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1
    
    
    for j in range(2):
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_Height
        Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z ])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1
    
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            if j == 0:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
            verts.append([x,y,z ])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_Height
        Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS

            if j == 0:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
            verts.append([x,y,z ])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1
        
   
    return verts,Row,Height_Offset



def Create_Thread_Verts(INNER_DIA,OUTTER_DIA,PITCH,HEIGHT,CREST_PERCENT,ROOT_PERCENT,Z_LOCATION = 0):
    verts = []
        
    DIV = 36
    
    INNER_RADIUS = INNER_DIA/2
    OUTTER_RADIUS = OUTTER_DIA/2
    
    Half_Pitch = float(PITCH)/2
    Deg_Step = 360.0 /float(DIV)
    Height_Step = float(PITCH)/float(DIV)

    NUM_OF_START_THREADS = 4.0
    NUM_OF_END_THREADS = 3.0
    Num = int((HEIGHT- ((NUM_OF_START_THREADS*PITCH) + (NUM_OF_END_THREADS*PITCH) ))/PITCH)
    Row = 0
    

    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0


    Height_Offset = Z_LOCATION
    
    Lowest_Z_Vert = 0;
    FaceStart = len(verts)
    
    
    for j in range(Num):
        
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            z = Height_Offset - (Height_Step*i) 
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_Height
        Row += 1
    
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            z = Height_Offset - (Height_Step*i)
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1
    
        
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            z = Height_Offset - (Height_Step*i) 
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_Height
        Row += 1
    
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            z = Height_Offset - (Height_Step*i) 
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1
    
    return verts,Row,Height_Offset



def Create_Thread_End_Verts(INNER_DIA,OUTTER_DIA,PITCH,CREST_PERCENT,ROOT_PERCENT,Z_LOCATION = 0):
    verts = []
        
    DIV = 36

    INNER_RADIUS = INNER_DIA/2
    OUTTER_RADIUS = OUTTER_DIA/2
    
    Half_Pitch = float(PITCH)/2
    Deg_Step = 360.0 /float(DIV)
    Height_Step = float(PITCH)/float(DIV)

    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0
       
    Col = 0
    Row = 0
    
    Height_Offset = Z_LOCATION 
    
    Tapper_Height_Start = Height_Offset - PITCH - PITCH 
    
    Max_Height = Tapper_Height_Start - PITCH 
    
    Lowest_Z_Vert = 0;
    
    FaceStart = len(verts)
    for j in range(4):
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i)
            z = max(z,Max_Height)
            Tapper_Radius = OUTTER_RADIUS
            if z < Tapper_Height_Start:
                Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)

            x = sin(radians(i*Deg_Step))*(Tapper_Radius)
            y = cos(radians(i*Deg_Step))*(Tapper_Radius)
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_Height
        Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i)
            z = max(z,Max_Height)
            Tapper_Radius = OUTTER_RADIUS
            if z < Tapper_Height_Start:
                Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)

            x = sin(radians(i*Deg_Step))*(Tapper_Radius)
            y = cos(radians(i*Deg_Step))*(Tapper_Radius)
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Crest_to_Root_Height
        Row += 1
    
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i)
            z = max(z,Max_Height)
            Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)
            if Tapper_Radius > INNER_RADIUS:
               Tapper_Radius = INNER_RADIUS
            
            x = sin(radians(i*Deg_Step))*(Tapper_Radius)
            y = cos(radians(i*Deg_Step))*(Tapper_Radius)
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_Height
        Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i)
            z = max(z,Max_Height)
            Tapper_Radius = OUTTER_RADIUS - (Tapper_Height_Start - z)
            if Tapper_Radius > INNER_RADIUS:
               Tapper_Radius = INNER_RADIUS
            
            x = sin(radians(i*Deg_Step))*(Tapper_Radius)
            y = cos(radians(i*Deg_Step))*(Tapper_Radius)
            verts.append([x,y,z])
            Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Height_Offset -= Root_to_Crest_Height
        Row += 1
    
    return verts,Row,Height_Offset,Lowest_Z_Vert




def Create_External_Thread(SHANK_DIA,SHANK_LENGTH,INNER_DIA,OUTTER_DIA,PITCH,LENGTH,CREST_PERCENT,ROOT_PERCENT):
    
    verts = []
    faces = []

    DIV = 36
    
    Total_Row = 0
    Thread_Len = 0;
    
    Face_Start = len(verts)
    Offset = 0.0;
    
                                             
    Shank_Verts,Shank_Row,Offset = Create_Shank_Verts(SHANK_DIA,OUTTER_DIA,SHANK_LENGTH,Offset)
    Total_Row += Shank_Row

    Thread_Start_Verts,Thread_Start_Row,Offset = Create_Thread_Start_Verts(INNER_DIA,OUTTER_DIA,PITCH,CREST_PERCENT,ROOT_PERCENT,Offset)
    Total_Row += Thread_Start_Row
    
    
    Thread_Verts,Thread_Row,Offset = Create_Thread_Verts(INNER_DIA,OUTTER_DIA,PITCH,LENGTH,CREST_PERCENT,ROOT_PERCENT,Offset)
    Total_Row += Thread_Row
    
    
    Thread_End_Verts,Thread_End_Row,Offset,Lowest_Z_Vert = Create_Thread_End_Verts(INNER_DIA,OUTTER_DIA,PITCH,CREST_PERCENT,ROOT_PERCENT,Offset )
    Total_Row += Thread_End_Row       
    
    
    verts.extend(Shank_Verts)
    verts.extend(Thread_Start_Verts)
    verts.extend(Thread_Verts)
    verts.extend(Thread_End_Verts)
    
    faces.extend(Build_Face_List_Quads(Face_Start,DIV,Total_Row -1,0))
    faces.extend(Fill_Ring_Face(len(verts)-DIV,DIV,1))
    
    return verts,faces,0.0 - Lowest_Z_Vert
 

##########################################################################################
##########################################################################################
##                    Create Nut
##########################################################################################
##########################################################################################

def add_Hex_Nut(FLAT,HOLE_DIA,HEIGHT):
    global Global_Head_Height
    global Global_NutRad
    
    verts = []
    faces = []
    HOLE_RADIUS = HOLE_DIA * 0.5
    Half_Flat = FLAT/2
    Half_Height = HEIGHT/2
    TopBevelRadius = Half_Flat - 0.05
    
    Global_NutRad =  TopBevelRadius
    
    Row = 0;
    Lowest_Z_Vert = 0.0;

    verts.append([0.0,0.0,0.0])
    
    
    FaceStart = len(verts)
    #inner hole
    
    x = sin(radians(0))*HOLE_RADIUS
    y = cos(radians(0))*HOLE_RADIUS
    #print ("rad 0 x;",  x,  "y:" ,y )
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/6))*HOLE_RADIUS
    y = cos(radians(60/6))*HOLE_RADIUS
    #print ("rad 60/6x;",  x,  "y:" ,y )
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/3))*HOLE_RADIUS
    y = cos(radians(60/3))*HOLE_RADIUS
    #print ("rad 60/3x;",  x,  "y:" ,y )
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/2))*HOLE_RADIUS
    y = cos(radians(60/2))*HOLE_RADIUS
    #print ("rad 60/2x;",  x,  "y:" ,y )
    verts.append([x,y,0.0])
    Row += 1
    
    
    #bevel
    
    x = sin(radians(0))*TopBevelRadius
    y = cos(radians(0))*TopBevelRadius
    vec1 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/6))*TopBevelRadius
    y = cos(radians(60/6))*TopBevelRadius
    vec2 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/3))*TopBevelRadius
    y = cos(radians(60/3))*TopBevelRadius
    vec3 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    
    
    x = sin(radians(60/2))*TopBevelRadius
    y = cos(radians(60/2))*TopBevelRadius
    vec4 = MATHUTILS.Vector([x,y,0.0])
    verts.append([x,y,0.0])
    Row += 1
    
    #Flats
    
    x = tan(radians(0))*Half_Flat
    dvec = vec1 - MATHUTILS.Vector([x,Half_Flat,0.0])
    verts.append([x,Half_Flat,-dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert,-dvec.length)
    
    
    x = tan(radians(60/6))*Half_Flat
    dvec = vec2 - MATHUTILS.Vector([x,Half_Flat,0.0])
    verts.append([x,Half_Flat,-dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert,-dvec.length)
    

    x = tan(radians(60/3))*Half_Flat
    dvec = vec3 - MATHUTILS.Vector([x,Half_Flat,0.0])
    Lowest_Point = -dvec.length
    verts.append([x,Half_Flat,-dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert,-dvec.length)

    x = tan(radians(60/2))*Half_Flat
    dvec = vec4 - MATHUTILS.Vector([x,Half_Flat,0.0])
    Lowest_Point = -dvec.length
    verts.append([x,Half_Flat,-dvec.length])
    Lowest_Z_Vert = min(Lowest_Z_Vert,-dvec.length)
    Row += 1
    
    #down Bits Tri
    x = tan(radians(0))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    
    
    x = tan(radians(60/6))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    x = tan(radians(60/3))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    
    x = tan(radians(60/2))*Half_Flat
    verts.append([x,Half_Flat,Lowest_Point])
    Lowest_Z_Vert = min(Lowest_Z_Vert,Lowest_Point)
    Row += 1

    #down Bits
    
    x = tan(radians(0))*Half_Flat
    verts.append([x,Half_Flat,-Half_Height])
    
    x = tan(radians(60/6))*Half_Flat
    verts.append([x,Half_Flat,-Half_Height])

    x = tan(radians(60/3))*Half_Flat
    verts.append([x,Half_Flat,-Half_Height])
    
    x = tan(radians(60/2))*Half_Flat
    verts.append([x,Half_Flat,-Half_Height])
    Lowest_Z_Vert = min(Lowest_Z_Vert,-Half_Height)
    Row += 1
    
    faces.extend(Build_Face_List_Quads(FaceStart,3,Row - 1))

    Global_Head_Height = HEIGHT
    
    Tvert,tface = Mirror_Verts_Faces(verts,faces,'z',Lowest_Z_Vert)
    verts.extend(Tvert)
    faces.extend(tface)
           
    
    Tvert,tface = Mirror_Verts_Faces(verts,faces,'y')
    verts.extend(Tvert)
    faces.extend(tface)
    
    S_verts,S_faces = SpinDup(verts,faces,360,6,'z')
    
    #return verts,faces,TopBevelRadius
    return S_verts,S_faces,TopBevelRadius



def add_Nylon_Head(OUTSIDE_RADIUS,Z_LOCATION = 0):
    DIV = 36
    verts = []
    faces = []
    Row = 0

    INNER_HOLE = OUTSIDE_RADIUS - (OUTSIDE_RADIUS * (1.25/4.75))
    EDGE_THICKNESS = (OUTSIDE_RADIUS * (0.4/4.75))
    RAD1 = (OUTSIDE_RADIUS * (0.5/4.75))
    OVER_ALL_HEIGTH = (OUTSIDE_RADIUS * (2.0/4.75))
    
    
    FaceStart = len(verts)

    Start_Height = 0 - 3
    Height_Offset = Z_LOCATION
    Lowest_Z_Vert = 0
    
    x = INNER_HOLE
    z = (Height_Offset - OVER_ALL_HEIGTH) + EDGE_THICKNESS
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1
    
    x = INNER_HOLE
    z = (Height_Offset - OVER_ALL_HEIGTH)
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1
    
    
    for i in range(180,80,-10):
        x = sin(radians(i))*RAD1
        z = cos(radians(i))*RAD1
        verts.append([(OUTSIDE_RADIUS-RAD1)+x,0.0,((Height_Offset - OVER_ALL_HEIGTH)+RAD1)+z])
        Lowest_Z_Vert = min(Lowest_Z_Vert,z)
        Row += 1
    
    
    x = OUTSIDE_RADIUS - 0
    z = Height_Offset 
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1

    sVerts,sFaces = SpinDup(verts,faces,360,DIV,'z')
    sVerts.extend(verts)        #add the start verts to the Spin verts to complete the loop
    
    faces.extend(Build_Face_List_Quads(FaceStart,Row-1,DIV,1))

    return Move_Verts_Up_Z(sVerts,0),faces,Lowest_Z_Vert



def add_Nylon_Part(OUTSIDE_RADIUS,Z_LOCATION = 0):
    DIV = 36
    verts = []
    faces = []
    Row = 0

    INNER_HOLE = OUTSIDE_RADIUS - (OUTSIDE_RADIUS * (1.5/4.75))
    EDGE_THICKNESS = (OUTSIDE_RADIUS * (0.4/4.75))
    RAD1 = (OUTSIDE_RADIUS * (0.5/4.75))
    OVER_ALL_HEIGTH = (OUTSIDE_RADIUS * (2.0/4.75))
    PART_THICKNESS = OVER_ALL_HEIGTH - EDGE_THICKNESS
    PART_INNER_HOLE = (OUTSIDE_RADIUS * (2.5/4.75))
    
    FaceStart = len(verts)

    Start_Height = 0 - 3
    Height_Offset = Z_LOCATION
    Lowest_Z_Vert = 0
    

    x = INNER_HOLE + EDGE_THICKNESS
    z = Height_Offset 
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1
    
    x = PART_INNER_HOLE
    z = Height_Offset
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1
    
    x = PART_INNER_HOLE
    z = Height_Offset - PART_THICKNESS
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1
    
    x = INNER_HOLE + EDGE_THICKNESS
    z = Height_Offset - PART_THICKNESS
    verts.append([x,0.0,z])
    Lowest_Z_Vert = min(Lowest_Z_Vert,z)
    Row += 1


    sVerts,sFaces = SpinDup(verts,faces,360,DIV,'z')
    sVerts.extend(verts)  #add the start verts to the Spin verts to complete the loop
    
    faces.extend(Build_Face_List_Quads(FaceStart,Row-1,DIV,1))

    return sVerts,faces,0 - Lowest_Z_Vert


##########################################################################################
##########################################################################################
##                    Create Internal Thread
##########################################################################################
##########################################################################################


def Create_Internal_Thread_Start_Verts(verts,INNER_RADIUS,OUTTER_RADIUS,PITCH,DIV,CREST_PERCENT,ROOT_PERCENT,Height_Offset):
    
    
    Ret_Row = 0;
    
    Height_Offset = Height_Offset + PITCH  #Move the offset up so that the verts start at 
                                           #at the correct place  (Height_Start)
    
    Half_Pitch = float(PITCH)/2
    Height_Start = Height_Offset - PITCH 
    Height_Step = float(PITCH)/float(DIV)
    Deg_Step = 360.0 /float(DIV)
    
    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0
    

    Rank = float(OUTTER_RADIUS - INNER_RADIUS)/float(DIV)
    for j in range(1):
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z])
        Height_Offset -= Crest_Height
        Ret_Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z ])
        Height_Offset -= Crest_to_Root_Height
        Ret_Row += 1
    
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            if j == 0:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
            verts.append([x,y,z ])
        Height_Offset -= Root_Height
        Ret_Row += 1
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z > Height_Start:
                z = Height_Start
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS

            if j == 0:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS - (i*Rank))
            verts.append([x,y,z ])
        Height_Offset -= Root_to_Crest_Height
        Ret_Row += 1
   
    return Ret_Row,Height_Offset


def Create_Internal_Thread_End_Verts(verts,INNER_RADIUS,OUTTER_RADIUS,PITCH,DIV,CREST_PERCENT,ROOT_PERCENT,Height_Offset):
    
    
    Ret_Row = 0;
    
    Half_Pitch = float(PITCH)/2
    #Height_End = Height_Offset - PITCH - PITCH - PITCH- PITCH - PITCH- PITCH
    Height_End = Height_Offset - PITCH 
    #Height_End = -2.1
    Height_Step = float(PITCH)/float(DIV)
    Deg_Step = 360.0 /float(DIV)
    
    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0
    

    Rank = float(OUTTER_RADIUS - INNER_RADIUS)/float(DIV)
    
    Num = 0
    
    for j in range(2):
        
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z < Height_End:
                z = Height_End
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z])
        Height_Offset -= Crest_Height
        Ret_Row += 1
    
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z < Height_End:
                z = Height_End
            
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,z ])
        Height_Offset -= Crest_to_Root_Height
        Ret_Row += 1
    
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z < Height_End:
                z = Height_End
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            if j == Num:
                x = sin(radians(i*Deg_Step))*(INNER_RADIUS + (i*Rank))
                y = cos(radians(i*Deg_Step))*(INNER_RADIUS + (i*Rank))
            if j > Num:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS)
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS )
                
            verts.append([x,y,z ])
        Height_Offset -= Root_Height
        Ret_Row += 1
    
    
        for i in range(DIV+1):
            z = Height_Offset - (Height_Step*i) 
            if z < Height_End:
                z = Height_End
            
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS

            if j == Num:
                x = sin(radians(i*Deg_Step))*(INNER_RADIUS + (i*Rank))
                y = cos(radians(i*Deg_Step))*(INNER_RADIUS + (i*Rank))
            if j > Num:
                x = sin(radians(i*Deg_Step))*(OUTTER_RADIUS )
                y = cos(radians(i*Deg_Step))*(OUTTER_RADIUS )
                
            verts.append([x,y,z ])
        Height_Offset -= Root_to_Crest_Height
        Ret_Row += 1

       
    return Ret_Row,Height_End  # send back Height End as this is the lowest point


def Create_Internal_Thread(INNER_DIA,OUTTER_DIA,PITCH,HEIGHT,CREST_PERCENT,ROOT_PERCENT,INTERNAL = 1):
    verts = []
    faces = []
    
    DIV = 36
    
    INNER_RADIUS = INNER_DIA/2
    OUTTER_RADIUS = OUTTER_DIA/2
    
    Half_Pitch = float(PITCH)/2
    Deg_Step = 360.0 /float(DIV)
    Height_Step = float(PITCH)/float(DIV)
            
    Num = int(round((HEIGHT- PITCH)/PITCH))  # less one pitch for the start and end that is 1/2 pitch high    
    
    Col = 0
    Row = 0
    
    
    Crest_Height = float(PITCH) * float(CREST_PERCENT)/float(100)
    Root_Height = float(PITCH) * float(ROOT_PERCENT)/float(100)
    Root_to_Crest_Height = Crest_to_Root_Height = (float(PITCH) - (Crest_Height + Root_Height))/2.0
    
    Height_Offset = 0
    FaceStart = len(verts)
    
    Row_Inc,Height_Offset = Create_Internal_Thread_Start_Verts(verts,INNER_RADIUS,OUTTER_RADIUS,PITCH,DIV,CREST_PERCENT,ROOT_PERCENT,Height_Offset)
    Row += Row_Inc
    
    for j in range(Num):
        
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,Height_Offset - (Height_Step*i) ])
        Height_Offset -= Crest_Height
        Row += 1
    
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*OUTTER_RADIUS
            y = cos(radians(i*Deg_Step))*OUTTER_RADIUS
            verts.append([x,y,Height_Offset - (Height_Step*i) ])
        Height_Offset -= Crest_to_Root_Height
        Row += 1
        
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            verts.append([x,y,Height_Offset - (Height_Step*i) ])
        Height_Offset -= Root_Height
        Row += 1
    
        for i in range(DIV+1):
            x = sin(radians(i*Deg_Step))*INNER_RADIUS
            y = cos(radians(i*Deg_Step))*INNER_RADIUS
            verts.append([x,y,Height_Offset - (Height_Step*i) ])
        Height_Offset -= Root_to_Crest_Height
        Row += 1
    

    Row_Inc,Height_Offset = Create_Internal_Thread_End_Verts(verts,INNER_RADIUS,OUTTER_RADIUS,PITCH,DIV,CREST_PERCENT,ROOT_PERCENT,Height_Offset)
    Row += Row_Inc
    
    faces.extend(Build_Face_List_Quads(FaceStart,DIV,Row -1,INTERNAL))
    
    return verts,faces,0 - Height_Offset


def Nut_Mesh(context):

    verts = []
    faces = []
    Head_Verts = []
    Head_Faces= []
    sc = context.scene

    New_Nut_Height = 5
    
    Face_Start = len(verts)
    Thread_Verts,Thread_Faces,New_Nut_Height = Create_Internal_Thread(sc.bf_Minor_Dia,sc.bf_Major_Dia,sc.bf_Pitch,sc.bf_Hex_Nut_Height,sc.bf_Crest_Percent,sc.bf_Root_Percent,1)
    verts.extend(Thread_Verts)
    faces.extend(Copy_Faces(Thread_Faces,Face_Start))
    
    Face_Start = len(verts)
    Head_Verts,Head_Faces,Lock_Nut_Rad = add_Hex_Nut(sc.bf_Hex_Nut_Flat_Distance,sc.bf_Major_Dia,New_Nut_Height)
    verts.extend((Head_Verts))
    faces.extend(Copy_Faces(Head_Faces,Face_Start))
    
    LowZ = 0 - New_Nut_Height
    
    if sc.bf_Nut_Type == 'bf_Nut_Lock':
        Face_Start = len(verts)
        Nylon_Head_Verts,Nylon_Head_faces,LowZ = add_Nylon_Head(Lock_Nut_Rad,0-New_Nut_Height)    
        verts.extend((Nylon_Head_Verts))
        faces.extend(Copy_Faces(Nylon_Head_faces,Face_Start))
    
        Face_Start = len(verts)
        Nylon_Verts,Nylon_faces,Temp_LowZ = add_Nylon_Part(Lock_Nut_Rad,0-New_Nut_Height)    
        verts.extend((Nylon_Verts))
        faces.extend(Copy_Faces(Nylon_faces,Face_Start))
    

    return Move_Verts_Up_Z(verts,0 - LowZ),faces



##########################################################################################
##########################################################################################
##########################################################################################
##                    Create Bolt
##########################################################################################
##########################################################################################



def Bolt_Mesh(context):
    
    
    verts = []
    faces = []
    Bit_Verts = []
    Bit_Faces = []
    Bit_Dia = 0.001
    Head_Verts = []
    Head_Faces= []
    Head_Height = 0.0
    sc = context.scene

    ReSized_Allen_Bit_Flat_Distance = sc.bf_Allen_Bit_Flat_Distance   # set default  
   
    
    Head_Height = sc.bf_Hex_Head_Height # will be changed by the Head Functions
    
    
    if sc.bf_Bit_Type == 'bf_Bit_Allen' and sc.bf_Head_Type == 'bf_Head_Pan':
        #need to size Allen bit if it is too big.
        if  Allen_Bit_Dia(sc.bf_Allen_Bit_Flat_Distance) > Max_Pan_Bit_Dia(sc.bf_Pan_Head_Dia):
            ReSized_Allen_Bit_Flat_Distance = Allen_Bit_Dia_To_Flat(Max_Pan_Bit_Dia(sc.bf_Pan_Head_Dia)) * 1.05
            print ("Resized Allen Bit Flat Distance to ",ReSized_Allen_Bit_Flat_Distance) 
 
    #bit Mesh
    if sc.bf_Bit_Type == 'bf_Bit_Allen':
        Bit_Verts,Bit_Faces,Bit_Dia = Create_Allen_Bit(ReSized_Allen_Bit_Flat_Distance,sc.bf_Allen_Bit_Depth)
    
    if sc.bf_Bit_Type == 'bf_Bit_Philips':
        Bit_Verts,Bit_Faces,Bit_Dia = Create_Phillips_Bit(sc.bf_Philips_Bit_Dia,sc.bf_Philips_Bit_Dia*(0.5/1.82),sc.bf_Phillips_Bit_Depth)
   
        
    #Head Mesh
    
    if sc.bf_Head_Type =='bf_Head_Hex':  
        Head_Verts,Head_Faces,Head_Height = Create_Hex_Head(sc.bf_Hex_Head_Flat_Distance,Bit_Dia,sc.bf_Shank_Dia,sc.bf_Hex_Head_Height)

    elif sc.bf_Head_Type == 'bf_Head_Cap':  
        Head_Verts,Head_Faces,Head_Height = Create_Cap_Head(Bit_Dia,sc.bf_Cap_Head_Dia,sc.bf_Shank_Dia,sc.bf_Cap_Head_Height,sc.bf_Cap_Head_Dia*(1.0/19.0),sc.bf_Cap_Head_Dia*(1.0/19.0))
        
    elif sc.bf_Head_Type =='bf_Head_Dome':  
        Head_Verts,Head_Faces,Head_Height = Create_Dome_Head(Bit_Dia,sc.bf_Dome_Head_Dia,sc.bf_Shank_Dia,sc.bf_Hex_Head_Height,1,1,0)
    
    elif sc.bf_Head_Type == 'bf_Head_Pan':  
        Head_Verts,Head_Faces,Head_Height = Create_Pan_Head(Bit_Dia,sc.bf_Pan_Head_Dia,sc.bf_Shank_Dia,sc.bf_Hex_Head_Height,1,1,0)


    Face_Start = len(verts)
    verts.extend(Move_Verts_Up_Z(Bit_Verts,Head_Height))
    faces.extend(Copy_Faces(Bit_Faces,Face_Start))

    Face_Start = len(verts)
    verts.extend(Move_Verts_Up_Z(Head_Verts,Head_Height))
    faces.extend(Copy_Faces(Head_Faces,Face_Start))

    Face_Start = len(verts)
    Thread_Verts,Thread_Faces,Thread_Height = Create_External_Thread(sc.bf_Shank_Dia,sc.bf_Shank_Length,sc.bf_Minor_Dia,sc.bf_Major_Dia,sc.bf_Pitch,sc.bf_Thread_Length,sc.bf_Crest_Percent,sc.bf_Root_Percent)

    verts.extend(Move_Verts_Up_Z(Thread_Verts,00))
    faces.extend(Copy_Faces(Thread_Faces,Face_Start))
    
    return Move_Verts_Up_Z(verts,Thread_Height),faces


#####################################################################################3

def Load_Preset(context):
    Nothing = 1
    sc = context.scene

    if sc.bf_Preset_Menu == 'bf_Preset_M3':
 
        sc.bf_Shank_Dia = 3.0
        #sc.bf_Pitch = 0.5    #Coarse
        sc.bf_Pitch = 0.35  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10 
        sc.bf_Major_Dia = 3.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 5.5
        sc.bf_Hex_Head_Height = 2.0
        sc.bf_Cap_Head_Dia = 5.5
        sc.bf_Cap_Head_Height = 3.0
        sc.bf_Allen_Bit_Flat_Distance = 2.5
        sc.bf_Allen_Bit_Depth = 1.5
        sc.bf_Pan_Head_Dia = 5.6
        sc.bf_Dome_Head_Dia = 5.6
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 2.4
        sc.bf_Hex_Nut_Flat_Distance = 5.5
        sc.bf_Thread_Length = 6
        sc.bf_Shank_Length = 0.0
        
    
    elif sc.bf_Preset_Menu == 'bf_Preset_M4' : #M4
        sc.bf_Shank_Dia = 4.0
        #sc.bf_Pitch = 0.7    #Coarse
        sc.bf_Pitch = 0.5  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10 
        sc.bf_Major_Dia = 4.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 7.0
        sc.bf_Hex_Head_Height = 2.8
        sc.bf_Cap_Head_Dia = 7.0
        sc.bf_Cap_Head_Height = 4.0
        sc.bf_Allen_Bit_Flat_Distance = 3.0
        sc.bf_Allen_Bit_Depth = 2.0
        sc.bf_Pan_Head_Dia = 8.0
        sc.bf_Dome_Head_Dia = 8.0
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 3.2
        sc.bf_Hex_Nut_Flat_Distance = 7.0
        sc.bf_Thread_Length = 8
        sc.bf_Shank_Length = 0.0
        
        
    elif sc.bf_Preset_Menu == 'bf_Preset_M5' : #M5
        sc.bf_Shank_Dia = 5.0
        #sc.bf_Pitch = 0.8 #Coarse
        sc.bf_Pitch = 0.5  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10 
        sc.bf_Major_Dia = 5.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 8.0
        sc.bf_Hex_Head_Height = 3.5
        sc.bf_Cap_Head_Dia = 8.5
        sc.bf_Cap_Head_Height = 5.0
        sc.bf_Allen_Bit_Flat_Distance = 4.0
        sc.bf_Allen_Bit_Depth = 2.5
        sc.bf_Pan_Head_Dia = 9.5
        sc.bf_Dome_Head_Dia = 9.5
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 4.0
        sc.bf_Hex_Nut_Flat_Distance = 8.0
        sc.bf_Thread_Length = 10
        sc.bf_Shank_Length = 0.0
        
        
    if sc.bf_Preset_Menu == 'bf_Preset_M6' : #M6
        sc.bf_Shank_Dia = 6.0
        #bf_Pitch = 1.0 #Coarse
        sc.bf_Pitch = 0.75  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10
        sc.bf_Major_Dia = 6.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 10.0
        sc.bf_Hex_Head_Height = 4.0
        sc.bf_Cap_Head_Dia = 10.0
        sc.bf_Cap_Head_Height = 6.0
        sc.bf_Allen_Bit_Flat_Distance = 5.0
        sc.bf_Allen_Bit_Depth = 3.0
        sc.bf_Pan_Head_Dia = 12.0
        sc.bf_Dome_Head_Dia = 12.0
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 5.0
        sc.bf_Hex_Nut_Flat_Distance = 10.0
        sc.bf_Thread_Length = 12
        sc.bf_Shank_Length = 0.0
        
        
    if sc.bf_Preset_Menu == 'bf_Preset_M8' : #M8
        sc.bf_Shank_Dia = 8.0
        #sc.bf_Pitch = 1.25 #Coarse
        sc.bf_Pitch = 1.00  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10
        sc.bf_Major_Dia = 8.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 13.0
        sc.bf_Hex_Head_Height = 5.3
        sc.bf_Cap_Head_Dia = 13.5
        sc.bf_Cap_Head_Height = 8.0
        sc.bf_Allen_Bit_Flat_Distance = 6.0
        sc.bf_Allen_Bit_Depth = 4.0
        sc.bf_Pan_Head_Dia = 16.0
        sc.bf_Dome_Head_Dia = 16.0
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 6.5
        sc.bf_Hex_Nut_Flat_Distance = 13.0
        sc.bf_Thread_Length = 16
        sc.bf_Shank_Length = 0.0
    
    if sc.bf_Preset_Menu == 'bf_Preset_M10' : #M10
        sc.bf_Shank_Dia = 10.0
        #sc.bf_Pitch = 1.5 #Coarse
        sc.bf_Pitch = 1.25  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10
        sc.bf_Major_Dia = 10.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 17.0
        sc.bf_Hex_Head_Height = 6.4
        sc.bf_Cap_Head_Dia = 16.0
        sc.bf_Cap_Head_Height = 10.0
        sc.bf_Allen_Bit_Flat_Distance = 8.0
        sc.bf_Allen_Bit_Depth = 5.0
        sc.bf_Pan_Head_Dia = 20.0
        sc.bf_Dome_Head_Dia = 20.0
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 8.0
        sc.bf_Hex_Nut_Flat_Distance = 17.0
        sc.bf_Thread_Length = 20
        sc.bf_Shank_Length = 0.0
    
    
    if sc.bf_Preset_Menu == 'bf_Preset_M12' : #M12
        #sc.bf_Pitch = 1.75 #Coarse
        sc.bf_Pitch = 1.50  #Fine
        sc.bf_Crest_Percent = 10
        sc.bf_Root_Percent = 10
        sc.bf_Major_Dia = 12.0
        sc.bf_Minor_Dia = sc.bf_Major_Dia - (1.082532 * sc.bf_Pitch)
        sc.bf_Hex_Head_Flat_Distance = 19.0
        sc.bf_Hex_Head_Height = 7.5
        sc.bf_Cap_Head_Dia = 18.5
        sc.bf_Cap_Head_Height = 12.0
        sc.bf_Allen_Bit_Flat_Distance = 10.0
        sc.bf_Allen_Bit_Depth = 6.0
        sc.bf_Pan_Head_Dia = 24.0
        sc.bf_Dome_Head_Dia = 24.0
        sc.bf_Philips_Bit_Dia = sc.bf_Pan_Head_Dia*(1.82/5.6)
        sc.bf_Phillips_Bit_Depth = Get_Phillips_Bit_Height(sc.bf_Philips_Bit_Dia)
        sc.bf_Hex_Nut_Height = 10.0
        sc.bf_Hex_Nut_Flat_Distance = 19.0
        sc.bf_Shank_Dia = 12.0
        sc.bf_Shank_Length = 33.0
        sc.bf_Thread_Length = 32.0




def Create_Propertys():
    #Model Types
    Model_Type_List = [('bf_Model_Bolt','BOLT','Bolt Model'),('bf_Model_Nut','NUT','Nut Model')]
    bpy.types.Scene.EnumProperty( attr='bf_Model_Type',
            name='Model',
            description='Choose the type off model you would like',
            items = Model_Type_List, default = 'bf_Model_Bolt')

    #Head Types
    Model_Type_List = [('bf_Head_Hex','HEX','Hex Head'),('bf_Head_Cap','CAP','Cap Head'),('bf_Head_Dome','DOME','Dome Head'),('bf_Head_Pan','PAN','Pan Head')]
    bpy.types.Scene.EnumProperty( attr='bf_Head_Type',
            name='Head',
            description='Choose the type off Head you would like',
            items = Model_Type_List, default = 'bf_Head_Hex')

    
        #Bit Types
    Bit_Type_List = [('bf_Bit_None','NONE','No Bit Type'),('bf_Bit_Allen','ALLEN','Allen Bit Type'),('bf_Bit_Philips','PHILLIPS','Phillips Bit Type')]
    bpy.types.Scene.EnumProperty( attr='bf_Bit_Type',
            name='Bit Type',
            description='Choose the type of bit to you would like',
            items = Bit_Type_List, default = 'bf_Bit_None')


    #Nut Types
    Nut_Type_List = [('bf_Nut_Hex','HEX','Hex Nut'),('bf_Nut_Lock','LOCK','Lock Nut')]
    bpy.types.Scene.EnumProperty( attr='bf_Nut_Type',
            name='Nut Type',
            description='Choose the type of nut you would like',
            items = Nut_Type_List, default = 'bf_Nut_Hex')
    
    
    Preset_List = [('bf_Preset_M3','M3','M3'),('bf_Preset_M4','M4','M4'),('bf_Preset_M5','M5','M5'),('bf_Preset_M6','M6','M6'),('bf_Preset_M8','M8','M8'),('bf_Preset_M10','M10','M10'),('bf_Preset_M12','M12','M12')]
    bpy.types.Scene.EnumProperty( attr='bf_Preset_Menu',
            name='Presets',
            description='Choose a screw type and Click Apply',
            items = Preset_List, default = 'bf_Preset_M3')

    #Shank Types    
    bpy.types.Scene.FloatProperty( attr='bf_Shank_Length',
            name='Shank Length',
            min = 0,max = MAX_INPUT_NUMBER, 
            description='Length of the unthreaded shank'
            )
    
    bpy.types.Scene.FloatProperty( attr='bf_Shank_Dia',
            name='Shank Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the shank'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Phillips_Bit_Depth',
            name='Bit Depth',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Depth of the Phillips Bit'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Philips_Bit_Dia',
            name='Bit Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the Philips Bit'
            )
    
    bpy.types.Scene.FloatProperty( attr='bf_Allen_Bit_Depth',
            name='Bit Depth',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Depth of the Allen Bit'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Allen_Bit_Flat_Distance',
            name='Flat Dist',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Flat Distance of the Allen Bit'
            )
    
    bpy.types.Scene.FloatProperty( attr='bf_Hex_Head_Height',
            name='Head Height',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Height of the Hex Head'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Hex_Head_Flat_Distance',
            name='Flat Dist',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Flat Distance of the Hex Head'
            )


    bpy.types.Scene.FloatProperty( attr='bf_Cap_Head_Dia',
            name='Head Height',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the Cap Head'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Cap_Head_Height',
            name='Head Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Height of the Cap Head'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Dome_Head_Dia',
            name='Dome Head Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Length of the unthreaded shank'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Pan_Head_Dia',
            name='Pan Head Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the Pan Head'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Thread_Length',
            name='Thread Length',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Length of the Thread'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Major_Dia',
            name='Major Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Outside diameter of the Thread'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Minor_Dia',
            name='Minor Dia',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Inside diameter of the Thread'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Pitch',
            name='Pitch',
            min = 0.1,max = 7.0,
            description='Pitch if the thread'
            )
    
    bpy.types.Scene.IntProperty( attr='bf_Crest_Percent',
            name='Crest Percent',
            min = 1,max = 90,
            description='Percent of the pitch that makes up the Crest'
            )

    bpy.types.Scene.IntProperty( attr='bf_Root_Percent',
            name='Root Percent',
            min = 1,max = 90,
            description='Percent of the pitch that makes up the Root'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Hex_Nut_Height',
            name='Hex Nut Height',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Height of the Hex Nut'
            )

    bpy.types.Scene.FloatProperty( attr='bf_Hex_Nut_Flat_Distance',
            name='Hex Nut Flat Dist',
            min = 0,max = MAX_INPUT_NUMBER,
            description='Flat distance of the Hex Nut'
            )    

def Create_Tab(layout,context,Title,EnumProp,ExpandTab=True): # X1,Y1 = Top Left X2,Y2 = Bottom Right

    #layout.separator()
    row = layout.row()
    row.label(text=Title)
    layout.prop(context,EnumProp, expand=ExpandTab)
    


def Dispaly_Shank_Tab(layout,context):
    #layout.separator()
    row = layout.row()
    row.label(text="Shank")

    row = layout.row()
    layout.prop(context,'bf_Shank_Length')
    layout.prop(context,'bf_Shank_Dia')
    
    
def Dispaly_Head_Tab(layout,context):  
    
    Create_Tab(layout,context,'Head Type','bf_Head_Type')

#    layout.separator()
#    row = layout.row()
#    
    if context.bf_Head_Type == 'bf_Head_Hex':
        row = layout.row()
        layout.prop(context,'bf_Hex_Head_Height')
        layout.prop(context,'bf_Hex_Head_Flat_Distance')
    
    elif context.bf_Head_Type == 'bf_Head_Cap':
        row = layout.row()
        layout.prop(context,'bf_Cap_Head_Height')
        layout.prop(context,'bf_Cap_Head_Dia')

    elif context.bf_Head_Type == 'bf_Head_Dome':
        row = layout.row()
        layout.prop(context,'bf_Dome_Head_Dia')
    
    elif context.bf_Head_Type == 'bf_Head_Pan':
        row = layout.row()
        layout.prop(context,'bf_Pan_Head_Dia')
        

def Dispaly_Bit_Tab(layout,context):  
    
    Create_Tab(layout,context,'Bit Type','bf_Bit_Type')
    
    if context.bf_Bit_Type == 'bf_Bit_None':
        DoNothing = 1;
        
    elif context.bf_Bit_Type == 'bf_Bit_Allen':
         row = layout.row()
         layout.prop(context,'bf_Allen_Bit_Depth')
         layout.prop(context,'bf_Allen_Bit_Flat_Distance')
    
    elif context.bf_Bit_Type == 'bf_Bit_Philips':
        row = layout.row()
        layout.prop(context,'bf_Phillips_Bit_Depth')
        layout.prop(context,'bf_Philips_Bit_Dia')
    
    
    
def Dispaly_Bolt_Tab(layout,context):    
       
   Dispaly_Bit_Tab(layout,context)
   Dispaly_Head_Tab(layout,context)
   Dispaly_Shank_Tab(layout,context)

def Dispaly_Thread_Tab(layout,context):  
    
#    Create_Tab(3,Y_POS,CONTROL_WIDTH,Y_POS-CONTROL_HEIGHT,"Thread",0)
    #layout.separator()
    row = layout.row()
    row.label(text="Thread")
    
    if context.bf_Model_Type == 'bf_Model_Bolt':
        layout.prop(context,'bf_Thread_Length')
  
    layout.prop(context,'bf_Major_Dia')
    layout.prop(context,'bf_Minor_Dia')
    layout.prop(context,'bf_Pitch')
    layout.prop(context,'bf_Crest_Percent')
    layout.prop(context,'bf_Root_Percent')
  

def Dispaly_Nut_Tab(layout,context):  
   
    Create_Tab(layout,context,'Nut Type','bf_Nut_Type')
    layout.prop(context,'bf_Hex_Nut_Height')
    layout.prop(context,'bf_Hex_Nut_Flat_Distance')
        

def Dispaly_Preset_Tab(layout,context):
    
    Create_Tab(layout,context,'Preset Menu', "bf_Preset_Menu",ExpandTab=False)
    row = layout.row()
    row.operator("custom.Preset_Button")
    
    #Preset_Menu = Draw.Menu(name,No_Event,9,Y_POS-BUTTON_Y_OFFSET,50,18, Preset_Menu.val, "Predefined metric screw sizes.")
    #Draw.Button("Apply",On_Preset_Click,150,Y_POS-BUTTON_Y_OFFSET,55,18,"Apply the preset screw sizes.")
 



def Create_New_Mesh(context):
    
    verts = []
    faces = []
    sMeshName =''
    sObjName =''
        
    if context.scene.bf_Model_Type == 'bf_Model_Bolt':
        #print('Create Bolt')
        verts, faces = Bolt_Mesh(context)
        sMeshName = 'Bolt'
        sObjName = 'Bolt'
    
    if context.scene.bf_Model_Type == 'bf_Model_Nut':
        #print('Create Nut')
        verts, faces = Nut_Mesh(context)
        sMeshName = 'Nut'
        sObjName = 'Nut'

    
    verts, faces = RemoveDoubles(verts, faces)
    
    verts = Scale_Mesh_Verts(verts,GLOBAL_SCALE)
    
    
    mesh = bpy.data.meshes.new(sMeshName)
    
    mesh.add_geometry((len(verts)), 0, int(len(faces)))
    mesh.verts.foreach_set("co", unpack_list(verts))
    mesh.faces.foreach_set("verts_raw", unpack_face_list(faces))


    scene = context.scene

    # ugh
    for ob in scene.objects:
        ob.selected = False

    mesh.update()
    ob_new = bpy.data.objects.new(sObjName, mesh)
    scene.objects.link(ob_new)
    ob_new.selected = True

    ob_new.location = scene.cursor_location

    obj_act = scene.objects.active

    if obj_act and obj_act.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

        obj_act.selected = True
        scene.update() # apply location
        #scene.objects.active = ob_new

        bpy.ops.object.join() # join into the active.

        bpy.ops.object.mode_set(mode='EDIT')
    else:
        scene.objects.active = ob_new
        if context.user_preferences.edit.enter_edit_mode:
            bpy.ops.object.mode_set(mode='EDIT')






class ObjectButtonsPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "Bolt Factory V3.00"
    
    Create_Propertys()
    Load_Preset(bpy.context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='PLUGIN')



    def draw(self,context):
        layout = self.layout
 
        ob = context.object
        sc = context.scene
        wide_ui = context.region.width > NARROW_UI
        
        layout.prop(sc, "bf_Model_Type", expand=True)
        
        if sc.bf_Model_Type == 'bf_Model_Bolt':
            Dispaly_Bolt_Tab(layout,sc)
        
        if sc.bf_Model_Type == 'bf_Model_Nut':
            Dispaly_Nut_Tab(layout,sc)
            
        Dispaly_Thread_Tab(layout,sc)
        Dispaly_Preset_Tab(layout,sc)
        row = layout.row()
        
        row.operator("custom.Create_Button")


       


class CUSTOM_OT_Preset_Button(bpy.types.Operator):
    bl_idname = "CUSTOM_OT_Preset_Button"
    bl_label = "Apply"
    __doc__ = "Apply the Presets"
    
    def invoke(self, context, event):
        Load_Preset(context)
        return('FINISHED')


class CUSTOM_OT_Create_Button(bpy.types.Operator):
    bl_idname = "CUSTOM_OT_Create_Button"
    bl_label = "Create"
    __doc__ = "Create Bolt"
    
    
    def invoke(self, context, event):
        Create_New_Mesh(context);
        return('FINISHED')


# Register the operator
# Add to a menu, reuse an icon used elsewhere that happens to have fitting name
# unfortunately, the icon shown is the one I expected from looking at the
# blenderbuttons file from the release/datafiles directory

#menu_func = (lambda self, context: self.layout.operator(AddStar.bl_idname,
#                                        text="Bolt", icon='PLUGIN'))



def register():
    bpy.types.register(ObjectButtonsPanel)
    bpy.types.register(CUSTOM_OT_Preset_Button)    
    bpy.types.register(CUSTOM_OT_Create_Button)
    
def unregister():
    bpy.types.unregister(ObjectButtonsPanel)
    bpy.types.unregister(CUSTOM_OT_Preset_Button)
    bpy.types.unregister(CUSTOM_OT_Create_Button)    

 
if __name__ == "__main__":
    register()