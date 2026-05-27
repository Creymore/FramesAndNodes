# SPDX-License-Identifier: LGPL-2.1-or-later

"""Example demonstrating the workbench manipulator."""

from __future__ import annotations

from contextlib import suppress
from typing import ClassVar

import FreeCAD as App  # ty:ignore[unresolved-import]

from .example_command import ExampleCommand


class WorkbenchManipulator:
    """Adds/Remove Commands to Gui"""

    _instance: ClassVar[WorkbenchManipulator] | None = None  # ty:ignore[invalid-type-form]

    def modifyMenuBar(self) -> list[dict[str, str]]:
        """Add commands to menus."""
        return []

    def modifyContextMenu(self, recipient: str) -> list[dict[str, str]]:
        """Add commands to the context menu."""
        return []

    def modifyToolBars(self) -> list[dict[str, str]]:
        """Add commands to toolbars."""
        # Add our example command to the File toolbar
        #return [{"append": ExampleCommand.Name, "toolBar": "File"}]
        return []

    # Optional but useful (good practice to encapsulate here)
    @classmethod
    def install(cls) -> None:
        """Apply the workbench manipulator to the live session"""
        if App.GuiUp and cls._instance is None:
            cls._instance = WorkbenchManipulator()
            App.Gui.addWorkbenchManipulator(cls._instance)
            with suppress(Exception):
                App.Gui.activeWorkbench().reloadActive()

    # Optional but useful (good practice to encapsulate here)
    @classmethod
    def uninstall(cls) -> None:
        """Remove the workbench manipulator to the live session"""
        if App.GuiUp and cls._instance is not None:
            cls._instance = WorkbenchManipulator()
            App.Gui.removeWorkbenchManipulator(cls._instance)
            cls._instance = None
            with suppress(Exception):
                App.Gui.activeWorkbench().reloadActive()
