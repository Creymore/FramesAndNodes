
import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from PySide import QtCore  # ty:ignore[unresolved-import]

from importlib.resources import files
from typing import ClassVar
from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

from .. import resources
from ..resources import Resources


from ..features.KnotLogic import MembersToBlankKnot, MembersToKnotTuple2, KnotToID2, InsertPlaceKnot,ChangeKnot,RemoveKnot, findBlank, ReadFrameMembersFromKnot, readOrientations,OrientKnot
from ..features.SaveAndLoad import dummyLibaryPaths, LoadFromLibary
from ..features.SelectionProcessing2 import getKnotFromFrameMembers
from ..features.SelectionProcessing2 import getFrameMembersFromSelection

Libarys = dummyLibaryPaths()
KNOT_PLACER_UI = str(files(resources).joinpath("panels", "TaskFramesAndKnotsKnotPlacer.ui"))  # ty:ignore[too-many-positional-arguments]

class CommandKnotPlacer():

     # Good practice (optional): set a constant for your command name, it is used in several places.
    Name: ClassVar[str] = "KnotPlacer"

    def __init__(self):
        pass

    def GetResources(self):
       return {
            "Pixmap": ""
            ,
            "MenuText": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Knot Placer",
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Places or changes a knot for the selected frame members",
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        panel = TaskKnotPlacer2()
        Gui.Control.showDialog(panel)

class TaskKnotPlacer2():

    def __init__(self):
        self.form = Gui.PySideUic.loadUi(KNOT_PLACER_UI)
        self._selection_observer_active = False

        self.NoChange = "Don't Change"
        

        # State saver
        self.GloabalFrameMembers = []
        self.GloabalKnot = []
        self.KnotFound = False
        self.MatchesFound = True
        self.Matches = {}
        self.Orientations = []

        # Labels
        #self.form

        # Button BindWidgets
        self.form.StartStopSearch.clicked.connect(self.onStartStopClicked)
        self.form.CreateBlankKnot.clicked.connect(self.onCreateBlankKnot)
        self.form.EditKnot.clicked.connect(self.onEditKnot)
        self.Insert =self.form.Insert
        self.Insert.clicked.connect(self.onInsertChangeKnot)
        self.form.RemoveKnot.clicked.connect(self.onRemoveKnot)
        self.form.Orient.clicked.connect(self.onOrient)
        self.form.OpenGalerieSearch.clicked.connect(self.onOpenGalerieSearch)

        # Checkbox BindWidets
        self.asLink = self.form.asLink

        # Connect QlistView

        self.KnotFrameMemberListView = self.form.KnotFrameMemberList    # QListView holen
        self.KnotFrameMemberListmodel = QtCore.QStringListModel()       # Model erstellen
        self.KnotFrameMemberListView.setModel(self.KnotFrameMemberListmodel)     # Model setzen

        self.KnotListView =self.form.KnotSelctionList
        self.KnotListmodel = QtCore.QStringListModel()
        self.KnotListView.setModel(self.KnotListmodel)

        # Connect QComboBox

        self.LibaryCombo = self.form.Libary
        self.LibaryCombo.currentIndexChanged.connect(self.onLibaryChanged)

        self.MatchesCombo = self.form.Matches
        self.MatchesCombo.currentIndexChanged.connect(self.onMatchesChanged)

        self.OrientationCombo = self.form.Orientations
        self.OrientationCombo.currentIndexChanged.connect(self.onOrientationChanged)

        # Selction list
        self._register_selection_observer()
        self.updateSelectionList()

        # Libary QComboBox
        self.poppulateLiabrylist()

    def _register_selection_observer(self):
        if not self._selection_observer_active:
            Gui.Selection.addObserver(self)
            self._selection_observer_active = True

    def _unregister_selection_observer(self):
        if self._selection_observer_active:
            Gui.Selection.removeObserver(self)
            self._selection_observer_active = False

    def updateSelectionList(self):

        # Knot
        Knot = getKnotFromFrameMembers()
        #Knotobj = App.getDocument().getObject()
        self.KnotListmodel.setStringList([""])
        self.KnotFound = False
        if not len(Knot) == 0:
            self.KnotFound = True
            self.GloabalKnot = []
            self.GloabalKnot = list(Knot)
            print(f"Knot:{self.GloabalKnot}")
            ShowKnots = []
            for Show in Knot:
                ShowKnots.append(f"{Show.Label} | {Show.Name}")
            self.KnotListmodel.setStringList(ShowKnots)
            self.poppulateOrientations()

        # FrameMembers
        if self.KnotFound is True:
            FrameMembers = ReadFrameMembersFromKnot(Knot=Knot[0])
        else:
            FrameMembers = getFrameMembersFromSelection()

        self.KnotFrameMemberListmodel.setStringList([""])
        if not len(FrameMembers) == 0:
            self.GloabalFrameMembers = []
            self.GloabalFrameMembers = list(FrameMembers) #Important
            ShowMembers =[]
            for Show in FrameMembers:
                ShowMembers.append(f"{Show.Label} | {Show.Name}")
            self.KnotFrameMemberListmodel.setStringList(ShowMembers)
            print("Update Selection List")
            print( self.GloabalFrameMembers)

        #Insert button
        if self.KnotFound:
            self.Insert.setText("Change Knot")
            self.form.ModePC.setText("Mode: Changing")
        else:
            self.Insert.setText("Insert Knot")
            self.form.ModePC.setText("Mode: Placing")

        #Matches combobox
        if self.KnotFound is True and not  self.MatchesCombo.itemText(0) ==  self.NoChange:
            self.MatchesCombo.insertItem(0,self.NoChange)
            self.MatchesCombo.setCurrentIndex(0)

    def onOpenGalerieSearch(self):
        print("Open Galerie Search")

    def onStartStopClicked(self):
        print("Start/StopSearch")

        # self._unregister_selection_observer()

        lib = Libarys[self.LibaryCombo.currentText()]
        # print(lib)
        FrameMembers = self.GloabalFrameMembers
        if len(FrameMembers) == 0:
            return
        # print(FrameMembers)
        KnotID = KnotToID2( K=MembersToKnotTuple2(FrameMembers= FrameMembers),deg=True )
        results = LoadFromLibary(KnotID=KnotID,lib=lib)
        # print(results)
        self.MatchesCombo.clear()
        self.MatchesFound = True
        self.Matches.clear()
        self.Matches = results
        if len(results) == 0:
            self.MatchesCombo.addItem("No Mataches Found try:Create New")
            self.MatchesFound =False
        
        if self.KnotFound is True:
            self.MatchesCombo.addItem(self.NoChange)

        for result in results:
            self.MatchesCombo.addItem(result)

    def onCreateBlankKnot(self):
        FrameMembers =  self.GloabalFrameMembers
        # print(FrameMembers)
        if not len(FrameMembers) == 0:
            MembersToBlankKnot(FrameMembers=FrameMembers)
            self._unregister_selection_observer()
            Gui.Control.closeDialog()
        print("CreateBlankKnot")

    def onEditKnot(self):
        print("Edit Knot")
        if self.MatchesCombo.currentText() == "":
            return
        if self.MatchesCombo.currentIndex() == 0 and self.KnotFound == True:
            return
        file = self.Matches[self.MatchesCombo.currentText()]
        doc = App.openDocument(file,False,False)
        App.closeDocument(doc.Name)
        doc = App.openDocument(file,False,False)
        App.setActiveDocument(doc.Name)
        App.ActiveDocument=App.getDocument(doc.Name)
        Gui.ActiveDocument=Gui.getDocument(doc.Name)

        self._unregister_selection_observer()
        Gui.Control.closeDialog()
        return True

    def poppulateLiabrylist(self):
        for liabry in Libarys:
            self.LibaryCombo.addItem(liabry)

    def onLibaryChanged(self, index):
        key = self.form.Libary.currentText()
        value = self.form.Libary.currentData()

        print("Key:", key)
        print("Value:", value)

    def onMatchesChanged(self):
        key = self.MatchesCombo.currentText()
        print(key)
    
    def onOrientationChanged(self):
        key = self.OrientationCombo.currentText()
        print(key)

    def poppulateOrientations(self):
        orientations = readOrientations(self.GloabalKnot[0])
        self.Orientations = orientations
        n = len(orientations)
        self.OrientationCombo.clear()
        for i in range(1,n+1):
            self.OrientationCombo.addItem(f"{i}")
        

    def onOrientationsChanged(self):
        pass

    def onRemoveKnot(self):
        print("Remove Knot")
        if self.KnotFound is False:
            print("No Knot to remove")
            return

        RemoveKnot(self.GloabalKnot[0])
        print("Knot Removed")

        self.updateSelectionList()
        self.OrientationCombo.clear()
        self.GloabalKnot = []


    def onInsertChangeKnot(self):
        print("Insert/Change Knot")

        currentSelection = self.GloabalFrameMembers
        
        # print(f"asLink:{self.asLink.isChecked()}")

        FrameMembers = self.GloabalFrameMembers
        if len(FrameMembers) == 0:
            return
        # print(FrameMembers)
        doc = FrameMembers[0].Document
        # print(self.Matches)
        # print()
        if self.MatchesCombo.currentText() == "" or self.MatchesCombo.currentText() ==  self.NoChange:
            return
        
        if self.MatchesCombo.currentIndex() == 0 and self.KnotFound == True: #Don't change is in dropdown
            return
        
        file = self.Matches[self.MatchesCombo.currentText()]
        print(f"FilePath of Inserted Knot:{file}")
        Knot = findBlank(App.openDocument(file))
        # print(f"Test:{FrameMembers}")
        aslink =self.asLink.isChecked()
        if self.KnotFound == False:
            InsertPlaceKnot(target=doc,Knot=Knot,FrameMembers=FrameMembers,aslink=aslink)
        else:
            OldKnot = self.GloabalKnot[0]
            ChangeKnot(target=doc,OldKnot=OldKnot,NewKnot=Knot,aslink=aslink)
            print("Replace Knot")
        
        Gui.Selection.clearSelection()
        for member in currentSelection:
            Gui.Selection.addSelection(member)

        self.updateSelectionList()



    def onOrient(self):
        print("Orient")
        indx = self.OrientationCombo.currentIndex()
        print(f"Current Index:{indx}")
        if len(self.Orientations) == 0:
            self.OrientationCombo.addItem("No Orientations: Try Insert Knot")
            return
        Orientation = self.Orientations[indx]
        Knots = self.GloabalKnot
        if len(Knots) == 0:
            return
        Knot = Knots[0]
        OrientKnot(Knot=Knot,Orientation=Orientation)

    # Selection
    def addSelection(self, doc_name, obj_name, sub_name, point):
        del doc_name, obj_name, sub_name, point
        self.updateSelectionList()

    def removeSelection(self, doc_name, obj_name, sub_name):
        del doc_name, obj_name, sub_name
        self.updateSelectionList()

    def setSelection(self, doc_name):
        del doc_name
        self.updateSelectionList()

    def clearSelection(self, doc_name):
        del doc_name
        self.updateSelectionList()
    # Selection

    def reject(self):
        print("rejected")
        self._unregister_selection_observer()
        Gui.Control.closeDialog()
        return True

    def accept(self):
        print("accept")
        self._unregister_selection_observer()
        Gui.Control.closeDialog()
        return True


Gui.addCommand("KnotPlacer",CommandKnotPlacer())
