from jinja2 import Environment, PackageLoader, select_autoescape
from .ast_parser import ASTNode, AST
class PromptGenerator:
    def __init__(self, **kwargs):
        self.version = kwargs.get('version')
        self.classes = kwargs.get('classes')
        self.functions = kwargs.get('functions')
        self.constants = kwargs.get('constants')
        self.interfaces = kwargs.get('interfaces')
        self.errors = kwargs.get('errors')
        self.language = kwargs.get('language')
        self.location = kwargs.get('location')
        self.env = Environment(
            loader=PackageLoader("opensdkv2"),
            autoescape=select_autoescape()
        )

    def link_reference(self, prog: "AST") -> str:
        template = self.env.get_template("linking_text.txt")
        return template.render(
            classes=prog.classes,
            functions=prog.functions,
            constants=prog.constants,
            interfaces=prog.interfaces,
            errors=prog.errors,
            location=prog.location
        )


    def __constants_prompt(self, target=None):
        val = ""
        target_search = False
        template = self.env.get_template("constants.txt")
        components = self.constants
        if target is not None:
            components = self.__find_component(self.constants, target['target'])
        for const in components:
            const.language = self.language
            val = val + template.render(active_constant=const, location=self.location)
        return val


    def __classes_prompt(self, target=None):
        val = ""
        template = self.env.get_template("class.txt")
        components = self.classes
        print(f"lang in prompt is {self.language}")
        print(f"slef.classes is {self.classes}")
        if target is not None:
            components = self.__find_component(self.classes, target['target'])
        print(f"components is {components}")
        for cl in components:
            cl.language = self.language
            val = val + template.render(active_class=cl, location=self.location)
        return val

    def __find_component(self, component_group, target):
        if target == '':
            return component_group
        else:
            for component in component_group:
                if component.name == target:
                    return [component]
        
    def __interfaces_prompt(self, target=None):
        val = ""
        template = self.env.get_template("interfaces.txt")
        components = self.interfaces
        if target is not None:
            components = self.__find_component(self.interfaces, target['target'])
        for iface in components:
                iface.language = self.language
                val = val + template.render(active_interface=iface, location=self.location)
        return val

    def __errors_prompt(self, target=None):
        val = ""
        template = self.env.get_template("errors.txt")
        components = self.errors
        if target is not None:
            componets = self.__find_component(self.errors, target['target'])
        for err in components:
            # print(err)
            err.language = self.language
            val = val + template.render(active_error=err, location=self.location)
        return val


    def __functions_prompt(self, target=None):
        val = ""
        for fn in self.functions:
            template = self.env.get_template("functions.txt")
            # print(fn)
            fn.language = self.language
            val = val + template.render(active_function=fn, location=self.location)
        return val

    def create(self, target: dict):
        val = ""
        if len(target.keys()) == 0:
            val = val + self.__constants_prompt()
            val = val + self.__classes_prompt()
            val = val + self.__interfaces_prompt()
            val = val + self.__errors_prompt()
            val = val + self.__functions_prompt()
        else:
            if target['target_group'] == 'constants':
                val = val + self.__constants_prompt(target)
            if target['target_group'] == 'interfaces':
                val = val + self.__interfaces_prompt(target)
            if target['target_group'] == 'classes':
                val = val + self.__classes_prompt(target)
            if target['target_group'] == 'errors':
                val = val + self.__errors_prompt(target)
        
       
        
        print(val)
        return val

        
        
