# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Frank David Martínez Muñoz <mnesarco@gmail.com>
# SPDX-FileNotice: Part of the File Explorer addon.

# File copied from https://github.com/mnesarco/FileExplorerExt/blob/main/freecad/FileExplorerExt/_api.py
# This will be modified 

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import TypeAlias, Callable

FileActionFn: TypeAlias = Callable[[list[Path]], None]


@dataclass(kw_only=True)
class _CustomFileAction:
    text: str
    icon: object
    activated: FileActionFn


CustomActionProvider: TypeAlias = Callable[[list[Path]], list[_CustomFileAction]]


@dataclass
class ApiState:
    selected_path: Path | None = None
    action_providers: dict[object, CustomActionProvider] = field(
        default_factory=dict
    )


class FrameAndNodesApi:
    CustomFileAction = _CustomFileAction
    _state: ApiState

    def __init__(self):
        self._state = ApiState()

    @property
    def selected_path(self) -> Path | None:
        return self._state.selected_path

    def add_action_provider(self, provider: CustomActionProvider, key: object = None) -> None:
        self._state.action_providers[key or object()] = provider

    def get_custom_actions(self, paths: list[Path]) -> list[CustomFileAction]:
        actions: list[_CustomFileAction] = []
        if not self._state.action_providers:
            return actions

        for provider in self._state.action_providers.values():
            provided = provider(paths)
            if provided:
                actions.extend(provided)

        return actions


API = FrameAndNodesApi()