"""
novelWriter – GUI Document Viewer Panel
=======================================

File History:
Created: 2023-11-14 [2.2rc1] GuiDocViewerPanel

This file is a part of novelWriter
Copyright 2018–2023, Veronica Berglyd Olsen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import logging

from PyQt5.QtCore import QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget
)

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwHeaders, nwLabels, nwLists, trConst
from novelwriter.core.index import IndexHeading, IndexItem
from novelwriter.enum import nwItemClass

logger = logging.getLogger(__name__)


class GuiDocViewerPanel(QWidget):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocViewerPanel")

        self._lastHandle = None

        self.tabBackRefs = _ViewPanelBackRefs(self)

        self.mainTabs = QTabWidget(self)
        self.mainTabs.addTab(self.tabBackRefs, self.tr("Backreferences"))

        self.kwTabs: dict[str, _ViewPanelKeyWords] = {}
        self.idTabs: dict[str, int] = {}
        for itemClass in nwLists.USER_CLASSES:
            cTab = _ViewPanelKeyWords(self, itemClass)
            tabId = self.mainTabs.addTab(cTab, trConst(nwLabels.CLASS_NAME[itemClass]))
            self.kwTabs[itemClass.name] = cTab
            self.idTabs[itemClass.name] = tabId

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.mainTabs)
        self.outerBox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.outerBox)
        self.updateTheme()

        logger.debug("Ready: GuiDocViewerPanel")

        return

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""
        vPx = CONFIG.pxInt(4)
        lPx = CONFIG.pxInt(2)
        rPx = CONFIG.pxInt(14)
        hCol = self.palette().highlight().color()

        styleSheet = (
            "QTabWidget::pane {border: 0;} "
            "QTabWidget QTabBar::tab {"
            f"border: 0; padding: {vPx}px {rPx}px {vPx}px {lPx}px;"
            "} "
            "QTabWidget QTabBar::tab:selected {"
            f"color: rgb({hCol.red()}, {hCol.green()}, {hCol.blue()});"
            "} "
        )
        self.mainTabs.setStyleSheet(styleSheet)
        self.updateHandle(self._lastHandle)

        return

    def openProjectTasks(self) -> None:
        """Run open project tasks."""
        for key, name, tClass, iItem, hItem in SHARED.project.index.getTagsData():
            if tClass in self.kwTabs:
                print(key, name, iItem, hItem)
                self.kwTabs[tClass].addEntry(key, name, iItem, hItem)
        self._updateTabVisibility()
        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(str)
    def updateHandle(self, tHandle: str | None) -> None:
        """Update the document handle."""
        self._lastHandle = tHandle
        self.tabBackRefs.refreshContent(tHandle or None)
        return

    ##
    #  Internal Functions
    ##

    def _updateTabVisibility(self) -> None:
        """Hide class tabs with no content."""
        for tClass, cTab in self.kwTabs.items():
            self.mainTabs.setTabVisible(self.idTabs[tClass], cTab.count() > 0)
        return

# END Class GuiDocViewerPanel


class _ViewPanelBackRefs(QWidget):

    C_DATA     = 0
    C_TITLE    = 0
    C_EDIT     = 1
    C_VIEW     = 2
    C_DOCUMENT = 3

    D_HANDLE = Qt.ItemDataRole.UserRole
    D_TITLE  = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        iPx = SHARED.theme.baseIconSize
        cMg = CONFIG.pxInt(6)

        # Content
        self.listBox = QTreeWidget(self)
        # self.listBox.setHeaderHidden(True)
        # self.listBox.setColumnCount(4)
        self.listBox.setHeaderLabels([
            self.tr("Heading"), "", "", self.tr("Document")
        ])
        self.listBox.setIndentation(0)
        self.listBox.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.listBox.setIconSize(QSize(iPx, iPx))
        self.listBox.setFrameStyle(QFrame.Shape.NoFrame)

        treeHeader = self.listBox.header()
        treeHeader.setStretchLastSection(True)
        treeHeader.setSectionResizeMode(self.C_DOCUMENT, QHeaderView.ResizeMode.ResizeToContents)
        treeHeader.setSectionResizeMode(self.C_EDIT, QHeaderView.ResizeMode.Fixed)
        treeHeader.setSectionResizeMode(self.C_VIEW, QHeaderView.ResizeMode.Fixed)
        treeHeader.setSectionResizeMode(self.C_TITLE, QHeaderView.ResizeMode.ResizeToContents)
        treeHeader.resizeSection(self.C_EDIT, iPx + cMg)
        treeHeader.resizeSection(self.C_VIEW, iPx + cMg)

        fH1 = self.font()
        fH1.setBold(True)
        fH1.setUnderline(True)

        fH2 = self.font()
        fH2.setBold(True)

        self._hFonts = [self.font(), fH1, fH2, self.font(), self.font(), self.font()]
        self._editIcon = SHARED.theme.getIcon("edit")
        self._viewIcon = SHARED.theme.getIcon("view")

        # Assemble
        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.listBox)
        self.outerBox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.outerBox)
        self.setContentsMargins(0, 0, 0, 0)

        return

    def refreshContent(self, dHandle: str | None) -> None:
        """Update the content."""
        self.listBox.clear()
        if dHandle:
            refs = SHARED.project.index.getBackReferenceList(dHandle)
            for tHandle, (sTitle, hItem) in refs.items():
                nwItem = SHARED.project.tree[tHandle]
                if nwItem is None:
                    continue

                docIcon = SHARED.theme.getItemIcon(
                    nwItem.itemType, nwItem.itemClass,
                    nwItem.itemLayout, nwItem.mainHeading
                )
                iLevel = nwHeaders.H_LEVEL.get(hItem.level, 0) if nwItem.isDocumentLayout() else 5
                hDec = SHARED.theme.getHeaderDecorationNarrow(iLevel)

                trItem = QTreeWidgetItem()
                trItem.setText(self.C_TITLE, hItem.title)
                trItem.setData(self.C_TITLE, Qt.ItemDataRole.DecorationRole, hDec)
                trItem.setFont(self.C_TITLE, self._hFonts[iLevel])
                trItem.setIcon(self.C_EDIT, self._editIcon)
                trItem.setIcon(self.C_VIEW, self._viewIcon)
                trItem.setIcon(self.C_DOCUMENT, docIcon)
                trItem.setText(self.C_DOCUMENT, nwItem.itemName)

                trItem.setData(self.C_DATA, self.D_HANDLE, tHandle)
                trItem.setData(self.C_DATA, self.D_TITLE, sTitle)

                self.listBox.addTopLevelItem(trItem)
        return

# END Class _ViewPanelBackRefs


class _ViewPanelKeyWords(QTreeWidget):

    C_DATA     = 0
    C_NAME     = 0
    C_EDIT     = 1
    C_VIEW     = 2
    C_TITLE    = 3
    C_DOCUMENT = 4

    D_TAG    = Qt.ItemDataRole.UserRole
    D_HANDLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent: QWidget, itemClass: nwItemClass) -> None:
        super().__init__(parent=parent)
        self._itemClass = nwItemClass

        iPx = SHARED.theme.baseIconSize
        cMg = CONFIG.pxInt(6)

        self.setHeaderLabels([
            self.tr("Tag"), "", "", self.tr("Heading"), self.tr("Document")
        ])
        self.setIndentation(0)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setIconSize(QSize(iPx, iPx))
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSortingEnabled(True)
        self.sortByColumn(self.C_NAME, Qt.SortOrder.AscendingOrder)

        treeHeader = self.header()
        treeHeader.setStretchLastSection(True)
        treeHeader.setSectionResizeMode(self.C_NAME, QHeaderView.ResizeMode.ResizeToContents)
        treeHeader.setSectionResizeMode(self.C_EDIT, QHeaderView.ResizeMode.Fixed)
        treeHeader.setSectionResizeMode(self.C_VIEW, QHeaderView.ResizeMode.Fixed)
        treeHeader.resizeSection(self.C_EDIT, iPx + cMg)
        treeHeader.resizeSection(self.C_VIEW, iPx + cMg)

        self._classIcon = SHARED.theme.getIcon(nwLabels.CLASS_ICON[itemClass])
        self._editIcon = SHARED.theme.getIcon("edit")
        self._viewIcon = SHARED.theme.getIcon("view")

        return

    def count(self) -> int:
        return self.topLevelItemCount()

    def addEntry(self, tag: str, name: str, iItem: IndexItem | None,
                 hItem: IndexHeading | None) -> None:
        """Add a tag entry to the list."""
        if not iItem or not hItem:
            return

        nwItem = iItem.item
        docIcon = SHARED.theme.getItemIcon(
            nwItem.itemType, nwItem.itemClass,
            nwItem.itemLayout, nwItem.mainHeading
        )
        iLevel = nwHeaders.H_LEVEL.get(hItem.level, 0) if nwItem.isDocumentLayout() else 5
        hDec = SHARED.theme.getHeaderDecorationNarrow(iLevel)

        trItem = QTreeWidgetItem()
        trItem.setText(self.C_NAME, name)
        trItem.setIcon(self.C_NAME, self._classIcon)
        trItem.setIcon(self.C_EDIT, self._editIcon)
        trItem.setIcon(self.C_VIEW, self._viewIcon)
        trItem.setText(self.C_TITLE, hItem.title)
        trItem.setData(self.C_TITLE, Qt.ItemDataRole.DecorationRole, hDec)
        trItem.setIcon(self.C_DOCUMENT, docIcon)
        trItem.setText(self.C_DOCUMENT, nwItem.itemName)
        trItem.setData(self.C_DATA, self.D_TAG, tag)
        trItem.setData(self.C_DATA, self.D_HANDLE, iItem.handle)
        self.addTopLevelItem(trItem)

        return

# END Class _ViewPanelRefs
