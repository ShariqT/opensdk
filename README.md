# OpenSDK

**OpenSDK** is a specification-driven code generation framework. Instead of writing
boilerplate by hand, you describe *what* you want in YAML — classes, functions,
interfaces, constants, errors, or framework-level constructs like HTTP routes — and
OpenSDK turns those specs into structured prompts that a coding agent (backed by an
LLM) uses to generate the actual source code.

It's "spec-first": the YAML files are the single source of truth, and the generated
code is a build artifact you can regenerate at any time.

** THIS IS STILL A WORK IN PROGRESS. SOME FEATURES DO NOT WORK **

## How it works
1. **Specs** — YAML files describing components and may 
    `use:` other spec files (references are resolved and inlined).
2. **Prompt generation** — `PromptGenerator` renders the parsed components through
   Jinja2 templates (`src/opensdkv2/templates/*.txt`) to produce a precise,
   language-aware prompt. You can target a single component instead of generating
   everything (see [Targeting a component](#targeting-a-single-component)).
3. **Agent + provider** — the prompt is handed to a `CoderAgent` equipped with
   filesystem and `uv` tools, which drives the configured LLM provider to write the
   files at the spec's `location`.

### Pluggable frameworks

Beyond raw language components, OpenSDK supports **plugins** for opinionated
frameworks. A plugin validates a spec against a JSON schema and supplies its own
Jinja2 prompt template. The bundled example is a `flask` plugin
(`framework_example/plugins/flask/`) that reads a route table and generates Flask
handlers. See [Writing a plugin](#writing-a-plugin).

---

## Installation

OpenSDK targets **Python 3.10+** and uses [uv](https://docs.astral.sh/uv/) for
dependency management and building.

### Prerequisites

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed

### Set up a development environment

```bash
git clone <repo-url> opensdkv2
cd opensdkv2
uv sync
```

### Run the CLI without installing

```bash
uv run opensdk --help
```

### Build a distributable

OpenSDK uses the `uv_build` backend. To build a wheel/sdist and install the
`opensdk` entry point into your environment:

```bash
# Build the package
uv build

# Install the built wheel into the current environment
uv pip install dist/opensdkv2-*.whl
```

Once installed, the `opensdk` command is available directly:

```bash
opensdk --help
```

> **Note:** The CLI is defined in `pyproject.toml` as
> `opensdk = "opensdkv2:main"`. The package name is `opensdkv2`, while the
> executable is named `opensdk`.

---

## Using the CLI

### Basic invocation

```bash
opensdk <compile_target> [options]
```

`<compile_target>` is the path to a spec — either a **module directory** (containing
`main.yaml`/`main.yml` and `manifest.json`) or a **single spec file**. Optionally
append a `#group.name` fragment to target one component (see below).

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--module` | off | Treat the target as a module directory (loads it via `manifest.json`). |
| `--provider` | `wavespeed` | LLM provider to use. Only `wavespeed` is currently supported. |
| `--model` | `qwen/qwen3.8-flash` | Model identifier passed to the provider. |
| `--key` | placeholder | API key for the provider. **You must supply your own.** |
| `--plugin_directory` | `<user config>/OpenSDK/plugins` | Directory where plugins are discovered. |

The provider/model/key/plugin settings are persisted to a `settings.json` under the
user config directory on each run.

### Example: generate a module

```bash
uv run opensdk ./example_specs --module --key "$WAVESPEED_API_KEY"
```

This loads `example_specs/manifest.json`, parses `main.yaml`, `interfaces.yml`, and
`backbone.yml` (plus the referenced `classes/*.yaml`), builds a prompt, and runs the
agent to generate code at each spec's `location`.

### Example: generate from a single spec file

```bash
uv run opensdk ./framework_example/main.yaml --key "$WAVESPEED_API_KEY"
```

Because this file declares a `plugin: "flask"`, OpenSDK validates it against the
plugin's schema and uses the plugin's prompt template to generate the routes.

### Targeting a single component

Use the `#<group>.<name>` syntax to generate only one piece of a spec:

```bash
uv run opensdk ./example_specs/main.yaml#classes.Router --key "$WAVESPEED_API_KEY"
```

Supported groups: `classes`, `constants`, `interfaces`, `errors`, `functions`.

### The plugin directory

OpenSDK scans `--plugin_directory` for subdirectories; each subdirectory whose name
matches a plugin's module name (e.g. `flask/`) is registered as an available plugin.
Point it at the bundled examples to try them out:

```bash
uv run opensdk ./framework_example/main.yaml \
  --plugin_directory ./framework_example/plugins \
  --key "$WAVESPEED_API_KEY"
```

---

## Writing specs

A spec is a YAML document. The top-level keys describe the target and its components.
The `main.yaml`/`main.yml` in a module is the entry point; everything else is listed
in `manifest.json`.

**`main.yaml`**

```yaml
language: "python"
version: "0.1rc1"
location: "/src/backbone/__init__.py"
functions:
  - name: "start"
    description: "Entry point for the backbone component"
    prompt: >
      Create an instance of the Router class. This instance is used as a
      parameter for the creation of an instance of the Backbone class.
      This is returned from the function.
```

Components you can declare include:

- `classes` — properties, methods (with params/returns), and per-method `prompt`s
- `functions` — name, description, and `prompt`
- `interfaces` — protocol/interface definitions
- `constants` — name, datatype, value
- `errors` — custom exception types
- `required_libraries` — dependencies the generated code needs (this feature is still a WIP)

Components can reference other spec files with `use:`:

```yaml
classes:
  - use: "./example_specs/classes/Router.yaml#classes.Router"
  - use: "./example_specs/classes/Backbone.yaml#classes.Backbone"
```
Referenced files (via `use:`) are resolved relative to the
spec's location and inlined into the generated prompt.

---

## Writing a plugin

A plugin lets OpenSDK support an opinionated framework by validating a spec and
producing its own prompt. Plugins implement the `Plugin` protocol
(`src/opensdkv2/plugin.py`):

```python
class Plugin(Protocol):
    def validate_spec(filepath: str): ...
    def return_prompt() -> str: ...
```

A plugin lives in its own subdirectory under the plugin directory and exposes a class
named `<plugin_name>Plugin` (e.g. `flaskPlugin` in `flask/flask.py`). It typically:

1. Loads the spec YAML.
2. Validates it against a bundled JSON Schema.
3. Renders a Jinja2 prompt template with the spec's framework data.

See `framework_example/plugins/flask/` for a complete example:

```
framework_example/plugins/flask/
├── flask.py            # flaskPlugin class
├── schema.json         # JSON Schema for the spec
└── templates/
    └── prompt.txt      # Jinja2 prompt template
```

`flaskPlugin.validate_spec()` validates the spec and ensures a `framework` key is
present; `return_prompt()` renders `prompt.txt` with the routes and output location.

---

## The agent and its tools

Generated prompts are executed by a `CoderAgent` (LangGraph/LangChain) that can call
these tools (defined in `src/opensdkv2/utils.py`):

| Tool | Purpose |
|------|---------|
| `uv_tool` | Run a `uv` command in the target's directory. |
| `read_file` | Read a file's contents. |
| `write_file` | Write (or create) a file with given contents. |
| `create_file` | Create an empty file if it doesn't already exist. |
| `read_directory` | List a directory's entries. |

The agent plans first, then executes each step, and finishes by reporting the actions
it took. Prompts instruct it to produce syntactically correct code at the spec's
`location`.

---

## Repository layout

```
opensdkv2/
├── src/opensdkv2/
│   ├── __init__.py       # CLI entry point (main) and module/plugin loading
│   ├── ast_parser.py     # Parses YAML specs into AST nodes
│   ├── prompter.py       # PromptGenerator: renders components via Jinja2
│   ├── provider.py       # Model providers (WavespeedProvider)
│   ├── agent.py          # CoderAgent (LangGraph)
│   ├── plugin.py         # Plugin protocol
│   ├── utils.py          # Agent tools (file + uv helpers)
│   └── templates/        # Jinja2 prompt templates
├── example_specs/        # Example module spec (manifest + components)
├── framework_example/    # Example plugin (flask) and its spec
├── tests/                # Test suite
└── pyproject.toml        # Package metadata, deps, and the `opensdk` entry point
```

---

## Development

```bash
uv sync            # install dependencies
uv run pytest      # run the test suite
uv run opensdk --help   # exercise the CLI
```

## License

See the repository for license details.
