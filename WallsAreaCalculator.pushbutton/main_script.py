__author__ = 'Jakub Wlodarz'
__title__ = 'Face Area\nCalculator'
__version__ = '1.0.0'
__doc__ = """Calculates area of selected faces"""

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

# CONSTANTS:
FEET_TO_METER = 304.8/1000
SQ_FEET_TO_SQ_METERS = FEET_TO_METER**2

#Revit Document:
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application

def UnpackArray(array):
    output = []
    for element in array:
        output.append(element)
    return output

def get_picked_faces_area(doc, uidoc):
    selection = uidoc.Selection
    try:
        references_to_picked_face = selection.PickObjects(Selection.ObjectType.Face, "Please pick Face")
        total_area = 0
        single_areas = []
        for reference_to_picked_face in references_to_picked_face:
            face = doc.GetElement(reference_to_picked_face).\
                GetGeometryObjectFromReference(reference_to_picked_face)
            total_area += face.Area * SQ_FEET_TO_SQ_METERS
            single_areas.append(face.Area * SQ_FEET_TO_SQ_METERS)
        return (total_area, single_areas)
    # print("face = {}".format(face))
    except:
        return (0, [])

#MAIN FUNCTION:
def main():
    total_area, single_areas = get_picked_faces_area(doc, uidoc)
    print("You picked:")
    for index, a in enumerate(single_areas):
        print("nr {} = {} m2".format(index + 1, a))
    print("Total Area = {} m2".format(total_area))

if __name__ == "__main__":
    main()
