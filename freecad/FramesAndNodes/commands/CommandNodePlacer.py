
import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from PySide import QtCore  # ty:ignore[unresolved-import]

from importlib.resources import files
from typing import ClassVar
from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

from .. import resources
from ..resources import Resources


from ..features.NodeLogic import MembersToBlankNode, MembersToNodeTuple2, NodeToID2, InsertPlaceNode,ChangeNode,RemoveNode, findBlank, ReadFrameMembersFromNode, readOrientations,OrientNode
from ..features.SaveAndLoad import dummyLibaryPaths, LoadFromLibary
from ..features.SelectionProcessing2 import getNodeFromFramesMembers
from ..features.SelectionProcessing2 import getFrameMembersFromSelection

Libarys = dummyLibaryPaths()
Node_PLACER_UI = str(files(resources).joinpath("panels", "TaskFramesAndNodesNodePlacer.ui"))  # ty:ignore[too-many-positional-arguments]

class CommandNodePlacer():

     # Good practice (optional): set a constant for your command name, it is used in several places.
    Name: ClassVar[str] = "NodePlacer"

    def __init__(self):
        pass

    def GetResources(self):
       return {
            "Pixmap": ""
            ,
            "MenuText": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Node Placer",
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Places or changes a Node for the selected frame members",
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        panel = TaskNodePlacer2()
        Gui.Control.showDialog(panel)

class TaskNodePlacer2():

    def __init__(self):
        self.form = Gui.PySideUic.loadUi(Node_PLACER_UI)
        self._selection_observer_active = False

        self.NoChange = "Don't Change"
        

        # State saver
        self.GloabalFrameMembers = []
        self.GloabalNode = []
        self.NodeFound = False
        self.MatchesFound = True
        self.Matches = {}
        self.Orientations = []

        # Labels
        #self.form

        # Button BindWidgets
        self.form.StartStopSearch.clicked.connect(self.onStartStopClicked)
        self.form.CreateBlankNode.clicked.connect(self.onCreateBlankNode)
        self.form.EditNode.clicked.connect(self.onEditNode)
        self.Insert =self.form.Insert
        self.Insert.clicked.connect(self.onInsertChangeNode)
        self.form.RemoveNode.clicked.connect(self.onRemoveNode)
        self.form.Orient.clicked.connect(self.onOrient)
        self.form.OpenGalerieSearch.clicked.connect(self.onOpenGalerieSearch)

        # Checkbox BindWidets
        self.asLink = self.form.asLink

        # Connect QlistView

        self.NodeFrameMemberListView = self.form.NodeFrameMemberList    # QListView holen
        self.NodeFrameMemberListmodel = QtCore.QStringListModel()       # Model erstellen
        self.NodeFrameMemberListView.setModel(self.NodeFrameMemberListmodel)     # Model setzen

        self.NodeListView =self.form.NodeSelctionList
        self.NodeListmodel = QtCore.QStringListModel()
        self.NodeListView.setModel(self.NodeListmodel)

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

        # Node
        Node = getNodeFromFramesMembers()
        #Nodeobj = App.getDocument().getObject()
        self.NodeListmodel.setStringList([""])
        self.NodeFound = False
        if not len(Node) == 0:
            self.NodeFound = True
            self.GloabalNode = []
            self.GloabalNode = list(Node)
            print(f"Node:{self.GloabalNode}")
            ShowNodes = []
            for Show in Node:
                ShowNodes.append(f"{Show.Label} | {Show.Name}")
            self.NodeListmodel.setStringList(ShowNodes)
            self.poppulateOrientations()

        # FrameMembers
        if self.NodeFound is True:
            FrameMembers = ReadFrameMembersFromNode(Node[0])
        else:
            FrameMembers = getFrameMembersFromSelection()

        self.NodeFrameMemberListmodel.setStringList([""])
        if not len(FrameMembers) == 0:
            self.GloabalFrameMembers = []
            self.GloabalFrameMembers = list(FrameMembers) #Important
            ShowMembers =[]
            for Show in FrameMembers:
                ShowMembers.append(f"{Show.Label} | {Show.Name}")
            self.NodeFrameMemberListmodel.setStringList(ShowMembers)
            print("Update Selection List")
            print( self.GloabalFrameMembers)

        #Insert button
        if self.NodeFound:
            self.Insert.setText("Change Node")
            self.form.ModePC.setText("Mode: Changing")
        else:
            self.Insert.setText("Insert Node")
            self.form.ModePC.setText("Mode: Placing")

        #Matches combobox
        if self.NodeFound is True and not  self.MatchesCombo.itemText(0) ==  self.NoChange:
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
        NodeID = NodeToID2( K=MembersToNodeTuple2(FrameMembers= FrameMembers),deg=True )
        results = LoadFromLibary(NodeID,lib)
        # print(results)
        self.MatchesCombo.clear()
        self.MatchesFound = True
        self.Matches.clear()
        self.Matches = results
        if len(results) == 0:
            self.MatchesCombo.addItem("No Mataches Found try:Create New")
            self.MatchesFound =False
        
        if self.NodeFound is True:
            self.MatchesCombo.addItem(self.NoChange)

        for result in results:
            self.MatchesCombo.addItem(result)

    def onCreateBlankNode(self):
        FrameMembers =  self.GloabalFrameMembers
        # print(FrameMembers)
        if not len(FrameMembers) == 0:
            MembersToBlankNode(FrameMembers=FrameMembers)
            self._unregister_selection_observer()
            Gui.Control.closeDialog()
        print("CreateBlankNode")

    def onEditNode(self):
        print("Edit Node")
        if self.MatchesCombo.currentText() == "":
            return
        if self.MatchesCombo.currentIndex() == 0 and self.NodeFound == True:
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
        orientations = readOrientations(self.GloabalNode[0])
        self.Orientations = orientations
        n = len(orientations)
        self.OrientationCombo.clear()
        for i in range(1,n+1):
            self.OrientationCombo.addItem(f"{i}")
        

    def onOrientationsChanged(self):
        pass

    def onRemoveNode(self):
        print("Remove Node")
        if self.NodeFound is False:
            print("No Node to remove")
            return

        RemoveNode(self.GloabalNode[0])
        print("Node Removed")

        self.updateSelectionList()
        self.OrientationCombo.clear()
        self.GloabalNode = []


    def onInsertChangeNode(self):
        print("Insert/Change Node")

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
        
        if self.MatchesCombo.currentIndex() == 0 and self.NodeFound == True: #Don't change is in dropdown
            return
        
        file = self.Matches[self.MatchesCombo.currentText()]
        print(f"FilePath of Inserted Node:{file}")
        Node = findBlank(App.openDocument(file))
        # print(f"Test:{FrameMembers}")
        aslink =self.asLink.isChecked()
        if self.NodeFound == False:
            InsertPlaceNode(target=doc,Node=Node,FrameMembers=FrameMembers,aslink=aslink)
        else:
            OldNode = self.GloabalNode[0]
            ChangeNode(target=doc,OldNode=OldNode,NewNode=Node,aslink=aslink)
            print("Replace Node")
        
        Gui.Selection.clearSelection()
        for member in currentSelection:
            Gui.Selection.addSelection(member)

        self.updateSelectionList()



    def onOrient(self):
        print("Orient")
        indx = self.OrientationCombo.currentIndex()
        print(f"Current Index:{indx}")
        if len(self.Orientations) == 0:
            self.OrientationCombo.addItem("No Orientations: Try Insert Node")
            return
        Orientation = self.Orientations[indx]
        Nodes = self.GloabalNode
        if len(Nodes) == 0:
            return
        Node = Nodes[0]
        OrientNode(Node=Node,Orientation=Orientation)

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


Gui.addCommand("NodePlacer",CommandNodePlacer())
