__author__ = 'Jakub Wlodarz'
__title__ = 'Reload Selected\nDWG'
__version__ = '1.0.0'
__doc__ = """Reloads Selected DWG Link"""

# Dependencies:
import clr
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitAPI")

#Revit UI:
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.UI import TaskDialogIcon

#Revit DB:
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import CADLinkType
from Autodesk.Revit.DB import Transaction

from pyrevit import UI

# System:
import System
from System.Collections.Generic import *

#REGEX:
import re

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

#CLASSES:
class DWGLinkSelectionFilter(ISelectionFilter):
    def AllowElement(self, element):
        pattern = r'.*(\.dwg)' #Category.Name must end with ".dwg" to match DWG Link
        if re.match(pattern, element.Category.Name):
            return True
        else:
            return False
            
#METHODS:
def GetDWG(doc, uidoc):
    selection = uidoc.Selection
    dwg_sel_filter = DWGLinkSelectionFilter()
    try:
        reference_to_DWG = selection.PickObject(ObjectType.Element, dwg_sel_filter, "Please pick the DWG or hit ESC to cancel")
        DWG = doc.GetElement(reference_to_DWG)
        return DWG
    except:
        #exception occures when user hit ESC while selecting DWG
        return None

def UnpackArray(array):
    output = []
    for element in array:
        output.append(element)
    return output

def reload_link(DWG):
    DWG.Reload()
    
def main():

    CADLinkType_coll = FilteredElementCollector(doc)
    CADLinkType_coll.OfClass(CADLinkType)
    CADLinkType_coll_unpacked = UnpackArray(CADLinkType_coll)
    
    flag = True
    while flag:
        
        DWG = GetDWG(doc, uidoc)
        
        if DWG == None:
            flag = False
        else:
            if DWG.IsLinked == False:
                content = "This is an Imported DWG which can't be reloaded"
                instruction = "Please select Linked DWG"
                #creating Error Dialog:
                error_dialog = UI.TaskDialog("Reload Selected DWG")
                error_dialog.MainIcon = TaskDialogIcon.TaskDialogIconShield
                error_dialog.TitleAutoPrefix = False
                error_dialog.MainContent = content
                error_dialog.MainInstruction = instruction
                #Show Error Dialog:
                error_dialog.Show()
               
            else:
                DWG_name = DWG.Category.Name
                t = Transaction(doc, "Reload Selected DWG")
                for cad_link in CADLinkType_coll_unpacked:
                    if cad_link.Category.Name == DWG_name:
                        t.Start()
                        cad_link.Reload()
                        t.Commit()
                flag = False
    
if __name__ == "__main__":
    main()
