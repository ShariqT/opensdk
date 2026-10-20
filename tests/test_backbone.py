import opensdkv2
from opensdkv2.prompter import PromptGenerator
from opensdkv2.provider import WavespeedProvider


def test_start():
    assert opensdkv2.version == "0.0.1"

def test_parse():
    prog = opensdkv2.parse("spec.yaml")
    assert len(prog.ast.classes) == 3
    assert len(prog.ast.functions) == 2
    assert prog.ast.functions[0].params[0].name == "param1"
    assert len(prog.ast.classes[0].methods) == 1
    assert prog.ast.classes[0].methods[0].params[1].datatype == "classes#Plugin"
    assert len(prog.ast.interfaces) == 1
    assert prog.references[0].ast.interfaces[0].name == "ExportableJSON"
    assert prog.references[0].ast.location == "/src/backbone/interfaces.py"




def test_slimfile_decoding():
    prog = opensdkv2.parse("example_specs/main.yaml")
    assert len(prog.ast.classes) == 0
    assert prog.ast.language == "python"
    assert prog.ast.location == "/src/backbone/__init__.py"

def test_multifile_decoding():
    prog = opensdkv2.parse("example_specs/backbone.yml")
    assert len(prog.ast.classes) == 2
    assert prog.ast.classes[0].name == "Router"
    assert prog.ast.classes[1].name == "Backbone"
    assert prog.ast.location == "/src/backbone/classes.py"

def test_package_manifest():
    progs = opensdkv2.load("example_specs")
    assert len(progs) == 3
    assert len(progs[0].ast.interfaces) == 1
    assert progs[0].ast.location == "/src/backbone/interfaces.py"
    assert len(progs[1].ast.classes) == 2
    assert progs[1].ast.classes[0].name == "Router"
    assert progs[1].ast.classes[1].name == "Backbone"

def test_parsing_spec_target():
    results = opensdkv2.parse_yaml_target("example_specs/main.yaml")
    assert len(results.keys()) == 0
    results = opensdkv2.parse_yaml_target("main.yaml#classes.Backbone")
    print(results)
    assert results['target_group'] == "classes"
    assert results['target'] == "Backbone"

    