from opensdkv2.plugin import Plugin

import opensdkv2

def test_plugin_load():
    opensdkv2.set_plugin_directory("framework_example/plugins")
    opensdkv2.load_plugins(opensdkv2.plugin_directory)
    opensdkv2.parse("framework_example/main.yaml")
    assert len(opensdkv2.plugin_list) == 1

def test_plugin_check():
    answer, plugin = opensdkv2.is_file_a_plugin('framework_example/main.yaml')
    assert answer is True
    assert plugin == "flask"

def test_plugin_parsing():
    opensdkv2.set_plugin_directory("framework_example/plugins")
    opensdkv2.load_plugins(opensdkv2.plugin_directory)
    prog = opensdkv2.parse_plugin("framework_example/main.yaml", "flask")
    assert 'framework' in prog[0].keys()
    assert prog[0]['plugin'] == 'flask'
    assert "Before starting" in prog[1]



    


