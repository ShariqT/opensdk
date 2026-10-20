import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Any
from .utils import find_component, parse_yaml_target

@dataclass
class Property:
    name: str
    datatype: str
    prop_type: str = "instance"
    view: str = 'public'
    description: Optional[str] = None
    value: Optional[any] = None
@dataclass
class Parameter:
    name: str
    datatype: str
    description: Optional[str] = None


@dataclass
class Function:
    name: str
    prompt: str
    params: List[Parameter] = field(default_factory=list)


@dataclass
class Constant:
    name: str
    description: str
    datatype: str
    value: str


@dataclass
class ParentClass:
    location: str
    name: str


@dataclass
class ReturnValue:
    datatype: str
    description: Optional[str] = None


@dataclass
class Method:
    name: str
    prompt: Optional[str] = None
    description: Optional[str] = None
    namespace: Optional[str] = None
    params: List[Parameter] = field(default_factory=list)
    returns: List[ReturnValue] = field(default_factory=list)
    onfailure: List[str] = field(default_factory=list)


@dataclass
class Interface:
    name: str
    description: Optional[str] = None
    methods: List[Method] = field(default_factory=list)


@dataclass
class Error:
    name: str
    description: Optional[str] = None
    message: Optional[str] = None

@dataclass
class Class:
    name: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    inherits: List[ParentClass] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    methods: List[Method] = field(default_factory=list)
    use: Optional[str] = None

@dataclass
class AST:
    language: str
    version: str
    location: str
    plugin: Optional[str]
    classes: List[Class] = field(default_factory=list)
    functions: List[Function] = field(default_factory=list)
    constants: List[Constant] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    errors: List[Error] = field(default_factory=list)
    required_libraries: List[str] = field(default_factory=list)

    @classmethod
    def parse_preamble(cls, filepath: str) -> "AST":
        with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
        required_libraries = data.get('required_libraries', [])
        location = data.get('location', '')
        language = data.get('language', '')
        version = data.get('version', '0.0.1')
        plugin = data.get('plugin', None)
        return cls(
            language=language,
            plugin=plugin,
            version=version,
            classes=[],
            functions=[],
            constants=[],
            interfaces=[],
            errors=[],
            required_libraries=required_libraries,
            location=location
        )
    # def generate_prompt(self, return_value=False):
    #     self.prompter.language = self.language
    #     self.prompter.classes = self.classes
    #     self.prompter.functions = self.functions
    #     self.prompter.constants = self.constants
    #     self.prompter.interfaces = self.interfaces
    #     self.prompter.errors = self.errors
    #     self.prompter.required_libraries = self.required_libraries
    #     self.prompter.version = self.version
    #     
    #     return self.prompter.create(return_value)


@dataclass
class ASTNode:
    """A node in the AST graph structure. Contains an AST and references to other ASTs."""
    ast: AST
    references: List["ASTNode"] = field(default_factory=list)


    @classmethod
    def _load_classes(cls, filepath: str, base_dir: str) -> List[Class]:
        """Load classes from a spec file, handling 'use' references recursively."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        # get all use references 
        all_loaded_classes = data.get('classes', [])
        for cdata in data.get('classes', []):
            if 'use' in cdata:
                use_path = cdata.get('use')
                referenced_classes = find_component("classes", use_path, None)
                all_loaded_classes.append(referenced_classes)
        classes = []
        for class_data in all_loaded_classes:
            current_data = class_data
            if 'use' in class_data:
                continue
                # This is a reference to another spec file
                use_path = class_data.get('use')
                referenced_classes = find_component("classes", use_path, None) 
                # if not os.path.isabs(use_path):
                #     use_path = os.path.join(base_dir, use_path)
                # # Recursively load classes from the referenced spec
                # referenced_classes = cls._load_classes(use_path, os.path.dirname(use_path))
                # classes.extend(referenced_classes)
                # classes.append(Class(
                #     name=referenced_classes.get('name'),
                #     inherits=referenced_classes,
                #     implements=interfaces_implemented,
                #     properties=properties,
                #     methods=methods,
                #     use=class_data.get('use')
                # ))
                current_data = referenced_classes
                
            else:
                # parent classes
                parent_class_data = []
                parent_classes = current_data.get('inherits', [])
                for pclass in parent_classes:

                    pclass_data = find_component("classes", pclass, None)
                    parent_class_data.append(
                        ParentClass(
                            name = pclass_data.get('name'),
                            location = pclass_data.get('location')
                        )
                    )
                # any interfaces implemented
                iface_data_key = {}
                interfaces_implemented = current_data.get('implements', [])
                for iface in interfaces_implemented:
                    iface_data = find_component("interfaces", iface, data)
                    for m in iface_data.get('methods'):
                        iface_data_key[ m.get('name')] = m
                
                # Regular class definition
                properties = [
                    Property(
                        name=prop.get('name'),
                        datatype=prop.get('datatype'),
                        view=prop.get('view', 'public'),
                        prop_type=prop.get('prop_type', 'instance'),
                        description=prop.get('description'),
                        value=prop.get('value')
                    )
                    for prop in current_data.get('properties', [])
                ]
                # Parse methods
                methods = []
                for method_data in current_data.get('methods', []):
                    prompt = method_data.get('prompt')
                    description = method_data.get('description')
                    if method_data.get('name') in iface_data_key.keys():
                        method_data = iface_data_key[method_data.get('name')]

                    
                    params =[]
                    for param in method_data.get('params', []):
                        params.append(Parameter(
                            name= param.get('name'),
                            datatype=param.get('datatype'),
                            description=param.get('description'),
                        ))

                   
                            
                    returns =[]
                    for ret in method_data.get('returns', []):
                        returns.append(
                            ReturnValue(
                                datatype=ret.get('datatype'),
                                description=ret.get('description'),
                            )
                        )
                    

                    methods.append(Method(
                        name=method_data.get('name'),
                        description=description,
                        prompt=prompt,
                        params=params,
                        returns=returns,
                        onfailure=method_data.get('onfailure', [])
                    ))
                
            
                classes.append(Class(
                    name=current_data.get('name'),
                    inherits=parent_class_data,
                    implements=interfaces_implemented,
                    properties=properties,
                    methods=methods,
                    use=current_data.get('use')
                ))
        return classes

    
    @classmethod
    def from_yaml(cls, filepath: str) -> "ASTNode":
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        base_dir = os.path.dirname(os.path.abspath(filepath))
        classes = cls._load_classes(filepath, base_dir)
        
        functions = []
        for func_data in data.get('functions', []):
            params = [
                Parameter(
                    name=param.get('name'),
                    datatype=param.get('datatype'),
                    description=param.get('description')
                )
                for param in func_data.get('params', [])
            ]
            functions.append(Function(
                name=func_data.get('name'),
                prompt=func_data.get('prompt'),
                params=params
            ))

        constants = [
            Constant(
                name=const.get('name'),
                description=const.get('description'),
                datatype=const.get('datatype'),
                value=const.get('value')
            )
            for const in data.get('constants', [])
        ]

        interfaces = []
        for interface_data in data.get('interfaces', []):
            methods = []
            for method_data in interface_data.get('methods', []):
                params = [
                    Parameter(
                        name=param.get('name'),
                        datatype=param.get('datatype'),
                        description=param.get('description')
                    )
                    for param in method_data.get('params', [])
                ]
                returns = [
                    ReturnValue(
                        datatype=ret.get('datatype'),
                        description=ret.get('description')
                    )
                    for ret in method_data.get('returns', [])
                ]
                methods.append(Method(
                    name=method_data.get('name'),
                    description=method_data.get('description'),
                    namespace=method_data.get('namespace'),
                    params=params,
                    returns=returns,
                    onfailure=method_data.get('onfailure', [])
                ))
            interfaces.append(Interface(
                name=interface_data.get('name'),
                description=interface_data.get('description'),
                methods=methods
            ))

        errors = [
            Error(
                name=err.get('name'),
                description=err.get('description'),
                message=err.get('message')
            )
            for err in data.get('errors', [])
        ]

        required_libraries = data.get('required_libraries', [])
        location = data.get('location', '')
        language = data.get('language', '')
        version = data.get('version', '0.0.1')
        plugin = data.get('plugin', None)

        if language == '':
            raise Exception("You need to specify a language for this spec")
        print(f"creating ast with classes {classes}")
        # Create the main AST
        main_ast = AST(
            language=language,
            plugin=plugin,
            version=version,
            classes=classes,
            functions=functions,
            constants=constants,
            interfaces=interfaces,
            errors=errors,
            required_libraries=required_libraries,
            location=location
        )

        # Handle references - create separate ASTNodes for each referenced file
        reference_nodes = []
        references = data.get('references', [])
        for ref_path in references:
            if not os.path.isabs(ref_path):
                ref_path = os.path.join(base_dir, ref_path)
            
            # Recursively load the referenced file as an ASTNode
            ref_node = cls.from_yaml(ref_path)
            reference_nodes.append(ref_node)

        # Return the ASTNode with the main AST and reference branches
        return ASTNode(ast=main_ast, references=reference_nodes)



