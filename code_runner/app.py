import subprocess
import venv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import gi
from cookiecutter.main import cookiecutter

from code_runner.config import IDE_COMMANDS, COOKIECUTTER
from code_runner.db import DB
from code_runner.project import Project

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa


class Handler:
    def __init__(self, builder):
        self.db = DB()

        self.projects: Dict[str, Project] = {}

        self.gtk_projects_store = builder.get_object("projects_store")
        self.gtk_selection = builder.get_object("projects_view_selection")

        self.choose_dir_window = builder.get_object("choose_dir")
        self.ide_menu = builder.get_object("ide_menu")
        self.ide_store = builder.get_object("ide_store")
        self.ide = builder.get_object("ide_store")

        self.update_projects_list()
        self.set_ide_menu()

    # VIEW

    def update_projects_list(self):
        self.gtk_projects_store.clear()
        self.projects = self.db.get_all_projects()
        for k, project in self.projects.items():
            self.gtk_projects_store.append(
                [
                    project.name,
                    project.path,
                    f"{(datetime.now() - project.last_opened).days}",
                ]
            )

    def set_ide_menu(self):
        for ide_command in IDE_COMMANDS:
            self.ide_store.append([ide_command])
        self.ide_menu.set_active(0)

    # BUTTONS HANDLERS

    def add_project(self, *args):
        self.choose_dir_window.run()
        self.choose_dir_window.hide()
        directory = self.choose_dir_window.get_filename()
        if directory:
            project = Project(
                name=Path(directory).name,
                path=directory,
                last_opened=datetime.now(),
            )
            self.db.add_project(project)
            self.update_projects_list()

    def create_project(self, *args):
        self.choose_dir_window.run()
        self.choose_dir_window.hide()
        directory = self.choose_dir_window.get_filename()
        if (
            directory
            and Path(directory).is_dir()
            and not any(Path(directory).iterdir())
        ):
            dir_path = Path(directory)
            project_name = dir_path.name
            output_dir = dir_path.parent.absolute()
            cookiecutter(
                COOKIECUTTER,
                no_input=True,
                output_dir=str(output_dir),
                extra_context={"project_name": project_name},
                overwrite_if_exists=True,
            )
            venv.create(dir_path.absolute() / "venv", with_pip=True)
            project = Project(
                name=project_name,
                path=directory,
                last_opened=datetime.now(),
            )
            self.db.add_project(project)
            self.update_projects_list()

    def run_projects(self, *args):
        projects = self.get_selected_projects()
        arguments = []
        for project in projects:
            arguments.append(project.path)
            self.db.update_project(project)
        subprocess.Popen(
            [IDE_COMMANDS[self.ide_menu.get_active()], *arguments]
        )
        self.exit()

    def delete_projects(self, *args):
        projects = self.get_selected_projects()
        for project in projects:
            self.db.delete_project(project)
        self.update_projects_list()

    def exit(self, *args):
        Gtk.main_quit()

    # KEY PRESS

    def key_press(self, *args):
        print(args)

    # COMMON

    def get_selected_projects(self) -> List[Project]:
        model, path_list = self.gtk_selection.get_selected_rows()
        res = []
        for path in path_list:
            tree_iter = model.get_iter(path)
            path = model.get_value(tree_iter, 1)
            res.append(self.projects[path])
        return res


def run():
    builder = Gtk.Builder()
    builder.add_from_file(
        str(Path(__file__).parent / "templates" / "main.xml")
    )

    builder.connect_signals(Handler(builder))

    window = builder.get_object("main")
    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    run()
