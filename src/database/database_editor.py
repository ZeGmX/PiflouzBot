from my_database import ElementDict, ElementList, db
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QKeyEvent
from PyQt6.QtWidgets import QApplication, QDialog, QMenu, QTreeWidgetItem
from PyQt6.uic import loadUi
import sys


class ItemType:
    DICT = 1
    LIST = 2
    LEAF = 3


class KeyId:
    """
    Used to generate unique keys when creating new elements in the database editor
    """

    last_id = 0

    @staticmethod
    def next_id():
        KeyId.last_id += 1
        return KeyId.last_id


class DatabaseHistory:
    """
    Used to keep track of the database history and allow undo/redo operations
    """

    def __init__(self, initial_db, max_size=100):
        self.previous = []  # stack of previous databases (0: oldest, -1: newest)
        self.current = initial_db
        self.next = []  # stack of databases that were undone (0: newest = last to redo, -1: oldest = first to redo)
        self.max_size = max_size

    def add(self, new_db):
        self.previous.append(self.current)
        self.next = []
        self.current = new_db
        if len(self.previous) > self.max_size:
            self.previous.pop(0)

    def undo(self):
        if len(self.previous) > 0:
            prev_db = self.previous.pop()
            self.next.append(self.current)
            self.current = prev_db

    def redo(self):
        if len(self.next) > 0:
            next_db = self.next.pop()
            self.previous.append(self.current)
            self.current = next_db


class MainWindow(QDialog):
    alt_key_pressed = False
    can_save = True  # Used to prevent saving the database too often when adding new elements

    def __init__(self):
        super(MainWindow, self).__init__()

        loadUi("src/database/assets/mainwindow.ui", self)

        self.show()
        self.print_db()

        self.treeWidget.itemChanged.connect(self.save_database)
        self.treeWidget.itemCollapsed.connect(self.on_item_collapse)
        self.treeWidget.itemExpanded.connect(self.on_item_expand)

        self.treeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.prepare_context_menu)

        self.reloadButton.clicked.connect(self.reload_database)
        self.undoButton.clicked.connect(self.on_undo)
        self.redoButton.clicked.connect(self.on_redo)

        self.history = DatabaseHistory(self.get_current_db())
        self.update_undo_redo_buttons()

    ### Quick expand/collapse with Alt key

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """
        Override the keyPressEvent method to detect the Alt key press event

        Parameters
        ----------
        event : QKeyEvent | None
            contains information about the key press event
        """
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Alt:
            self.alt_key_pressed = True

    def keyReleaseEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """
        Override the keyReleaseEvent method to detect the Alt key release event

        Parameters
        ----------
        event : QKeyEvent | None
            Contains information about the key release event
        """
        super().keyReleaseEvent(event)
        if event.key() == Qt.Key.Key_Alt:
            self.alt_key_pressed = False

    def on_item_collapse(self, item):
        """
        Called when an item is collapsed. If the Alt key is pressed, collapses all the children of the item

        Parameters
        ----------
        item : QTreeWidgetItem
        """
        if not self.alt_key_pressed: return
        if item.childCount() == 0: return

        for i in range(1, item.childCount() - 1):
            item.child(i).setExpanded(False)

    def on_item_expand(self, item):
        """
        Called when an item is expanded. If the Alt key is pressed, expands all the children of the item

        Parameters
        ----------
        item : QTreeWidgetItem
        """
        if not self.alt_key_pressed: return
        if item.childCount() == 0: return

        for i in range(1, item.childCount() - 1):
            item.child(i).setExpanded(True)

    ### Undo/Redo

    def on_undo(self):
        """
        Called when the undo button is clicked or when pressing ctrl + Z. Reverts the database to the previous state
        """
        self.history.undo()
        self.set_db(self.history.current)
        self.print_db()
        self.update_undo_redo_buttons()

    def on_redo(self):
        """
        Called when the redo button is clicked or when pressing ctrl + shift + Z. Reverts the database to the next state
        """
        self.history.redo()
        self.set_db(self.history.current)
        self.print_db()
        self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        """
        Enables or disables the undo and redo buttons depending on the history state
        """
        self.undoButton.setEnabled(len(self.history.previous) > 0)
        self.redoButton.setEnabled(len(self.history.next) > 0)

    ### Right click context menu

    def prepare_context_menu(self, pos):
        """
        Generates the right click context menu when clicking on an item in the tree view

        Parameters
        ----------
        pos : QPoint
            Position of the mouse click
        """
        item: QTreeWidgetItem = self.treeWidget.itemAt(pos)

        if item is None: return

        menu = QMenu(self)

        # Clicking an actual item
        if item.text(0) not in ["{", "[", "}", "]"]:
            if item.childCount() == 0:  # Leaf value
                action = QAction("Delete associated key", self)
                action.triggered.connect(lambda: self.delete_item(item.parent()))
                menu.addAction(action)

            else:  # Non-leaf item (key, associated to either a dict, list or leaf item)
                action = QAction("Delete item", self)
                action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(action)

                if item.childCount() > 2:  # Not associated to a leaf item (so either a dict or a list)
                    action = QAction("Empty", self)
                    action.triggered.connect(lambda: self.clear_values(item))
                    menu.addAction(action)

        # Clicking a dict key
        if item.parent() is None or item.parent().child(0).text(0) == "{":
            menu_add_after = QMenu("Add key/value pair", self)
            menu.addMenu(menu_add_after)

            item_before = item
            if item.parent() is None and self.treeWidget.indexOfTopLevelItem(item) == self.treeWidget.topLevelItemCount() - 1:
                item_before = self.treeWidget.topLevelItem(self.treeWidget.topLevelItemCount() - 2)
            elif item.parent() is not None and item.parent().indexOfChild(item) == item.parent().childCount() - 1:
                item_before = item.parent().child(item.parent().childCount() - 2)

            action = QAction("Leaf element", self)
            action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.LEAF, item_before))
            menu_add_after.addAction(action)

            action = QAction("Dictionary", self)
            action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.DICT, item_before))
            menu_add_after.addAction(action)

            action = QAction("List", self)
            action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.LIST, item_before))
            menu_add_after.addAction(action)

        # Clicking a list key
        if item.parent() is not None and item.parent().child(0).text(0) == "[":
            menu_add_after = QMenu("Add value after", self)
            menu_add_before = QMenu("Add value before", self)

            if item.parent().indexOfChild(item) > 0:
                item_before = item.parent().child(item.parent().indexOfChild(item) - 1)
                menu.addMenu(menu_add_before)

                action = QAction("Leaf element", self)
                action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.LEAF, item_before))
                menu_add_before.addAction(action)

                action = QAction("Dictionary", self)
                action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.DICT, item_before))
                menu_add_before.addAction(action)

                action = QAction("List", self)
                action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.LIST, item_before))
                menu_add_before.addAction(action)

            if (item.parent().indexOfChild(item) < item.parent().childCount() - 1):
                menu.addMenu(menu_add_after)

                action = QAction("Leaf element", self)
                action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.LEAF))
                menu_add_after.addAction(action)

                action = QAction("Dictionary", self)
                action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.DICT))
                menu_add_after.addAction(action)

                action = QAction("List", self)
                action.triggered.connect(lambda: self.add_key_value_pair(item, ItemType.LIST))
                menu_add_after.addAction(action)

        menu.exec(self.treeWidget.mapToGlobal(pos))

    def delete_item(self, item):
        """
        Deletes an item from the tree view and database

        Parameters
        ----------
        item : QTreeWidgetItem
            The item to delete
        """
        parent = item.parent()
        if parent is None:  # Top level item
            self.treeWidget.takeTopLevelItem(self.treeWidget.indexOfTopLevelItem(item))
        else:
            parent.removeChild(item)
        self.save_database()
        self.history.add(self.get_current_db())
        self.update_undo_redo_buttons()

    def clear_values(self, item):
        """
        Removes all the children of an item (corresponding to a dict or a list) except the opening and closing brackets

        Parameters
        ----------
        item : QTreeWidgetItem
            The item to clear
        """
        for i in range(1, item.childCount() - 1):
            item.removeChild(item.child(1))
        self.save_database()
        self.history.add(self.get_current_db())
        self.update_undo_redo_buttons()

    def add_key_value_pair(self, item, item_type, item_before=None):
        """
        Generates a new key/value pair in the tree view and database

        Parameters
        ----------
        item : QTableWidgetItem
            The item clicked on before opening the context menu
        item_type : ItemType (int)
            What type of pair to add (dict, list or leaf)
        item_before : QTableWidgetItem, optional
            After which item to add the new one, by default `item`
        """
        self.can_save = False
        parent = item.parent()
        if item_before is None:
            item_before = item
        key_item = self.create_tree_item(self.treeWidget if parent is None else parent, f"CHANGE THIS KEY {KeyId.next_id()}", previous=item_before)

        match item_type:
            case ItemType.DICT:
                self.create_tree_item(key_item, "{", editable=False)
                self.create_tree_item(key_item, "}", editable=False)
            case ItemType.LIST:
                self.create_tree_item(key_item, "[", editable=False)
                self.create_tree_item(key_item, "]", editable=False)
            case ItemType.LEAF:
                self.create_tree_item(key_item, "\"CHANGE THIS VALUE\"")

        # Re numbering if we inserted in a list
        if parent is not None and parent.child(0).text(0) == "[":
            for i in range(1, parent.childCount() - 1):
                parent.child(i).setText(0, f"    {i - 1}")

        key_item.setExpanded(True)
        key_item.setSelected(True)
        item.setSelected(False)

        self.can_save = True
        self.save_database()
        self.history.add(self.get_current_db())
        self.update_undo_redo_buttons()

    ### Database handling

    def save_database(self):
        """
        Saves the current visualised database to disk
        """
        if not self.can_save: return

        new_db = self.get_current_db()
        self.set_db(new_db)

    def set_db(self, new_db):
        """
        Changes the current database to a new one

        Parameters
        ----------
        new_db : dict
            the new database
        """
        for key, val in new_db.items():
            db[key] = val

        for key in list(db.keys()):
            if key not in new_db.keys():
                del db[key]

    def get_current_db(self):
        """
        Recovers the dict corresponding the the current visualised database

        Returns
        -------
        dict
            the current database
        """
        new_db = dict()

        for i in range(1, self.treeWidget.topLevelItemCount() - 1):
            item = self.treeWidget.topLevelItem(i)
            key = item.text(0)
            val = self.get_db_key(item)
            new_db[key.strip()] = val

        return new_db

    def get_db_key(self, parent):
        """
        Recovers the sub-database corresponding to a given item

        Parameters
        ----------
        parent : QTreeWidgetItem
            root item of the sub-database

        Returns
        -------
        dict/list/leaf element
            sub-database
        """
        if parent.childCount() == 1:
            return eval(parent.child(0).text(0))

        if parent.child(0).text(0) == "{":
            res = dict()
            for i in range(1, parent.childCount() - 1):
                item = parent.child(i)
                key = item.text(0)
                res[key.strip()] = self.get_db_key(item)
            return res

        if parent.child(0).text(0) == "[":
            res = list()
            for i in range(1, parent.childCount() - 1):
                item = parent.child(i)
                res.append(self.get_db_key(item))
            return res

        raise Exception("Invalid item")

    def reload_database(self):
        """
        Reloads the database from disk and updates the visualisation
        """
        db.is_loaded = False
        db._clear()
        db._load()
        self.print_db()
        self.history.add(self.get_current_db())
        self.update_undo_redo_buttons()

    ### Displaying the database

    def print_db(self):
        """
        Updates the visualisation of the database in the tree view
        """
        self.can_save = False
        self.treeWidget.clear()
        self.treeWidget.setColumnCount(1)

        self.print_db_key(db.to_element(), self.treeWidget)
        self.can_save = True

    def print_db_key(self, sub_db, parent):
        """
        Updates the visualisation of a sub-database in the tree view

        Parameters
        ----------
        sub_db : ElementDict/ElementList/leaf element
            sub-database to visualise
        parent : QTreeWidgetItem
            parent item in the tree view
        """
        if type(sub_db) is ElementDict:
            self.create_tree_item(parent, "{", editable=False)
            for key, val in sub_db.items():
                item = self.create_tree_item(parent, "    " + key)
                self.print_db_key(val, item)
            self.create_tree_item(parent, "}", editable=False)
        elif type(sub_db) is ElementList:
            self.create_tree_item(parent, "[", editable=False)
            for i, val in enumerate(sub_db):
                item = self.create_tree_item(parent, "    " + str(i))
                self.print_db_key(val, item)
            self.create_tree_item(parent, "]", editable=False)
        else:
            self.create_tree_item(parent, item_to_str(sub_db))

    ### Utils

    def create_tree_item(self, parent, text, editable=True, previous=None):
        """
        Miscellaneous method to create a new item in the tree view

        Parameters
        ----------
        parent : QTreeWidgetItem
            Parent item in the tree view. If None, the item is added at the top level
        text : str
            Text to display in the item
        editable : bool, optional
            Whether the text can be edited by the user of not, by default True
        previous : QTreeWidgetItem, optional
            Item in the visualization after which it should be displayed, by default None

        Returns
        -------
        QTreeWidgetItem
            The created item
        """
        if previous is None:
            item = QTreeWidgetItem(parent)
        else:
            item = QTreeWidgetItem(parent, previous)
        item.setText(0, text)
        if editable:
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        return item


def item_to_str(item):
    """
    Wraps a string in quotes if it is a string

    Parameters
    ----------
    item : any

    Returns
    -------
    any (same as input)
    """
    if type(item) is str:
        return f"\"{item}\""
    else:
        return str(item)


def compare_databases(new_db, old_db):
    """
    Checks if the two databases are equivalent

    Parameters
    ----------
    new_db : dict/list/leaf element
        new proposed database
    old_db : ElementDict/ElementList/leaf element
        previous database

    Returns
    -------
    bool
    """
    if type(new_db) is dict:
        if type(old_db) is not ElementDict: return False

        if len(new_db) != len(old_db): return False
        for key in new_db.keys():
            if key not in old_db.keys(): return False
            if not compare_databases(new_db[key], old_db[key]): return False
        return True
    elif type(new_db) is list:
        if type(old_db) is not ElementList: return False

        if len(new_db) != len(old_db): return False
        for i in range(len(new_db)):
            if not compare_databases(new_db[i], old_db[i]): return False
        return True
    else:
        return new_db == old_db


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setWindowTitle("Pibot's Database Editor")
    main_window.setWindowIcon(QIcon("src/database/assets/piflouz.png"))
    app.exec()
