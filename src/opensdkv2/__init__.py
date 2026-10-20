import json
import os
from typing import List, Union
from .ast_parser import AST, ASTNode
from .prompter import PromptGenerator
from .utils import parse_yaml_target
import argparse
import json
from platformdirs import user_config_path
from . import provider as model_providers
from pathlib import Path


version = "0.0.1"

plugin_directory = ""

provider = ""
current_model = ""
current_api_key = ""
plugin_list = []

def main():
    global plugin_directory
    global provider
    global current_model
    global current_api_key
    parser = argparse.ArgumentParser(prog='opensdk')
    parser.add_argument("compile_target")
    parser.add_argument("--module", action="store_true")
    parser.add_argument("--provider", default="wavespeed")
    parser.add_argument("--model", default="qwen/qwen3.8-flash")
    parser.add_argument("--key", default="changethis")
    parser.add_argument("--plugin_directory", default=user_config_path("OpenSDK") / "plugins")
    args = parser.parse_args()
    if args.key == "changethis":
        raise Exception("You have a default API key set! Change this to your OWN API KEY!")

    current_api_key = args.key
    config_file = user_config_path("OpenSDK") / "settings.json"

    plugin_directory = args.plugin_directory
    Path(plugin_directory).mkdir(parents=True, exist_ok=True)
    current_model = args.model
    provider = args.provider
    load_plugins(plugin_directory)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    settings = {"key": args.key, "provider": args.provider, "model": args.model, "plugin_directory": str(args.plugin_directory)}
    config_file.write_text(json.dumps(settings))
    target_group = parse_yaml_target(args.compile_target)

    if len(target_group.keys()) == 0:
        compile_target = args.compile_target
    else:
        compile_target = target_group['compile_file']

    try:
        if args.module is True:
            is_module = check_if_target_is_a_module(compile_target)
            prog = None
            if is_module is True:
                prog = load(compile_target)
        else:
            is_plugin = is_file_a_plugin(compile_target)
            if is_plugin[0] is True:
                plugin_prog = parse_plugin(compile_target, is_plugin[1])
                run_prompt(plugin_prog[1])
            else:
                prog = parse(compile_target)
                print(f"lang is {prog.ast.language}")
                prompter = PromptGenerator(
                    classes=prog.ast.classes,
                    functions=prog.ast.functions,
                    constants=prog.ast.constants,
                    version=prog.ast.version,
                    interfaces=prog.ast.interfaces,
                    errors=prog.ast.errors,
                    language=prog.ast.language,
                    location=prog.ast.location
                )
                prompt = generate(prog, prompter, target_group)
                run_prompt(prompt)

        

        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))




def check_if_target_is_a_module(directory: str):
    # Check if directory exists and is a directory
    if not os.path.exists(directory):
        raise Exception(f"Directory does not exist: {directory}")
    if not os.path.isdir(directory):
        raise Exception(f"Path is not a directory: {directory}")
    
    # Look for main.yaml or main.yml
    main_yaml_path = os.path.join(directory, "main.yaml")
    main_yml_path = os.path.join(directory, "main.yml")
    
    if os.path.exists(main_yaml_path):
        return True
    elif os.path.exists(main_yml_path):
        return True
    else:
        raise Exception(f"No main.yaml or main.yml file found in directory: {directory}")
    
    # Look for manifest.json
    manifest_path = os.path.join(directory, "manifest.json")
    if not os.path.exists(manifest_path):
        raise Exception(f"No manifest.json file found in directory: {directory}")



def parse_plugin(filepath: str, plugin: str):
    return parse_plugin_spec(filepath, plugin)



def is_file_a_plugin(filepath: str)-> bool:
    prog = AST.parse_preamble(filepath)
    if prog.plugin is not None:
        return (True, prog.plugin)
    else:
        return (False, None)

    
def set_plugin_directory(filepath):
    global plugin_directory
    plugin_directory = filepath
    return True

def parse(filepath:str) -> Union["ASTNode", dict]:
    prog = ASTNode.from_yaml(filepath)
    return prog

def load_plugins(filepath: str):
    plugins = []
    for name in os.listdir(filepath):
        full_path = os.path.join(filepath, name)
        if os.path.isdir(full_path):
            plugins.append({"name": name, "status": True})
    global plugin_list
    plugin_list = plugins
    import sys
    plugin_path = os.path.abspath(str(plugin_directory))
    if plugin_path not in sys.path:
        sys.path.insert(0, plugin_path)
    

def __load_plugin_protocol(module_name: str):
    import importlib.util
    # Load the plugin module straight from its file so we don't depend on the
    # plugin directory being on sys.path. Importing by name (e.g. "flask.flask")
    # breaks when a plugin shares its name with an installed package, or when
    # the plugin folder has no __init__.py (making it a namespace package that
    # a regular installed package will shadow).
    global plugin_directory
    plugin_root = os.path.abspath(str(plugin_directory))
    module_file = os.path.join(plugin_root, module_name, f"{module_name}.py")
    if not os.path.isfile(module_file):
        package_init = os.path.join(plugin_root, module_name, "__init__.py")
        if os.path.isfile(package_init):
            module_file = package_init
        else:
            raise ModuleNotFoundError(
                f"Could not find a plugin module for '{module_name}' in {plugin_root}"
            )
    spec = importlib.util.spec_from_file_location(
        f"opensdk_plugin_{module_name}", module_file
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Could not load plugin module from {module_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class_name = f"{module_name}Plugin"
    return getattr(module, class_name)

def parse_plugin_spec(filepath: str, plugin_name: str) -> tuple:
    global plugin_list
    global plugin_directory
    found = False
    for p in plugin_list:
        if p["name"] == plugin_name:
            found = True
            break
    if found is False:
        raise Exception(f"The {plugin_name} plugin was not found.")
    pluginClass = __load_plugin_protocol(plugin_name)
    prog = pluginClass(filepath)
    validation_results = prog.validate_spec()
    if validation_results[0] is False:
        raise Exception(f"""Validation failed for {filepath} because 
                        of {validation_results[1]}""")
    prompt = prog.return_prompt()
    return (validation_results[1], prompt)
    
 

def load(directory: str) -> List["ASTNode"]:
    # Look for manifest.json
    manifest_path = os.path.join(directory, "manifest.json")
    if not os.path.exists(manifest_path):
        raise Exception(f"No manifest.json file found in directory: {directory}")
    
    # Read manifest.json
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    files = manifest.get('files', [])
    
    # List to store all ASTNodes
    ast_list = []

    # Look for main.yaml or main.yml
    main_yaml_path = os.path.join(directory, "main.yaml")
    main_yml_path = os.path.join(directory, "main.yml")
    
    if os.path.exists(main_yaml_path):
        main_file = main_yaml_path
    elif os.path.exists(main_yml_path):
        main_file = main_yml_path
    else:
        raise Exception(f"No main.yaml or main.yml file found in directory: {directory}")
    
    # Get the canonical path of main file to compare
    main_file_canonical = os.path.realpath(main_file)
    
    # Parse all files from manifest first (excluding main file if it's listed)
    for rel_path in files:
        full_path = os.path.join(directory, rel_path)
        if not os.path.exists(full_path):
            raise Exception(f"File listed in manifest does not exist: {full_path}")
        
        # Skip if this is the main file
        if os.path.realpath(full_path) == main_file_canonical:
            continue
        
        ast_node = ASTNode.from_yaml(full_path)
        ast_list.append(ast_node)
    
    # Parse main file last and add to the list
    main_ast_node = ASTNode.from_yaml(main_file)
    ast_list.append(main_ast_node)
    
    return ast_list





def generate(prog: "ASTNode", prompter: PromptGenerator, target: dict) -> bool:
    print("generating the prompt")
    prompt = ""
    for ref in prog.references:
        if Path(ref.ast.location).exists:
            prompt = prompt + prompter.link_reference(ref.ast)
    prompt = prompt + prompter.create(target) 
    print(f"the prompt is {prompt}")   
    return prompt

def run_prompt(prompt: str):
    global provider
    global current_model
    global current_api_key
    current_provider = None
    system_prompt = """You are a helpful coding assistant. You have access to tools to create files. Once you receive a tool output, analyze it and respond to the user or finish the task; do not loop back to the tool. " \
    When given a prompt, you must always create a plan first. Return this plan to the user. Then go through each step of this plan. At the end,
    return all of the actions taken to complete the plan. Plans are complete when all of the steps are complete. IMPORTANT: you do not
    have to verify output works; only that it adheres to correct syntax.
    """
    if provider == "wavespeed":
       current_provider = model_providers.WavespeedProvider(current_model, current_api_key, system_prompt)
    else:
        raise Exception(f"{provider} is not supported!")

    current_provider.generate(prompt)


