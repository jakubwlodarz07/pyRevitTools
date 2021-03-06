__author__ = 'Jakub Wlodarz'
__title__ = 'Disallow Join\nBeams'
__version__ = '1.0.0'
__doc__ = """Disallow Join at start and end of Structural Framing"""

# Dependencies:
import clr
clr.AddReference("RevitAPIUI")
clr.AddReference("RevitAPI")
clr.AddReference("System")

#Revit UI:
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.UI.Selection import Selection

#Revit DB:
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import FamilyInstance
from Autodesk.Revit.DB.Structure import StructuralType, StructuralFramingUtils

#pyRevit:
from pyrevit import UI
from pyrevit import revit

#System:
from System.Collections.Generic import List

#Revit Document:
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

#CLASSES:
class FramingSelectionFilter(ISelectionFilter):
    def AllowElement(self, element):
        if isinstance(element, FamilyInstance):
            if element.StructuralType == StructuralType.Beam:
                return True
            else:
                return False
        else:
            return False
            
#METHODS:

def PickFramingByRectangle():
    selection = uidoc.Selection
    framing_sel_filter = FramingSelectionFilter()
    try:
        elements = selection.PickElementsByRectangle(framing_sel_filter, 
        "Please pick Strctural Framing by drawing rectangle or hit ESC to cancel.")
        # FRM = doc.GetElement(reference)
        return elements
    except:
        #exception occures when user hit ESC while selecting Rebar
        return None

#MAIN FUNCTION:
def main():
    picked = PickFramingByRectangle()
    if picked != None:
        with revit.Transaction('Disallow Join - Beams'):
            for beam in picked:
                StructuralFramingUtils.DisallowJoinAtEnd(beam, 0)
                StructuralFramingUtils.DisallowJoinAtEnd(beam, 1)

if __name__ == "__main__":
    main()


# NOTES:

# def PickFraming():
#     selection = uidoc.Selection
#     framing_sel_filter = FramingSelectionFilter()
#     try:
#         # reference = selection.PickObject(ObjectType.Element, framing_sel_filter, "Please pick Strctural Framing by drawing rectangle.")
#         reference = selection.PickObject(ObjectType.Element, framing_sel_filter, "Please pick Strctural Framing by drawing rectangle.")
#         FRM = doc.GetElement(reference)
#         return FRM
#     except:
#         #exception occures when user hit ESC while selecting Rebar
#         return None


    # if picked == None:
    #     uidoc.Selection.SetElementIds(picked_before)
    # else:
    #     rebar_ids = SearchRebarsAfterParameter(picked, "Rebar Selection Mark")
    #     combined = []
    #     for i in rebar_ids:
    #         combined.append(i)
    #     for j in picked_before:
    #         combined.append(j)

    #     ICollection_combined = List[ElementId](combined)
    #     uidoc.Selection.SetElementIds(ICollection_combined)

    # picked_before = uidoc.Selection.GetElementIds()
    # print(picked_before)

    # def SearchRebarsAfterParameter(rebar, parameter_name):
#     parameter = rebar.LookupParameter(parameter_name)
#     parameter_id = parameter.Id
#     param_value_provider = ParameterValueProvider(parameter_id)
#     param_equality = FilterStringEquals()
#     string_value = parameter.AsString()
#     selection_value_rule = FilterStringRule(param_value_provider,
#                                             param_equality,
#                                             string_value,
#                                             False)
#     param_filter = ElementParameterFilter(selection_value_rule)
#     rebars_ids = FilteredElementCollector(doc).WherePasses(param_filter).ToElementIds()
#     return rebars_ids