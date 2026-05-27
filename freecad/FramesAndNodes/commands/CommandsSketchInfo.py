import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from typing import ClassVar

from ..features.ProfileLogic import addInfoToSketch

from ..resources import Resources
from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

class CommandAddSketchInfo():
    Name: ClassVar[str] = "AddSketchInfo"

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
        sel = Gui.Selection.getSelection()
        for obj in sel:
            if obj.TypeId == 'Sketcher::SketchObject':
                addInfoToSketch(sketch=obj,MaxNsym=10)


Gui.addCommand("AddSketchInfo",CommandAddSketchInfo())
