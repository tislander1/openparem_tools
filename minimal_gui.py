from PySide6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QHBoxLayout, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from parse_local_materials_and_project_file import MaterialFileIO, ProjectFileIO
import sys

# Portions of this code were developed with the assistance
# of GitHub Copilot, an AI programming assistant.

material_file_dict = {}
project_file_dict = {}

def populate_tree(parent, data):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                child = QTreeWidgetItem([str(k), ""])
                parent.addChild(child)
                populate_tree(child, v)
            else:
                child = QTreeWidgetItem([str(k), str(v)])
                child.setFlags(child.flags() | Qt.ItemIsEditable)
                parent.addChild(child)
    elif isinstance(data, list):
        for item in data:
            # For lists of values (like duplicate keys in project file)
            if isinstance(item, dict) or isinstance(item, list):
                child = QTreeWidgetItem(["", ""])
                parent.addChild(child)
                populate_tree(child, item)
            else:
                # Use parent's key for duplicate key lists
                child = QTreeWidgetItem([parent.text(0), str(item)])
                child.setFlags(child.flags() | Qt.ItemIsEditable)
                parent.addChild(child)

def tree_to_dict(item):
    # If the item has no children, return its value (column 1)
    if item.childCount() == 0:
        return item.text(1)
    # Gather all keys
    keys = [item.child(i).text(0) for i in range(item.childCount())]
    # If all children are list-like ([0], [1], ...)
    is_list = all(k.startswith('[') and k.endswith(']') for k in keys)
    if is_list:
        return [tree_to_dict(item.child(i)) for i in range(item.childCount())]
    # If there are duplicate keys, store as list
    result = {}
    key_counts = {}
    for key in keys:
        key_counts[key] = key_counts.get(key, 0) + 1
    for i, key in enumerate(keys):
        value = tree_to_dict(item.child(i))
        if key_counts[key] > 1:
            if key not in result:
                result[key] = []
            result[key].append(value)
        else:
            result[key] = value
    return result

def get_dict_from_tree(tree):
    result = {}
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        result[item.text(0)] = tree_to_dict(item)
    return result

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Material/Project Editor")
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # --- Project File Tab ---
        tab1 = QWidget()
        tab1.setLayout(QVBoxLayout())
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels(["Key", "Value"])
        self.project_tree.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        tab1.layout().addWidget(self.project_tree)

        proj_btn_layout = QHBoxLayout()
        proj_add_btn = QPushButton("Add Node")
        proj_remove_btn = QPushButton("Remove Node")
        proj_save_btn = QPushButton("Save As")
        proj_load_btn = QPushButton("Load")
        proj_btn_layout.addWidget(proj_add_btn)
        proj_btn_layout.addWidget(proj_remove_btn)
        proj_btn_layout.addWidget(proj_save_btn)
        proj_btn_layout.addWidget(proj_load_btn)

        tab1.layout().addLayout(proj_btn_layout)

        proj_add_btn.clicked.connect(self.add_project_node)
        proj_remove_btn.clicked.connect(self.remove_project_node)
        proj_load_btn.clicked.connect(self.load_project)
        proj_save_btn.clicked.connect(self.save_project_as)

        # --- Material File Tab ---
        tab2 = QWidget()
        tab2.setLayout(QVBoxLayout())
        self.material_tree = QTreeWidget()
        self.material_tree.setHeaderLabels(["Key", "Value"])
        self.material_tree.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        tab2.layout().addWidget(self.material_tree)

        mat_btn_layout = QHBoxLayout()
        mat_add_btn = QPushButton("Add Node")
        mat_remove_btn = QPushButton("Remove Node")
        mat_save_btn = QPushButton("Save As")
        mat_load_btn = QPushButton("Load")
        mat_btn_layout.addWidget(mat_add_btn)
        mat_btn_layout.addWidget(mat_remove_btn)
        mat_btn_layout.addWidget(mat_save_btn)
        mat_btn_layout.addWidget(mat_load_btn)
        tab2.layout().addLayout(mat_btn_layout)

        mat_add_btn.clicked.connect(self.add_material_node)
        mat_remove_btn.clicked.connect(self.remove_material_node)
        mat_save_btn.clicked.connect(self.save_materials_as)
        mat_load_btn.clicked.connect(self.load_materials)

        tabs.addTab(tab1, "Project File")
        tabs.addTab(tab2, "Material File")
        layout.addWidget(tabs)

    # --- Project File Methods ---

    def add_project_node(self):
        selected = self.project_tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a node to add a child to.")
            return
        child = QTreeWidgetItem(["new_key", "value"])
        child.setFlags(child.flags() | Qt.ItemIsEditable)
        selected.addChild(child)
        selected.setExpanded(True)

    def remove_project_node(self):
        selected = self.project_tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a node to remove.")
            return
        parent = selected.parent()
        if parent:
            parent.removeChild(selected)
        else:
            idx = self.project_tree.indexOfTopLevelItem(selected)
            self.project_tree.takeTopLevelItem(idx)

    def load_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Project Files (*.proj *.txt);;All Files (*)")
        if file_path:
            pfio = ProjectFileIO()
            try:
                project_dict = pfio.read_project_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load project file:\n{e}")
                return
            self.project_tree.clear()
            for k, v in project_dict.items():
                if isinstance(v, (dict, list)):
                    item = QTreeWidgetItem([k, ""])
                    self.project_tree.addTopLevelItem(item)
                    populate_tree(item, v)
                else:
                    item = QTreeWidgetItem([k, str(v)])
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.project_tree.addTopLevelItem(item)
            QMessageBox.information(self, "Loaded", f"Loaded project from {file_path}")

    def save_project_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", "Project Files (*.proj *.txt);;All Files (*)")
        if file_path:
            pfio = ProjectFileIO()
            project_dict = get_dict_from_tree(self.project_tree)
            pfio.write_project_file(project_dict, file_path)
            QMessageBox.information(self, "Saved", f"Project saved to {file_path}")

    # --- Material File Methods ---
    def add_material_node(self):
        selected = self.material_tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a node to add a child to.")
            return
        child = QTreeWidgetItem(["new_key", "value"])
        child.setFlags(child.flags() | Qt.ItemIsEditable)
        selected.addChild(child)
        selected.setExpanded(True)

    def remove_material_node(self):
        selected = self.material_tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a node to remove.")
            return
        parent = selected.parent()
        if parent:
            parent.removeChild(selected)
        else:
            idx = self.material_tree.indexOfTopLevelItem(selected)
            self.material_tree.takeTopLevelItem(idx)

    def save_materials_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Materials As", "", "Material Files (*.txt);;All Files (*)")
        if file_path:
            mfio = MaterialFileIO()
            material_dict = get_dict_from_tree(self.material_tree)
            mfio.write_material_file(material_dict, file_path)
            QMessageBox.information(self, "Saved", f"Materials saved to {file_path}")

    def load_materials(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Materials", "", "Material Files (*.txt);;All Files (*)")
        if file_path:
            mfio = MaterialFileIO()
            try:
                material_dict = mfio.read_material_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
                return
            self.material_tree.clear()
            for mat_name, mat_data in material_dict.items():
                mat_item = QTreeWidgetItem([mat_name, ""])
                self.material_tree.addTopLevelItem(mat_item)
                populate_tree(mat_item, mat_data)
            QMessageBox.information(self, "Loaded", f"Loaded materials from {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())