import datetime
import subprocess
import tkinter
from enum import Enum
from tkinter import filedialog, EXTENDED
from typing import Callable, List

from charm_runner.db import DB
from charm_runner.project import Project


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
        self.projects = {}

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
            width=20,
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
        self.main.bind("<Return>", self.run_in_pycharm)

    def update_listbox(self):
        self.projects = {}
        self.listbox.delete(0, tkinter.END)
        for i, project in enumerate(self.db.get_all_projects()):
            self.listbox.insert(i, project.name)
            self.listbox.itemconfig(
                i,
                bg=Colors.bg_listbox
                if datetime.datetime.now() - project.last_opened
                > datetime.timedelta(days=3)
                else Colors.highlighted,
                foreground=Colors.bg_default,
                selectbackground=Colors.selected,
            )
            self.projects[project.name] = project

    # BUTTONS

    def init_buttons(self):
        self.button_frame = tkinter.Frame(
            self.main, bg=Colors.bg_default, bd=0
        )
        self.button_frame.grid(column=1, row=0, sticky=tkinter.N)
        self.buttons = []
        self.create_button("Add folder", self.add_project)
        self.create_button("Delete", self.delete_from_db)
        self.create_button("Run", self.run_in_pycharm)
        self.create_button("Exit", self.main.destroy)

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
        button.grid(column=0, row=len(self.buttons))
        self.buttons.append(button)

    # CALLS

    def run_in_pycharm(self, *args):
        projects = self.get_selected_projects()
        args = []
        for project in projects:
            args.append(project.path)
            self.db.update_project(project)
        subprocess.Popen(["pycharm", *args])
        self.main.destroy()

    def delete_from_db(self, *args):
        projects = self.get_selected_projects()
        for project in projects:
            self.db.delete_project(project)
        self.update_listbox()

    def add_project(self):
        directory = filedialog.askdirectory(initialdir="~/Projects")
        if isinstance(directory, str):
            project = Project(
                name=directory.split("/")[-1],
                path=directory,
                last_opened=datetime.datetime.now(),
            )
            self.db.add_project(project)
            self.update_listbox()

    # HELPERS

    def get_selected_projects(self) -> List[Project]:
        return [
            self.projects[self.listbox.get(i)]
            for i in self.listbox.curselection()
        ]

    # RUN

    @classmethod
    def run(cls):
        App()


if __name__ == "__main__":
    App()
