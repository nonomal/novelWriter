"""
novelWriter – GUI Build Manuscript
==================================
GUI classes for the Manuscript build tool

File History:
Created: 2023-02-13 [2.1b1]

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

import logging

import novelwriter

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QPushButton,
    QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget
)

from novelwriter.core.buildsettings import BuildSettings, FilterMode
from novelwriter.extensions.switchbox import NSwitchBox
from novelwriter.extensions.pagedsidebar import NPagedSideBar

logger = logging.getLogger(__name__)


class GuiBuildManuscript(QDialog):

    OPT_FILTERS  = 1
    OPT_HEADINGS = 2
    OPT_FORMAT   = 3
    OPT_CONTENT  = 4
    BLD_HTML     = 5
    BLD_MARKDOWN = 6
    BLD_ODT      = 7

    def __init__(self, mainGui):
        super().__init__(parent=mainGui)

        self.mainConf   = novelwriter.CONFIG
        self.mainGui    = mainGui
        self.mainTheme  = mainGui.mainTheme
        self.theProject = mainGui.theProject

        self.buildOpts = {
            "name": self.tr("Default Settings"),
            "settings": BuildSettings(),
            "filter": {},
        }

        self.setWindowTitle(self.tr("Build Manuscript"))
        self.setMinimumWidth(self.mainConf.pxInt(700))
        self.setMinimumHeight(self.mainConf.pxInt(400))

        # Style
        mPx = self.mainConf.pxInt(150)
        wWin = self.mainConf.pxInt(900)
        hWin = self.mainConf.pxInt(600)

        pOptions = self.theProject.options
        self.resize(
            self.mainConf.pxInt(pOptions.getInt("GuiBuildManuscript", "winWidth",  wWin)),
            self.mainConf.pxInt(pOptions.getInt("GuiBuildManuscript", "winHeight", hWin))
        )

        # Options SideBar
        # ===============

        self.optSideBar = NPagedSideBar(self)
        self.optSideBar.setMinimumWidth(mPx)
        self.optSideBar.setMaximumWidth(mPx)
        self.optSideBar.setLabelColor(self.mainTheme.helpText)

        self.optSideBar.addLabel(self.tr("Options"))
        self.optSideBar.addButton(self.tr("Filters"), self.OPT_FILTERS)
        self.optSideBar.addButton(self.tr("Headings"), self.OPT_HEADINGS)
        self.optSideBar.addButton(self.tr("Format"), self.OPT_FORMAT)
        self.optSideBar.addButton(self.tr("Content"), self.OPT_CONTENT)
        self.optSideBar.addSeparator()

        self.optSideBar.addLabel(self.tr("Build"))
        self.optSideBar.addButton(self.tr("HTML"), self.BLD_HTML)
        self.optSideBar.addButton(self.tr("Markdown"), self.BLD_MARKDOWN)
        self.optSideBar.addButton(self.tr("Open Document"), self.BLD_ODT)

        self.optSideBar.buttonClicked.connect(self._stackPageSelected)

        # Options Area
        # ============

        # Create Tabs
        self.optTabSelect = GuiBuildFilterTab(self)
        self.optTabHeadings = GuiBuildHeadingsTab(self)
        self.optTabFormat = GuiBuildFormatTab(self)
        self.optTabContent = GuiBuildContentTab(self)
        self.buildTabHTML = GuiBuildHTMLTab(self)
        self.buildTabMarkdown = GuiBuildMarkdownTab(self)
        self.buildTabODT = GuiBuildODTTab(self)

        # Add Tabs
        self.toolStack = QStackedWidget(self)
        self.toolStack.addWidget(self.optTabSelect)
        self.toolStack.addWidget(self.optTabHeadings)
        self.toolStack.addWidget(self.optTabFormat)
        self.toolStack.addWidget(self.optTabContent)
        self.toolStack.addWidget(self.buildTabHTML)
        self.toolStack.addWidget(self.buildTabMarkdown)
        self.toolStack.addWidget(self.buildTabODT)

        # Assemble
        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.optSideBar)
        self.outerBox.addWidget(self.toolStack)

        self.setLayout(self.outerBox)

        # Set Default Tab
        self.optSideBar.setSelected(self.OPT_FILTERS)

        return

    def loadContent(self):
        """Populate the tool widgets.
        """
        self.optTabSelect.populateTree()
        self.optTabSelect.populateFilters()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(int)
    def _stackPageSelected(self, pageId):
        """Process a user request to switch page.
        """
        if pageId == self.OPT_FILTERS:
            self.toolStack.setCurrentWidget(self.optTabSelect)
        elif pageId == self.OPT_HEADINGS:
            self.toolStack.setCurrentWidget(self.optTabHeadings)
        elif pageId == self.OPT_FORMAT:
            self.toolStack.setCurrentWidget(self.optTabFormat)
        elif pageId == self.OPT_CONTENT:
            self.toolStack.setCurrentWidget(self.optTabContent)
        elif pageId == self.BLD_HTML:
            self.toolStack.setCurrentWidget(self.buildTabHTML)
        elif pageId == self.BLD_MARKDOWN:
            self.toolStack.setCurrentWidget(self.buildTabMarkdown)
        elif pageId == self.BLD_ODT:
            self.toolStack.setCurrentWidget(self.buildTabODT)
        return

    ##
    #  Events
    ##

    def closeEvent(self, event):
        """Capture the user closing the window so we can save settings.
        """
        self._saveSettings()
        event.accept()
        return

    ##
    #  Internal Functions
    ##

    def _saveSettings(self):
        """Save the various user settings.
        """
        logger.debug("Saving GuiBuildManuscript settings")

        winWidth  = self.mainConf.rpxInt(self.width())
        winHeight = self.mainConf.rpxInt(self.height())

        treeWidth, filterWidth = self.optTabSelect.mainSplitSizes()

        pOptions = self.theProject.options
        pOptions.setValue("GuiBuildManuscript", "winWidth", winWidth)
        pOptions.setValue("GuiBuildManuscript", "winHeight", winHeight)
        pOptions.setValue("GuiBuildManuscript", "treeWidth", treeWidth)
        pOptions.setValue("GuiBuildManuscript", "filterWidth", filterWidth)
        pOptions.saveSettings()

        return

# END Class GuiBuildManuscript


class GuiBuildFilterTab(QWidget):

    C_DATA   = 0
    C_NAME   = 0
    C_ACTIVE = 1
    C_STATUS = 2

    D_HANDLE = Qt.UserRole
    D_FILE   = Qt.UserRole + 1

    F_NONE     = 0
    F_FILTERED = 1
    F_INCLUDED = 2
    F_EXCLUDED = 3

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        self.mainConf   = novelwriter.CONFIG
        self.mainGui    = buildMain.mainGui
        self.mainTheme  = buildMain.mainGui.mainTheme
        self.theProject = buildMain.mainGui.theProject
        self.buildOpts  = buildMain.buildOpts

        self._treeMap = {}

        self._statusFlags = {
            self.F_NONE:     ("", QIcon()),
            self.F_FILTERED: (self.tr("Filtered"), self.mainTheme.getIcon("build_filtered")),
            self.F_INCLUDED: (self.tr("Included"), self.mainTheme.getIcon("build_included")),
            self.F_EXCLUDED: (self.tr("Excluded"), self.mainTheme.getIcon("build_excluded")),
        }

        # Project Tree
        # ============

        # Tree Settings
        iPx = self.mainTheme.baseIconSize
        cMg = self.mainConf.pxInt(6)

        # Tree Widget
        self.optTree = QTreeWidget(self)
        self.optTree.setIconSize(QSize(iPx, iPx))
        self.optTree.setUniformRowHeights(True)
        self.optTree.setAllColumnsShowFocus(True)
        self.optTree.setHeaderHidden(True)
        self.optTree.setIndentation(iPx)
        self.optTree.setColumnCount(3)

        treeHeader = self.optTree.header()
        treeHeader.setStretchLastSection(False)
        treeHeader.setSectionResizeMode(self.C_NAME, QHeaderView.Stretch)
        treeHeader.setSectionResizeMode(self.C_ACTIVE, QHeaderView.Fixed)
        treeHeader.setSectionResizeMode(self.C_STATUS, QHeaderView.Fixed)
        treeHeader.resizeSection(self.C_ACTIVE, iPx + cMg)
        treeHeader.resizeSection(self.C_STATUS, iPx + cMg)

        self.optTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.optTree.setDragDropMode(QAbstractItemView.NoDragDrop)

        # Filters
        # =======

        self.filteredButton = QPushButton(self)
        self.filteredButton.setText(self._statusFlags[self.F_FILTERED][0])
        self.filteredButton.setIcon(self._statusFlags[self.F_FILTERED][1])
        self.filteredButton.clicked.connect(lambda: self._setSelectedMode(self.F_FILTERED))

        self.includedButton = QPushButton(self)
        self.includedButton.setText(self._statusFlags[self.F_INCLUDED][0])
        self.includedButton.setIcon(self._statusFlags[self.F_INCLUDED][1])
        self.includedButton.clicked.connect(lambda: self._setSelectedMode(self.F_INCLUDED))

        self.excludedButton = QPushButton(self)
        self.excludedButton.setText(self._statusFlags[self.F_EXCLUDED][0])
        self.excludedButton.setIcon(self._statusFlags[self.F_EXCLUDED][1])
        self.excludedButton.clicked.connect(lambda: self._setSelectedMode(self.F_EXCLUDED))

        self.modeBox = QHBoxLayout()
        self.modeBox.addWidget(self.filteredButton)
        self.modeBox.addWidget(self.includedButton)
        self.modeBox.addWidget(self.excludedButton)

        # Filer Options
        self.filterOpt = NSwitchBox(self, iPx)
        self.filterOpt.switchToggled.connect(self._applyFilterSwitch)

        # Assemble
        # ========

        pOptions = self.theProject.options
        wTree = self.mainConf.pxInt(pOptions.getInt("GuiBuildManuscript", "treeWidth", 0))
        fTree = self.mainConf.pxInt(pOptions.getInt("GuiBuildManuscript", "filterWidth", 0))

        self.selectionBox = QVBoxLayout()
        self.selectionBox.addLayout(self.modeBox)
        self.selectionBox.addWidget(self.filterOpt)
        self.selectionBox.setContentsMargins(0, 0, 0, 0)

        self.selectionWidget = QWidget()
        self.selectionWidget.setLayout(self.selectionBox)

        self.mainSplit = QSplitter()
        self.mainSplit.addWidget(self.optTree)
        self.mainSplit.addWidget(self.selectionWidget)
        if wTree > 0:
            self.mainSplit.setSizes([wTree, fTree])

        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.mainSplit)

        self.setLayout(self.outerBox)

        return

    def mainSplitSizes(self):
        """Extract the sizes of the main splitter.
        """
        sizes = self.mainSplit.sizes()
        if len(sizes) < 2:
            return 0, 0
        return sizes[0], sizes[1]

    def populateTree(self):
        """Build the tree of project items.
        """
        logger.debug("Building project tree")
        self._treeMap = {}
        self.optTree.clear()
        bSettings = self.buildOpts["settings"]
        for nwItem in self.theProject.getProjectItems():

            tHandle = nwItem.itemHandle
            pHandle = nwItem.itemParent
            rHandle = nwItem.itemRoot
            isFile = nwItem.isFileType()
            isActive = nwItem.isActive

            if nwItem.isInactiveClass() or not bSettings.isRootAllowed(rHandle):
                continue

            hLevel = nwItem.mainHeading
            itemIcon = self.mainTheme.getItemIcon(
                nwItem.itemType, nwItem.itemClass, nwItem.itemLayout, hLevel
            )

            if isFile:
                iconName = "checked" if isActive else "unchecked"
            else:
                iconName = "noncheckable"

            trItem = QTreeWidgetItem()
            trItem.setIcon(self.C_NAME, itemIcon)
            trItem.setText(self.C_NAME, nwItem.itemName)
            trItem.setData(self.C_DATA, self.D_HANDLE, tHandle)
            trItem.setData(self.C_DATA, self.D_FILE, isFile)
            trItem.setIcon(self.C_ACTIVE, self.mainTheme.getIcon(iconName))

            trItem.setTextAlignment(self.C_NAME, Qt.AlignLeft)

            if pHandle is None:
                if nwItem.isRootType():
                    self.optTree.addTopLevelItem(trItem)
                else:
                    logger.debug("Skipping item '%s'", tHandle)
                    continue

            elif pHandle in self._treeMap:
                self._treeMap[pHandle].addChild(trItem)

            else:
                logger.debug("Skipping item '%s'", tHandle)
                continue

            self._treeMap[tHandle] = trItem
            trItem.setExpanded(True)

        self._setTreeItemMode()

        return

    def populateFilters(self):
        """Populate the filter options switches.
        """
        self.filterOpt.clear()
        bSettings = self.buildOpts["settings"]

        self.filterOpt.addLabel(bSettings.getLabel("filter"))
        self.filterOpt.addItem(
            self.mainTheme.getIcon("proj_scene"),
            bSettings.getLabel("filter.includeNovel"),
            "doc:filter.includeNovel",
            default=bSettings.getValue("filter.includeNovel") or False
        )
        self.filterOpt.addItem(
            self.mainTheme.getIcon("proj_note"),
            bSettings.getLabel("filter.includeNotes"),
            "doc:filter.includeNotes",
            default=bSettings.getValue("filter.includeNotes") or False
        )
        self.filterOpt.addItem(
            self.mainTheme.getIcon("unchecked"),
            bSettings.getLabel("filter.includeInactive"),
            "doc:filter.includeInactive",
            default=bSettings.getValue("filter.includeInactive") or False
        )

        self.filterOpt.addSeparator()

        # Root Classes
        self.filterOpt.addLabel(self.tr("Root Folders"))
        for tHandle, nwItem in self.theProject.tree.iterRoots(None):
            if not nwItem.isInactiveClass():
                itemIcon = self.mainTheme.getItemIcon(
                    nwItem.itemType, nwItem.itemClass, nwItem.itemLayout
                )
                self.filterOpt.addItem(itemIcon, nwItem.itemName, f"root:{tHandle}", default=True)

        return

    ##
    #  Slots
    ##

    @pyqtSlot(str, bool)
    def _applyFilterSwitch(self, key, state):
        """A filter switch has been toggled, so update the settings.
        """
        if key.startswith("doc:"):
            self.buildOpts["settings"].setValue(key[4:], state)
            self._setTreeItemMode()
        elif key.startswith("root:"):
            self.buildOpts["settings"].setSkipRoot(key[5:], state)
            self.populateTree()
        return

    ##
    #  Internal Functions
    ##

    def _setSelectedMode(self, mode):
        """Set the mode for the selected items.
        """
        bSettings = self.buildOpts["settings"]

        for item in self.optTree.selectedItems():
            if not isinstance(item, QTreeWidgetItem):
                continue

            tHandle = item.data(self.C_DATA, self.D_HANDLE)
            isFile = item.data(self.C_DATA, self.D_FILE)
            if isFile:
                if mode == self.F_FILTERED:
                    bSettings.setFiltered(tHandle)
                elif mode == self.F_INCLUDED:
                    bSettings.setIncluded(tHandle)
                elif mode == self.F_EXCLUDED:
                    bSettings.setExcluded(tHandle)

        self._setTreeItemMode()

        return

    def _setTreeItemMode(self):
        """Update the filtered mode icon on all items.
        """
        filtered = self.buildOpts["settings"].checkItemFilter(self.theProject)
        for tHandle, item in self._treeMap.items():
            allow, mode = filtered.get(tHandle, (False, FilterMode.UNKNOWN))
            if mode == FilterMode.INCLUDED:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_INCLUDED][1])
            elif mode == FilterMode.EXCLUDED:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_EXCLUDED][1])
            elif mode == FilterMode.FILTERED and allow:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_FILTERED][1])
            else:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_NONE][1])
        return

# END Class GuiBuildFilterTab


class GuiBuildHeadingsTab(QWidget):

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        return

# END Class GuiBuildHeadingsTab


class GuiBuildFormatTab(QWidget):

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        return

# END Class GuiBuildFormatTab


class GuiBuildContentTab(QWidget):

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        return

# END Class GuiBuildContentTab


class GuiBuildHTMLTab(QWidget):

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        return

# END Class GuiBuildHTMLTab


class GuiBuildMarkdownTab(QWidget):

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        return

# END Class GuiBuildMarkdownTab


class GuiBuildODTTab(QWidget):

    def __init__(self, buildMain):
        super().__init__(parent=buildMain)

        return

# END Class GuiBuildODTTab
