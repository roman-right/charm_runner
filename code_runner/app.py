import subprocess
import sys
import venv
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QInputDialog,
    QWidget,
    QLabel,
    QFileDialog,
    QAbstractItemView,
    QHeaderView,
)
from cookiecutter.main import cookiecutter

from code_runner.config import IDE_COMMANDS, COOKIECUTTER
from code_runner.db import DB
from code_runner.project import Project, Category


class ProjectManager(QDialog):
    def __init__(self):
        super().__init__()

        self.db = DB()
        self.projects = {}
        self.categories = []

        self.table_headers = ["Name", "Path", "Days from last opened"]

        self.setWindowTitle("Project Manager")
        self.setLayout(QHBoxLayout())

        # Left section - Tabs for project categories
        wrapper = QWidget()
        wrapper.setFixedWidth(1200)
        left_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.rerender_table)
        left_layout.addWidget(self.tabs)
        wrapper.setLayout(left_layout)
        self.layout().addWidget(wrapper)

        # Add example categories
        self.rerender_categories()

        # Right section - Controls (IDE selector, buttons)
        right_layout = QVBoxLayout()

        self.ide_selector = QComboBox()
        for ide_command in IDE_COMMANDS:
            self.ide_selector.addItem(ide_command)
        right_layout.addWidget(self.ide_selector)

        # add seperator
        right_layout.addWidget(QLabel("Categories"))
        self.add_button("Add", self.show_add_category_dialog, right_layout)
        self.add_button("Delete", self.delete_category, right_layout)

        # add seperator
        right_layout.addWidget(QLabel("Projects"))

        self.add_button("Add", self.show_add_project_dialog, right_layout)
        self.add_button(
            "Edit", self.show_edit_project_dialog, parent_layout=right_layout
        )
        self.add_button(
            "Create",
            self.show_create_project_dialog,
            parent_layout=right_layout,
        )
        self.add_button(
            "Delete", self.delete_projects, parent_layout=right_layout
        )
        self.add_button("Run", self.run_projects, parent_layout=right_layout)
        self.add_button("Exit", self.close, right_layout)

        self.layout().addLayout(right_layout)

        # self.update_project_list()
        self.rerender_table()

    # HELPERS

    def add_button(self, label, callback=None, parent_layout=None):
        button = QPushButton(label)
        if callback:
            button.clicked.connect(callback)
        if parent_layout:
            parent_layout.addWidget(button)

    def get_current_tab_name(self):
        current_tab_index = self.tabs.currentIndex()
        current_tab_name = self.tabs.tabText(current_tab_index)
        return current_tab_name

    def get_selected_projects(self):
        selected_table = self.tabs.currentWidget()
        selected_items = selected_table.selectedItems()

        if not selected_items:
            return []

        projects = []
        for item in selected_items:
            row = item.row()
            project_name = selected_table.item(row, 0).text()
            project_path = selected_table.item(row, 1).text()
            project = Project(
                name=project_name,
                path=project_path,
                last_opened=datetime.now(),
                category=Category(id=None, name=self.get_current_tab_name()),
            )
            projects.append(project)
        return projects

    # RENDERS

    def render_category(self, name):
        table = self.create_table()
        self.tabs.addTab(table, name)
        self.rerender_table()

    def update_categories(self):
        self.categories = self.db.get_all_categories()

    def rerender_categories(self):
        self.tabs.clear()
        self.update_categories()
        for category in self.categories:
            self.render_category(category.name)

    def create_table(self):
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(self.table_headers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        table.verticalHeader().setVisible(False)

        # Make cell non-editable
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Add double click event
        table.doubleClicked.connect(self.run_projects)
        return table

    def rerender_table(self):
        selected_table = self.tabs.currentWidget()
        if selected_table is not None:
            selected_table.clear()

            projects = self.db.get_all_projects(
                category_name=self.get_current_tab_name()
            )

            updated_data = [
                [
                    project.name,
                    project.path,
                    str((datetime.now() - project.last_opened).days),
                ]
                for project in projects.values()
            ]

            selected_table.setRowCount(len(updated_data))
            selected_table.setHorizontalHeaderLabels(self.table_headers)
            for row, data_row in enumerate(updated_data):
                for col, data in enumerate(data_row):
                    selected_table.setItem(row, col, QTableWidgetItem(data))

    def show_add_project_dialog(self):
        add_dialog = QDialog(self)
        add_dialog.setWindowTitle("Add Project")
        add_dialog.setLayout(QVBoxLayout())

        project_name_label = QLabel("Project Name:")
        project_name_edit = QLineEdit()
        add_dialog.layout().addWidget(project_name_label)
        add_dialog.layout().addWidget(project_name_edit)

        project_path_label = QLabel("Project Path:")
        project_path_edit = QLineEdit()
        add_dialog.layout().addWidget(project_path_label)
        add_dialog.layout().addWidget(project_path_edit)

        browse_button = QPushButton("Browse")
        add_dialog.layout().addWidget(browse_button)

        def browse_directory():
            directory = QFileDialog.getExistingDirectory(
                self, "Select Project Directory", "/home/ro/Projects"
            )
            project_path_edit.setText(directory)

        browse_button.clicked.connect(browse_directory)

        category_label = QLabel("Category:")
        category_combo = QComboBox()

        categories = self.db.get_all_categories()

        for category in categories:
            category_combo.addItem(category.name)

        # Select current category
        category_combo.setCurrentText(self.get_current_tab_name())

        add_dialog.layout().addWidget(category_label)
        add_dialog.layout().addWidget(category_combo)

        add_button = QPushButton("Add")

        def add_project():
            category = Category(id=None, name=category_combo.currentText())
            project_name = (
                project_name_edit.text()
                or project_path_edit.text().split("/")[-1]
            )
            project = Project(
                name=project_name,
                path=project_path_edit.text(),
                last_opened=datetime.now(),
                category=category,
            )
            self.db.add_project(project)
            add_dialog.accept()

        add_button.clicked.connect(add_project)

        add_dialog.layout().addWidget(add_button)

        add_dialog.exec_()

        self.rerender_table()

    def show_create_project_dialog(self):
        create_dialog = QDialog(self)
        create_dialog.setWindowTitle("Create Project")
        create_dialog.setLayout(QVBoxLayout())

        project_name_label = QLabel("Project Name:")
        project_name_edit = QLineEdit()
        create_dialog.layout().addWidget(project_name_label)
        create_dialog.layout().addWidget(project_name_edit)

        project_path_label = QLabel("Project Path:")
        project_path_edit = QLineEdit()
        create_dialog.layout().addWidget(project_path_label)
        create_dialog.layout().addWidget(project_path_edit)

        browse_button = QPushButton("Browse")
        create_dialog.layout().addWidget(browse_button)

        def browse_directory():
            directory = QFileDialog.getExistingDirectory(
                self, "Select Project Directory", "/home/ro/Projects"
            )
            project_path_edit.setText(directory)

        browse_button.clicked.connect(browse_directory)

        category_label = QLabel("Category:")
        category_combo = QComboBox()

        categories = self.db.get_all_categories()

        for category in categories:
            category_combo.addItem(category.name)

        create_dialog.layout().addWidget(category_label)
        create_dialog.layout().addWidget(category_combo)

        create_button = QPushButton("Create")

        def create_project():
            path = Path(project_path_edit.text())
            cookiecutter(
                COOKIECUTTER,
                no_input=True,
                output_dir=str(project_path_edit.text()),
                extra_context={"project_name": project_name_edit.text()},
                overwrite_if_exists=True,
            )
            venv.create(path.absolute() / "venv", with_pip=True)
            category = Category(id=None, name=category_combo.currentText())
            project = Project(
                name=project_name_edit.text(),
                path=str(path.absolute()),
                last_opened=datetime.now(),
                category=category,
            )
            self.db.add_project(project)
            create_dialog.accept()

        create_button.clicked.connect(create_project)

        create_dialog.layout().addWidget(create_button)

        create_dialog.exec_()

        self.rerender_table()

    def show_edit_project_dialog(self):
        selected_table = self.tabs.currentWidget()
        selected_items = selected_table.selectedItems()

        if not selected_items:
            return

        row = selected_items[0].row()

        project_name = selected_table.item(row, 0).text()
        project_path = selected_table.item(row, 1).text()

        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle("Edit Project")
        edit_dialog.setLayout(QVBoxLayout())

        project_name_label = QLabel("Project Name:")
        project_name_edit = QLineEdit(project_name)
        edit_dialog.layout().addWidget(project_name_label)
        edit_dialog.layout().addWidget(project_name_edit)

        project_path_label = QLabel("Project Path:")
        project_path_edit = QLineEdit(project_path)
        edit_dialog.layout().addWidget(project_path_label)
        edit_dialog.layout().addWidget(project_path_edit)

        browse_button = QPushButton("Browse")
        edit_dialog.layout().addWidget(browse_button)

        def browse_directory():
            directory = QFileDialog.getExistingDirectory(
                self, "Select Project Directory", "/home/ro/Projects"
            )
            project_path_edit.setText(directory)

        browse_button.clicked.connect(browse_directory)

        category_label = QLabel("Category:")
        category_combo = QComboBox()

        for i in range(self.tabs.count()):
            category_combo.addItem(self.tabs.tabText(i))

        current_category = self.get_current_tab_name()
        category_combo.setCurrentText(current_category)

        edit_dialog.layout().addWidget(category_label)
        edit_dialog.layout().addWidget(category_combo)

        save_button = QPushButton("Save")
        edit_dialog.layout().addWidget(save_button)

        def save_changes():
            project = Project(
                name=project_name_edit.text(),
                path=project_path_edit.text(),
                last_opened=datetime.now(),
                category=Category(id=None, name=category_combo.currentText()),
            )
            self.db.update_project(project)

            edit_dialog.close()

        save_button.clicked.connect(save_changes)

        edit_dialog.exec_()

        self.rerender_table()

    def show_add_category_dialog(self):
        category_name, ok = QInputDialog.getText(
            self, "Add Category", "Category Name:"
        )
        if ok:
            self.db.add_category_if_not_exists(
                Category(id=None, name=category_name)
            )
            self.rerender_categories()

    # Button press handlers

    def delete_category(self):
        category_name = self.get_current_tab_name()
        category = self.db.get_category_by_name(category_name)
        self.db.delete_category_and_all_projects(category)
        self.rerender_categories()

    def run_projects(self):
        projects = self.get_selected_projects()
        arguments = []
        for project in projects:
            arguments.append(project.path)
            self.db.update_project(project)
        selected_ide = self.ide_selector.currentText()
        subprocess.Popen([selected_ide, *arguments])
        self.close()

    def delete_projects(self):
        projects = self.get_selected_projects()
        for project in projects:
            self.db.delete_project(project)
        self.rerender_table()


def run():
    app = QApplication(sys.argv)
    # app.setStyleSheet(open("style.qss").read())
    app.setStyleSheet(
        """
    QWidget {
        font-family: "Roboto";
        font-size: 24px;
    }
    """
    )
    project_manager = ProjectManager()
    project_manager.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
