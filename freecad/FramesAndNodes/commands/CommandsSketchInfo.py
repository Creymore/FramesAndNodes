import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from typing import ClassVar

from ..features.FrameMemberLogic import addInfoToSketch

from ..resources import Resources
from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

class CommandAddSketchInfo():
    Name: ClassVar[str] = "FramesAndNodes_AddSketchInfo"

    def __init__(self):
        pass

    def GetResources(self):
        return {
            "Pixmap": ""
            ,
            "MenuText": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Add Sketch Info",
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Adds FramesAndNodes profile metadata to selected sketches",
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()
        sketches = [obj for obj in sel if obj.TypeId == 'Sketcher::SketchObject']
        documents = []
        for sketch in sketches:
            doc = sketch.Document
            if doc not in documents:
                documents.append(doc)

        for doc in documents:
            doc.openTransaction("Add Sketch Info")
        try:
            for sketch in sketches:
                addInfoToSketch(sketch=sketch,MaxNsym=10)
            for doc in documents:
                doc.commitTransaction()
        except Exception:
            for doc in documents:
                doc.abortTransaction()
            raise


Gui.addCommand(CommandAddSketchInfo.Name,CommandAddSketchInfo())
