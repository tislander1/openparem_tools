from PySide6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QHBoxLayout, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from parse_local_materials_and_project_file import MaterialFileIO
import sys

material_file_dict = {}

def populate_tree(parent, data):
    if isinstance(data, dict):
        for k, v in data.items():
            child = QTreeWidgetItem([str(k)])
            child.setFlags(child.flags() | Qt.ItemIsEditable)
            parent.addChild(child)
            populate_tree(child, v)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            child = QTreeWidgetItem([f"[{idx}]"])
            child.setFlags(child.flags() | Qt.ItemIsEditable)
            parent.addChild(child)
            populate_tree(child, item)
    else:
        child = QTreeWidgetItem([str(data)])
        child.setFlags(child.flags() | Qt.ItemIsEditable)
        parent.addChild(child)


def tree_to_dict(item):
    if item.childCount() == 0:
        return item.text(0)
    is_list = all(child.text(0).startswith('[') and child.text(0).endswith(']') for child in [item.child(i) for i in range(item.childCount())])
    if is_list:
        return [tree_to_dict(item.child(i)) for i in range(item.childCount())]
    else:
        d = {}
        for i in range(item.childCount()):
            key = item.child(i).text(0)
            value = tree_to_dict(item.child(i))
            d[key] = value
        return d

def get_material_file_dict_from_tree(tree):
    result = {}
    for i in range(tree.topLevelItemCount()):
        mat_item = tree.topLevelItem(i)
        result[mat_item.text(0)] = tree_to_dict(mat_item)
    return result

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Material/Project Editor")
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        # Tab 1: Project File (blank for now)
        tab1 = QWidget()
        tab1.setLayout(QVBoxLayout())
        tab1.layout().addWidget(QLabel("Project File Editor (coming soon)"))
        # Tab 2: Material File (QTreeWidget)
        tab2 = QWidget()
        tab2.setLayout(QVBoxLayout())
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key/Index"])
        self.tree.setEditTriggers(QTreeWidget.AllEditTriggers)
        for mat_name, mat_data in material_file_dict.items():
            mat_item = QTreeWidgetItem([mat_name])
            mat_item.setFlags(mat_item.flags() | Qt.ItemIsEditable)
            self.tree.addTopLevelItem(mat_item)
            populate_tree(mat_item, mat_data)
        tab2.layout().addWidget(self.tree)

        # Add/Remove/Save buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Node")
        remove_btn = QPushButton("Remove Node")
        save_as_btn = QPushButton("Save As")
        load_btn = QPushButton("Load")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(save_as_btn)
        btn_layout.addWidget(load_btn)
        tab2.layout().addLayout(btn_layout)

        add_btn.clicked.connect(self.add_node)
        remove_btn.clicked.connect(self.remove_node)
        save_as_btn.clicked.connect(self.save_materials_as)
        load_btn.clicked.connect(self.load_materials)

        # Add tabs
        tabs.addTab(tab1, "Project File")
        tabs.addTab(tab2, "Material File")
        layout.addWidget(tabs)

        self.material_file_path = "global_materials_out.txt"  # Default path

    def add_node(self):
        selected = self.tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a node to add a child to.")
            return
        child = QTreeWidgetItem(["new_key"])
        child.setFlags(child.flags() | Qt.ItemIsEditable)
        selected.addChild(child)
        value_child = QTreeWidgetItem(["value"])
        value_child.setFlags(value_child.flags() | Qt.ItemIsEditable)
        child.addChild(value_child)
        selected.setExpanded(True)

    def remove_node(self):
        selected = self.tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a node to remove.")
            return
        parent = selected.parent()
        if parent:
            parent.removeChild(selected)
        else:
            idx = self.tree.indexOfTopLevelItem(selected)
            self.tree.takeTopLevelItem(idx)

    def save_materials(self):
        mfio = MaterialFileIO()
        material_dict = get_material_file_dict_from_tree(self.tree)
        mfio.write_material_file(material_dict, self.material_file_path)
        QMessageBox.information(self, "Saved", f"Materials saved to {self.material_file_path}")

    def save_materials_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Material Files (*.txt);;All Files (*)")
        if file_path:
            self.material_file_path = file_path
            self.save_materials()

    def load_materials(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load", "", "Material Files (*.txt);;All Files (*)")
        if file_path:
            mfio = MaterialFileIO()
            try:
                material_dict = mfio.read_material_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
                return
            self.tree.clear()
            for mat_name, mat_data in material_dict.items():
                mat_item = QTreeWidgetItem([mat_name])
                mat_item.setFlags(mat_item.flags() | Qt.ItemIsEditable)
                self.tree.addTopLevelItem(mat_item)
                populate_tree(mat_item, mat_data)
            QMessageBox.information(self, "Loaded", f"Loaded materials from {file_path}")
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())