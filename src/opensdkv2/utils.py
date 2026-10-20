import os
import subprocess
from typing_extensions import TypedDict
from typing import Any
from langchain_core.tools import tool
import yaml


def parse_yaml_target(filepath: str) -> dict:
    if "#" not in filepath:
        return {}
    target = filepath.split("#")
    target_group = target[1].split(".")
    if len(target_group) == 1:
        target_group.append('')

    return {'compile_file': target[0],'target_group': target_group[0], 'target': target_group[1]}

def find_component(component_type: str, component_name: str, yaml_data: Any) -> Any:
    selected_data = yaml_data
    target_data = None
    check = component_name.find("#")
    sym_check = component_name.find("@")
    if check > 0:
        target_data = parse_yaml_target(component_name)
        with open(target_data['compile_file'], 'r') as f:
            data = yaml.safe_load(f)        
            selected_data = data
    print(selected_data)
    if sym_check > 0:
        parts = component_name.split("@")
        return { 'location': parts[0], 'name': parts[1] }

    components = selected_data.get(component_type)
    # do one more check to see if this has an #. If it
    # does then, we need to use the target_data and not the component_name
    if check > 0:
        for comp in components:
            if comp.get('name') == target_data['target']:
                return comp
    
    print(f"found the following {component_type}: {components}")

    for comp in components:
        if comp.get('name') == component_name:
            return comp
    return None

class UVToolInput(TypedDict):
    filepath: str
    action: str
    args: list


@tool
def uv_tool(params: UVToolInput) -> dict:
    """Run a ``uv`` command described by ``params``.

    ``params`` is a dictionary of the shape
    ``{"filepath": str, "action": str, "args": list}``.
    The ``uv`` command is executed in the directory containing
    ``filepath`` (or ``filepath`` itself when it points to a directory),
    passing ``action`` and the entries of ``args`` as its arguments.

    Returns a dictionary with the ``returncode``, ``stdout`` and ``stderr``
    of the command, or an ``error`` key when the input is invalid.
    """
    if not isinstance(params, dict):
        return {"error": "params must be a dictionary"}

    filepath = params.get("filepath")
    action = params.get("action")
    args = params.get("args")

    if not filepath or not isinstance(filepath, str):
        return {"error": "filepath must be a non-empty string"}
    if not action or not isinstance(action, str):
        return {"error": "action must be a non-empty string"}
    if args is None:
        args = []
    if not isinstance(args, list):
        return {"error": "args must be a list"}

    target = os.path.abspath(filepath)
    if os.path.isdir(target):
        workdir = target
    else:
        workdir = os.path.dirname(target) or os.getcwd()

    command = ["uv", action, *[str(arg) for arg in args]]

    try:
        result = subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return {"error": "the 'uv' executable was not found on PATH"}
    except OSError as exc:
        return {"error": str(exc)}

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@tool
def read_file(filepath: str) -> str:
    """Read a file and return its contents as a string.

    If the file at ``filepath`` does not exist, returns the string
    ``"This file does not exist"``.
    """
    if not os.path.exists(filepath):
        return "This file does not exist. Do not call this again with the same parameters."

    with open(filepath, "r") as f:

        return f"Succesfully read the contents of {filepath}. The contents are \n" + f.read()


@tool
def write_file(filepath: str, contents: str) -> str:
    """Write ``contents`` to the file at ``filepath``.

    If the file at ``filepath`` does not exist, this function will create it.
    
    """
    # if not os.path.exists(filepath):
    #     return "This file does not exist"

    with open(filepath, "w+") as f:
        f.write(contents)

    return f"Successfully wrote {len(contents)} characters to {filepath}. The task finished; do not call this again with the same parameters. "


@tool
def create_file(filepath: str) -> str:
    """Create an empty file at ``filepath``.

    If the file at ``filepath`` already exists, returns the string
    ``"This file already exists!"`` instead of creating it.
    """
    if os.path.exists(filepath):
        return "This file already exists! Do not call this again with the same parameters."

    with open(filepath, "w") as f:
        pass

    return f"Successfully created {filepath}. Task finished."


@tool
def read_directory(filepath: str) -> str:
    """List the files inside the directory at ``filepath`` as a single string.

    If the directory at ``filepath`` does not exist, returns the string
    ``"This directory does not exist. Task finished"``.
    """
    if not os.path.isdir(filepath):
        return "This directory does not exist. Task finished"

    entries = sorted(os.listdir(filepath))
    return "\n".join(entries)


# def export_uv_tool() -> dict:
#     """Return the OpenAI/OpenAPI function definition for :func:`uv_tool`."""
#     return {
#         "type": "function",
#         "function": {
#             "name": "uv_tool",
#             "description": (
#                 "Run a 'uv' command. The command is executed in the directory "
#                 "containing 'filepath' (or in 'filepath' itself when it points "
#                 "to a directory). Returns the command's returncode, stdout and "
#                 "stderr."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "filepath": {
#                         "type": "string",
#                         "description": (
#                             "Path to a file or directory that locates the uv "
#                             "project to run the command in."
#                         ),
#                     },
#                     "action": {
#                         "type": "string",
#                         "description": (
#                             "The uv subcommand or argument to run, for example "
#                             "'run', 'sync', 'add' or '--version'."
#                         ),
#                     },
#                     "args": {
#                         "type": "array",
#                         "items": {"type": "string"},
#                         "description": (
#                             "Additional arguments passed to the uv command."
#                         ),
#                     },
#                 },
#                 "required": ["filepath", "action"],
#                 "additionalProperties": False,
#             },
#         },
#     }
