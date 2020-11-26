__author__ = 'Jakub Wlodarz'
__title__ = 'Workplane By\nFace'
__version__ = '1.0.0'
__doc__ = """Makes Setting Work Plane Easy"""

# Dependencies:
import clr
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitAPI")

#Revit UI:
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI import Selection, UIApplication

#Revit DB:
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import SketchPlane

#pyRevit:
from pyrevit import revit
from pyrevit import UI

#Revit Document:
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

def pick_face(doc, uidoc):
    selection = uidoc.Selection
    try:
        reference_to_picked_face = selection.PickObject(Selection.ObjectType.Face, "Please pick Face")
        return reference_to_picked_face
    except:
        return None

#MAIN FUNCTION:
def main():
    ref = pick_face(doc, uidoc)
    if ref != None:
        with revit.Transaction('Work Plane By Face'):
            new_sketch_plane = SketchPlane.Create(doc, ref)
            uidoc.ActiveView.SketchPlane = new_sketch_plane
if __name__ == "__main__":
    main()
