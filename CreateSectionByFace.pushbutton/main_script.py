__author__ = 'Jakub Wlodarz'
__title__ = 'Create Section\nBy Face'
__version__ = '1.0.0'
__doc__ = """Short description"""

# Dependencies:
import clr
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitAPI")
clr.AddReference("System")

#Revit AplicationServices:
from Autodesk.Revit.ApplicationServices import Application

#Revit UI:
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI import Selection, UIApplication

#Revit DB:
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import XYZ, Line, Plane
from Autodesk.Revit.DB import BoundingBoxXYZ, SketchPlane, Transform, Options
from Autodesk.Revit.DB import FilteredElementCollector, ViewFamilyType, ViewFamily, ViewSection

#Revit Creation
from Autodesk.Revit.Creation import ItemFactoryBase

#pyRevit:
from pyrevit import revit
from pyrevit import UI

#System:
from System.Collections.Generic import List

# math
import math

# GUI:
from GUI import GUIWindowCSBF

#Revit Document:
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application


def GenerateNormalVectorFromSetOfCurves(SetOfCurves):
    #create vector with (0,0,0) coordinates:
    ZeroVector = XYZ()
    
    #If there is only one curve in SetOfCurves:
    if len(SetOfCurves) == 1:
        OnlyCurve = SetOfCurves[0]
        StartPoint = OnlyCurve.GetEndPoint(0)
        EndPoint = OnlyCurve.GetEndPoint(1)
        CurveVector = EndPoint - StartPoint
        
        Axis = XYZ(0.0,0.0,1.0) #vector representing Z-axis
        
        if CurveVector.CrossProduct(Axis).IsAlmostEqualTo(ZeroVector):
            Axis = XYZ(1.0,0.0,0.0) #change Axis to X
        NormalVector = CurveVector.CrossProduct(Axis)
        return NormalVector

def UnpackArray(array):
    output = []
    for element in array:
        output.append(element)
    return output

def generate_section_view_by_face(doc, uidoc, view_family, view_name, view_depth):
    selection = uidoc.Selection
    reference_to_picked_face = selection.PickObject(Selection.ObjectType.Face, "Please pick Face")

    face = doc.GetElement(reference_to_picked_face).\
               GetGeometryObjectFromReference(reference_to_picked_face)
    # print("face = {}".format(face))

    host = doc.GetElement(reference_to_picked_face)
    # print("host = {}".format(host))

    host_location = host.Location
    # print("host location = {}".format(host_location))

    normal_vector = face.FaceNormal
    # print("normal vector = {}".format(normal_vector))

    face_X_vector = face.XVector
    face_Y_vector = face.YVector

    bounding_box_uv = face.GetBoundingBox()
    # print("bounding box uv = {}".format(bounding_box_uv))

    max_UV = bounding_box_uv.Max
    min_UV = bounding_box_uv.Min

    # print("max UV = {}\nmin UV = {}".format(max_UV, min_UV))

    max_XYZ = face.Evaluate(max_UV)
    min_XYZ = face.Evaluate(min_UV)
    # print("max XYZ = {}\nmin XYZ = {}".format(max_XYZ, min_XYZ))

    new_line = Line.CreateBound(max_XYZ, min_XYZ)
    # print("new line start = {}".format(new_line.Evaluate(0, True)))
    # print("new line end = {}".format(new_line.Evaluate(1, True)))
    
    if isinstance(host, FamilyInstance):
        
        if isinstance(host_location, LocationPoint):
            translation = Transform.CreateTranslation(host_location.Point)
            rotation = Transform.CreateRotationAtPoint(XYZ.BasisZ, host_location.Rotation, host_location.Point)
            
            new_line = new_line.CreateTransformed(translation)
            new_line = new_line.CreateTransformed(rotation)
            normal_vector = rotation.OfVector(normal_vector)
            face_X_vector = rotation.OfVector(face_X_vector)
            face_Y_vector = rotation.OfVector(face_Y_vector)
            # print("new line transformed = {}".format(new_line))
        
        if isinstance(host_location, LocationCurve):
            translation = Transform.CreateTranslation(host_location.Curve.Evaluate(0.5, True))
            # print("host location curve" ,host_location.Curve.Evaluate(0, True))
            new_line = new_line.CreateTransformed(translation)
            # print("new line transformed = {}".format(new_line))

    # print("face X vector = {}".format(face_X_vector))
    # print("face Y vector = {}".format(face_Y_vector))

    new_line_midpoint = new_line.Evaluate(0.5, True)
    new_line_start = new_line.Evaluate(0, True) # MAX
    new_line_end = new_line.Evaluate(1, True) # MIN

    line_direction = new_line.Direction # XYZ vector
    alpha_angle = line_direction.AngleTo(face_X_vector)

    if alpha_angle * 180/math.pi >= 90:
        alpha_angle = (180 - (alpha_angle * 180/math.pi)) * math.pi/180
    
    len_of_new_line = new_line.Length

    offset_factor = 0.6
    x_size = len_of_new_line * math.cos(alpha_angle) * offset_factor
    y_size = len_of_new_line * math.sin(alpha_angle) * offset_factor

    # print("x size = {}".format(x_size))
    # print("y size = {}".format(y_size))

    # Generate view BoundingBox boundaries:
    bbox_min = XYZ(-x_size, -y_size, 0)
    bbox_max = XYZ(x_size, y_size, view_depth)

    # print("new line midpoint = {}".format(new_line_midpoint))
    # print("new line start = {}".format(new_line_start))
    # print("new line end = {}".format(new_line_end))
    
    with revit.Transaction('Create Section By Face'):
        
        # Creating new BoundingBox:
        new_BBox = BoundingBoxXYZ()

        # Creating transformation of BoundingBox:
        BBox_transformation = Transform.Identity
        BBox_transformation.Origin = new_line_midpoint

        # Generate transformation vectors:
        vector_X = face_X_vector.Negate().Normalize()
        vector_Y = face_Y_vector.Normalize()
        vector_Z = vector_X.CrossProduct(vector_Y)

        # Apply transformation vectors to BBox_transformation:
        BBox_transformation.BasisX = vector_X
        BBox_transformation.BasisY = vector_Y
        BBox_transformation.BasisZ = vector_Z

        # Apply transformation to new_BBox:
        new_BBox.Transform = BBox_transformation
        
        # Set new_BBox Max and Min:
        new_BBox.Max = bbox_max
        new_BBox.Min = bbox_min
        
        view_section = ViewSection.CreateSection(doc, view_family.Id, new_BBox)
        view_section.Name = view_name

    return new_BBox


#MAIN FUNCTION:
def main():
    ViewFamilyTypes_collection = FilteredElementCollector(doc).OfClass(ViewFamilyType)
    # print("view family types collection = {}".format(ViewFamilyType_collection))
    
    viewsection_families = []
    for view_family_type in ViewFamilyTypes_collection:
        if view_family_type.ViewFamily == ViewFamily.Section:
            viewsection_families.append(view_family_type)

    existing_SectionNames = []
    ViewSections_collection = FilteredElementCollector(doc).OfClass(ViewSection)
    for view_section in ViewSections_collection:
        section_name = Element.Name.GetValue(view_section)
        existing_SectionNames.append(section_name)

    # Dictionary with data from Revit for GUI:
    selection = uidoc.Selection
    reference_to_picked_face = selection.PickObject(Selection.ObjectType.Face, "Please pick Face")

    data_from_Revit = {"ViewSection Families": viewsection_families,
                       "Existing Section Names": existing_SectionNames,
                       "Face Reference": reference_to_picked_face}
    
    UI_Window = GUIWindowCSBF(doc, uidoc, data_from_Revit)
    UI_Window.Show()

    # # Keeping it to test:
    # section_family = None
    # for vft in ViewFamilyTypes_collection:
    #     if "Section" in Element.Name.GetValue(vft):
    #         section_family = vft
    #         break
    

    # name = "working section 1"
    # depth = 1
    # generate_section_view_by_face(doc, uidoc, section_family, name, depth)
    
if __name__ == "__main__":
    main()



























# NOTES:

# def GenerateNormalVectorFromSetOfCurves(SetOfCurves):
#     #create vector with (0,0,0) coordinates:
#     ZeroVector = XYZ()
    
#     #If there is only one curve in SetOfCurves:
#     if len(SetOfCurves) == 1:
#         OnlyCurve = SetOfCurves[0]
#         StartPoint = OnlyCurve.GetEndPoint(0)
#         EndPoint = OnlyCurve.GetEndPoint(1)
#         CurveVector = EndPoint - StartPoint
        
#         Axis = XYZ(0.0,0.0,1.0) #vector representing Z-axis
        
#         if CurveVector.CrossProduct(Axis).IsAlmostEqualTo(ZeroVector):
#             Axis = XYZ(1.0,0.0,0.0) #change Axis to X
#         NormalVector = CurveVector.CrossProduct(Axis)
#         return NormalVector


        # # checking XY dot product:
        # print("X and Y dot product = {}".format(vector_X.DotProduct(vector_Y)))
        # print("X and Z dot product = {}".format(vector_X.DotProduct(vector_Z)))
        # print("Y and Z dot product = {}".format(vector_Y.DotProduct(vector_Z)))

        # # checking lengths of vectors:
        # print("X len = {}".format(vector_X.GetLength()))
        # print("Y len = {}".format(vector_X.GetLength()))
        # print("Z len = {}".format(vector_X.GetLength()))

        # # checking if X x Y = Z:

        # X_Y_cross_product = vector_X.CrossProduct(vector_Y)
        # print("XY cross product = {}".format(X_Y_cross_product))
        # print("vector Z = {}".format(vector_Z))
        # print(X_Y_cross_product.IsAlmostEqualTo(vector_Z))
        # print("-" * 80)