import datetime
import subprocess
import tkinter
import venv
from enum import Enum
from pathlib import Path
from tkinter import filedialog, EXTENDED
from typing import Callable, List

from cookiecutter.main import cookiecutter

from code_runner.config import IDE_COMMANDS, PROJECTS_PATH, COOKIECUTTER
from code_runner.db import DB
from code_runner.project import Project


class Colors(str, Enum):
    bg_default = "#282828"
    bg_button = "#3c3836"
    fg_button = "#a89984"
    bg_listbox = "#bdae93"
    highlighted = "#ebdbb2"
    selected = "#fabd2f"


class App:
    def __init__(self):
        self.db = DB()
        self.projects = []

        self.main = tkinter.Tk()
        self.main.attributes("-type", "dialog")
        self.main.configure(
            bg=Colors.bg_default,
            highlightbackground=Colors.bg_default,
            border=0,
        )

        self.main.title("Choose Projects")

        self.init_listbox()
        self.init_buttons()

        self.main.mainloop()

    # LISTBOX

    def init_listbox(self):
        frame = tkinter.Frame(
            self.main,
        )
        frame.grid(column=0, row=0)

        self.listbox = tkinter.Listbox(
            frame,
            selectmode=EXTENDED,
            # width=50,
            height=15,
            font=("Roboto", 18),
            highlightbackground=Colors.bg_listbox,
            background=Colors.bg_listbox,
            bd=0,
        )

        self.listbox.grid(column=0, row=0, columnspan=1)
        self.update_listbox()

        self.main.bind("<Delete>", self.delete_from_db)
        self.main.bind("<Escape>", lambda e: self.main.destroy())
        self.main.bind("<Return>", self.run_in_ide)

    def update_listbox(self):
        self.projects = []
        self.listbox.delete(0, tkinter.END)
        projects = self.db.get_all_projects()
        project_names = [p.name for p in projects]
        len_max = 15
        for i, project in enumerate(projects):
            name = (
                f"{project.name} ({project.path})"
                if project_names.count(project.name) > 1
                else project.name
            )
            self.listbox.insert(i, name)
            self.listbox.itemconfig(
                i,
                bg=Colors.bg_listbox
                if datetime.datetime.now() - project.last_opened
                > datetime.timedelta(days=3)
                else Colors.highlighted,
                foreground=Colors.bg_default,
                selectbackground=Colors.selected,
            )
            self.projects.append(project)
            if len(name) > len_max:
                len_max = len(name)
        self.listbox.configure(width=len_max)

    # BUTTONS

    def init_buttons(self):
        self.button_frame = tkinter.Frame(
            self.main, bg=Colors.bg_default, bd=0
        )
        self.button_frame.grid(column=1, row=0, sticky=tkinter.N)

        self.init_ide_menu()

        self.buttons = []
        self.create_button("Add", self.add_project)
        self.create_button("Create", self.create_project)
        self.create_button("Delete", self.delete_from_db)
        self.create_button("Run", self.run_in_ide)
        self.create_button("Exit", self.main.destroy)

    def init_ide_menu(self):
        values = IDE_COMMANDS
        self.ide = tkinter.StringVar()
        self.ide.set(values[0])
        ide_menu = tkinter.OptionMenu(
            self.button_frame,
            self.ide,
            *values,
        )
        ide_menu.configure(
            bg=Colors.bg_button,
            foreground=Colors.fg_button,
            highlightbackground=Colors.bg_default,
            activebackground=Colors.selected,
            activeforeground=Colors.bg_default,
            bd=0,
            width=10,
            font=("Roboto", 16),
        )
        ide_menu.grid(column=0, row=0)

    def create_button(self, text: str, command: Callable):
        button = tkinter.Button(
            self.button_frame,
            text=text,
            bg=Colors.bg_button,
            foreground=Colors.fg_button,
            highlightbackground=Colors.bg_default,
            activebackground=Colors.selected,
            activeforeground=Colors.bg_default,
            bd=0,
            width=10,
            font=("Roboto", 16),
            command=command,
        )
        button.grid(column=0, row=len(self.buttons) + 1)
        self.buttons.append(button)

    # CALLS

    def run_in_ide(self, *args):
        projects = self.get_selected_projects()
        arguments = []
        for project in projects:
            arguments.append(project.path)
            self.db.update_project(project)
        subprocess.Popen([self.ide.get(), *arguments])
        self.main.destroy()

    def delete_from_db(self, *args):
        projects = self.get_selected_projects()
        for project in projects:
            self.db.delete_project(project)
        self.update_listbox()

    def add_project(self):
        directory = filedialog.askdirectory(initialdir=PROJECTS_PATH)
        if isinstance(directory, str) and directory:
            project = Project(
                name=Path(directory).name,
                path=directory,
                last_opened=datetime.datetime.now(),
            )
            self.db.add_project(project)
            self.update_listbox()

    def create_project(self):
        directory = filedialog.askdirectory(initialdir=PROJECTS_PATH)
        if isinstance(directory, str):
            dir_path = Path(directory)
            project_name = dir_path.name
            output_dir = dir_path.parent.absolute()
            cookiecutter(
                COOKIECUTTER,
                no_input=True,
                output_dir=str(output_dir),
                extra_context={"project_name": project_name},
            )
            venv.create(dir_path.absolute() / "venv", with_pip=True)
            project = Project(
                name=project_name,
                path=directory,
                last_opened=datetime.datetime.now(),
            )
            self.db.add_project(project)
            self.update_listbox()

    # HELPERS

    def get_selected_projects(self) -> List[Project]:
        return [self.projects[i] for i in self.listbox.curselection()]

    # RUN

    @classmethod
    def run(cls):
        App()


if __name__ == "__main__":
    App()
