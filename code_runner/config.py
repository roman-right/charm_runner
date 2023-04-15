from pathlib import Path

import yaml

BASE_DIR = Path.home() / ".config" / "code_runner"
DB_PATH = BASE_DIR / "data.db"
CONFIG_PATH = BASE_DIR / "config.yaml"

config_src = {}
if CONFIG_PATH.is_file():
    with CONFIG_PATH.open() as f:
        config_src = yaml.safe_load(f.read())

IDE_COMMANDS = config_src.get("IDE_COMMANDS", ["pycharm"])
PROJECTS_PATH = str(
    Path(config_src.get("PROJECTS_PATH", Path.home() / "Projects"))
)
COOKIECUTTER = config_src.get(
    "COOKIECUTTER", "https://github.com/roman-right/py-template"
)
