# Dependencies
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

# External Event:
from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent
from Autodesk.Revit.Exceptions import InvalidOperationException

# pyRevit:
from pyrevit import revit, script, framework, UI
from pyrevit.framework import ComponentModel

# pyevent:
import pyevent 
###this is not included with pyRevit! This program has bo be independent - ship this in main folder###
###(pyevent.py sits in ...\pyRevit-Master\site-packages)###

# Revit UI:
from Autodesk.Revit.UI import TaskDialog, TaskDialogIcon
from Autodesk.Revit.UI import Selection, UIApplication

# Revit DB:
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import XYZ, Line, Plane
from Autodesk.Revit.DB import BoundingBoxXYZ, SketchPlane, Transform, Options
from Autodesk.Revit.DB import FilteredElementCollector, ViewFamilyType, ViewFamily, ViewSection

# math
import math

# wpf:
import wpf

# CONSTANTS:
WPF_HIDDEN = framework.Windows.Visibility.Hidden
WPF_COLLAPSED = framework.Windows.Visibility.Collapsed
WPF_VISIBLE = framework.Windows.Visibility.Visible
FEET_TO_METER = 304.8/1000

# XAML FILE:
xaml_file = script.get_bundle_file('ui.xaml') # path of ui.xaml

class ReusableExternalEventHandler(IExternalEventHandler):
    
    def __init__(self, do_this):
        self.do_this = do_this
    
    def Execute(self, uiapp):
        try:
            self.do_this()
        except InvalidOperationException:
            UI.TaskDialog.Show("Error","Invalid Operation Exception")
        except:
            UI.TaskDialog.Show("Error","Reusable External Event Handler has thrown an Exception")
    
    def GetName(self):
        return "Reusable External Event Handler"

class reactive(property):
    #https://gui-at.blogspot.com/2009/11/inotifypropertychanged-in-ironpython.html
    """Decorator for WPF bound properties"""
    def __init__(self, getter):
        def newgetter(ui_control):
            try:
                return getter(ui_control)
            except AttributeError:
                return None
        super(reactive, self).__init__(newgetter)

    def setter(self, setter):
        def newsetter(ui_control, newvalue):
            oldvalue = self.fget(ui_control)
            if oldvalue != newvalue:
                setter(ui_control, newvalue)
                ui_control.OnPropertyChanged(setter.__name__)
        return property(
            fget=self.fget,
            fset=newsetter,
            fdel=self.fdel,
            doc=self.__doc__)

class Reactive(ComponentModel.INotifyPropertyChanged):
    """WPF property updator base mixin"""
    PropertyChanged, _propertyChangedCaller = pyevent.make_event()

    def add_PropertyChanged(self, value):
        self.PropertyChanged += value

    def remove_PropertyChanged(self, value):
        self.PropertyChanged -= value

    def OnPropertyChanged(self, prop_name):
        if self._propertyChangedCaller:
            args = ComponentModel.PropertyChangedEventArgs(prop_name)
            self._propertyChangedCaller(self, args)

class DataFromRevit:
    def __init__(self, data_from_Revit):
        # extracting input dictionary:
        viewsection_families = data_from_Revit["ViewSection Families"]

        viewsection_name_family_dict = {}  # create empty dictionary

        for family in viewsection_families:
            name = Element.Name.GetValue(family)  # retrieve name of family
            name_family_tuple = tuple([name, family])  # create tuple with name and family
            name_family_dict = dict([name_family_tuple])  # converting tuple to dictionary
            viewsection_name_family_dict.update(name_family_dict)  # updating dictionary

        self.viewsection_families_dict = viewsection_name_family_dict
        self.existing_sections_names = data_from_Revit["Existing Section Names"]
        self.face_reference = data_from_Revit["Face Reference"]

    # Standard properties:
    @property
    def ViewSectionFamilies(self):
        return sorted(self.viewsection_families_dict.keys())

class GUIWindowCSBF(framework.Windows.Window):
    def __init__(self, doc, uidoc, data_from_Revit):
        wpf.LoadComponent(self, xaml_file)
        
        # The GUI window will be always on top:
        self.Topmost = True

        # Load DataFromRevit:
        Data = DataFromRevit(data_from_Revit)
        self.DataFromRevit = Data
        self.combobox_SF.DataContext = Data
        
        self.selected_view_family = None
        self.selected_view_name = None
        self.selected_view_depth = None

        self.doc = doc
        self.uidoc = uidoc

        #Create Rebars ExternalEventHandler and ExternalEvent:
        create_section_event_handler = ReusableExternalEventHandler(self.generate_section_view_by_face)
        self.create_section_external_event = ExternalEvent.Create(create_section_event_handler)

        # functions to run when user press execute:
        self.execute_button.Click += self.on_execute

    def collapse(self):
        self.Visibility = WPF_COLLAPSED
        
    def make_visible(self):
        self.Visibility = WPF_VISIBLE

    def generate_section_view_by_face(self):
        
        doc = self.doc
        uidoc = self.uidoc
        view_family = self.selected_view_family
        view_name = self.selected_view_name
        view_depth = self.selected_view_depth

        reference_to_picked_face = self.DataFromRevit.face_reference

        face = doc.GetElement(reference_to_picked_face).GetGeometryObjectFromReference(reference_to_picked_face)

        host = doc.GetElement(reference_to_picked_face)
        host_location = host.Location

        normal_vector = face.FaceNormal

        face_X_vector = face.XVector
        face_Y_vector = face.YVector

        bounding_box_uv = face.GetBoundingBox()
        max_UV = bounding_box_uv.Max
        min_UV = bounding_box_uv.Min

        max_XYZ = face.Evaluate(max_UV)
        min_XYZ = face.Evaluate(min_UV)

        new_line = Line.CreateBound(max_XYZ, min_XYZ)
        
        if isinstance(host, FamilyInstance):
            
            if isinstance(host_location, LocationPoint):
                translation = Transform.CreateTranslation(host_location.Point)
                rotation = Transform.CreateRotationAtPoint(XYZ.BasisZ, host_location.Rotation, host_location.Point)
                
                new_line = new_line.CreateTransformed(translation)
                new_line = new_line.CreateTransformed(rotation)
                normal_vector = rotation.OfVector(normal_vector)
                face_X_vector = rotation.OfVector(face_X_vector)
                face_Y_vector = rotation.OfVector(face_Y_vector)
            
            if isinstance(host_location, LocationCurve):
                translation = Transform.CreateTranslation(host_location.Curve.Evaluate(0.5, True))
                new_line = new_line.CreateTransformed(translation)

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

        # Generate view BoundingBox boundaries:
        bbox_min = XYZ(-x_size, -y_size, 0)
        bbox_max = XYZ(x_size, y_size, view_depth)

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

    def on_execute(self, sender, args):
        selected_view_family_name = self.combobox_SF.SelectedItem

        self.selected_view_family = self.DataFromRevit.viewsection_families_dict[selected_view_family_name]
        self.selected_view_name = str(self.textbox_SN.Text)
        
        bad_depth_input = False
        try:
            self.selected_view_depth = float(self.textbox_D.Text)
        except:
            bad_depth_input = True
        
        bad_chars = r"\:{}[]|;<>?`~"
        contains_bad_char = False

        for ch in bad_chars:
            if ch in self.selected_view_name:
                contains_bad_char = True
                break

        if self.selected_view_name in self.DataFromRevit.existing_sections_names:
            
            self.collapse()
            #creating TaskDialog for Error Report:
            report_dialog = UI.TaskDialog("Name Error")
            report_dialog.MainIcon = TaskDialogIcon.TaskDialogIconInformation
            report_dialog.TitleAutoPrefix = False
            report_dialog.MainInstruction = "Name must be unique!"
            #Show Error Report:
            report_dialog.Show()
            #make GUI visible:
            self.make_visible()
        
        elif contains_bad_char:
            self.collapse()
            #creating TaskDialog for Error Report:
            report_dialog = UI.TaskDialog("Name Error")
            report_dialog.MainIcon = TaskDialogIcon.TaskDialogIconInformation
            report_dialog.TitleAutoPrefix = False
            report_dialog.MainInstruction = "Name cannot contain: {}".format(bad_chars)
            #Show Error Report:
            report_dialog.Show()
            #make GUI visible:
            self.make_visible()
        
        elif bad_depth_input:
            self.collapse()
            #creating TaskDialog for Error Report:
            report_dialog = UI.TaskDialog("Value Error")
            report_dialog.MainIcon = TaskDialogIcon.TaskDialogIconInformation
            report_dialog.TitleAutoPrefix = False
            report_dialog.MainInstruction = "Please input valid View Depth value!\n(in case of float use '.' as separator)"
            #Show Error Report:
            report_dialog.Show()
            #make GUI visible:
            self.make_visible()

        else:
            try:
                self.create_section_external_event.Raise()
            except:
                UI.TaskDialog.Show("Exception","An Exception occured while Executing")
            self.Close()




# NOTES:
    # Reactive properties:
    # @reactive
    # def RebarHookType(self):
    #     return list(self._RHT_names)
        
    # @RebarHookType.setter
    # def RebarHookType(self, value):
    #     self._RHT_names = value




