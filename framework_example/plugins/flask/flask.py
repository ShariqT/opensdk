from opensdkv2.plugin import Plugin
import yaml, json, os
from jsonschema import validate, Draft202012Validator, ValidationError
from jinja2 import Environment, FileSystemLoader, select_autoescape


class flaskPlugin(Plugin):
        def __init__(self, filepath: str):
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            parent_directory = os.path.dirname(os.path.abspath(__file__))
            print(parent_directory)
            with open(f"{parent_directory}/schema.json") as f:
                schema_data = json.load(f)
            # check if the schema itself is valid
            Draft202012Validator.check_schema(schema_data)
            self.env = Environment(
                        loader=FileSystemLoader(f"{parent_directory}/templates"),
                        autoescape=select_autoescape()
                    )
            self.data = data
            self.schema = schema_data
           
        def validate_spec(self):
            try:
                validate(self.data, self.schema)
                framework_keyword = self.data.get('framework', None)
                if framework_keyword is None:
                    raise ValidationError("Missing framework keyword in schema")
                return (True, self.data)
            except ValidationError as e:
                return (False, e)

        def return_prompt(self):
            templ = self.env.get_template("prompt.txt")
            val = templ.render(data=self.data['framework'], location=self.data['location'])
            return val