import shutil
from pathlib import Path

import yaml

BASE_DIR = Path.home() / ".config" / "code_compass"
DB_PATH = BASE_DIR / "data.db"
CONFIG_PATH = BASE_DIR / "config.yaml"
TEMPLATE_CONFIG_PATH = Path(__file__).parent / "config.yaml"


config_src = {}
if not CONFIG_PATH.is_file():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE_CONFIG_PATH, CONFIG_PATH)

with CONFIG_PATH.open() as f:
    config_src = yaml.safe_load(f.read())

IDE_COMMANDS = config_src.get("ide_commands", ["pycharm"])

projects_path = config_src.get("projects_path", Path.home())
if projects_path in ["~", "HOME"]:
    projects_path = Path.home()
else:
    projects_path = Path(projects_path)

PROJECTS_PATH = str(projects_path)
COOKIECUTTER = config_src.get("cookiecutter")
