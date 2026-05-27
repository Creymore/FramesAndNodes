# SPDX-License-Identifier: LGPL-2.1-or-later

"""Example FreeCAD Workbench."""

import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]

from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

from .resources import Resources
from .commands import CommandAddSketchInfo, CommandKnotPlacer, CommandProfilePlacer, CommandSaveKnot

class FramesAndNodesWorkbench(Gui.Workbench):

    MenuText: str = QT_TRANSLATE_NOOP(
            "FramesAndNodes",
            "Example Workbench",
        )

    ToolTip: str = QT_TRANSLATE_NOOP(
            "FramesAndNodes",
            "Example Workbench tooltip",
        )

    Icon: str = Resources.icon("FramesAndNodes-wb.svg")


    def Initialize(self) -> None:
        App.Console.PrintMessage("Example Workbench initialized\n")
        # Adding menus and toolbars when the Workbench is active (example)
        commands = [
            CommandKnotPlacer.Name,
            CommandProfilePlacer.Name,
            CommandSaveKnot.Name,
            CommandAddSketchInfo.Name,
        ]
        self.appendToolbar("FramesAndNodes", commands)
        self.appendMenu("FramesAndNodes", commands)

    def Activated(self) -> None:
        App.Console.PrintMessage("Example Workbench activated\n")

    def Deactivated(self) -> None:
        App.Console.PrintMessage("Example Workbench deactivated\n")

    def ContextMenu(self, recipient: str) -> None:
        App.Console.PrintMessage("Example Workbench context menu\n")
        # Adding context menus when the Workbench is active (example)
        self.appendContextMenu("", [])

    @classmethod
    def Install(cls) -> None:
        Gui.addWorkbench(cls)
