# Go-to-Jinja

A Python application to convert Go text templates (used in Helm) to Jinja templates.

## Description

Go-to-Jinja is a tool that converts Go text templates (as used in Helm charts) to Jinja2 templates. It parses Go templates into an Abstract Syntax Tree (AST), transforms each tree node to an AST node for Jinja, and then dumps the Jinja templates.

## Installation

### From Source

1. Clone the repository:
   ```
   git clone <repository-url>
   cd go-to-jinja
   ```

2. Install the package:
   ```
   pip install -e .
   ```

## Usage

### Command Line Interface

Convert a single file:
```
go-to-jinja input.tmpl -o output.j2
```

Convert all templates in a directory:
```
go-to-jinja input_dir -o output_dir
```

Convert all templates in a directory recursively:
```
go-to-jinja input_dir -o output_dir -r
```

Print the converted template to stdout:
```
go-to-jinja input.tmpl
```

### Python API

```python
from go_to_jinja.go_parser import parse_template
from go_to_jinja.jinja_transformer import transform_template
from go_to_jinja.jinja_renderer import render_template

# Convert a Go template to a Jinja template
def convert_template(input_content):
    # Parse Go template to AST
    go_ast = parse_template(input_content)
    
    # Transform to Jinja AST
    jinja_ast = transform_template(go_ast)
    
    # Render Jinja template
    jinja_template = render_template(jinja_ast)
    
    return jinja_template

# Example usage
go_template = """
Hello, {{ .Name }}!

{{ if .ShowItems }}
Items:
{{ range .Items }}
- {{ .Name }}: {{ .Price }}
{{ end }}
{{ else }}
No items to display.
{{ end }}
"""

jinja_template = convert_template(go_template)
print(jinja_template)
```

## How It Works

The conversion process involves three main steps:

1. **Parsing**: The Go template is parsed into an Abstract Syntax Tree (AST) using a custom parser.
2. **Transformation**: Each node in the Go template AST is transformed into a corresponding node in the Jinja AST.
3. **Rendering**: The Jinja AST is rendered back to a template string.

### Go Template to Jinja Mapping

| Go Template | Jinja Template |
|-------------|---------------|
| `{{ .Name }}` | `{{ Name }}` |
| `{{ if .Condition }}...{{ else }}...{{ end }}` | `{% if Condition %}...{% else %}...{% endif %}` |
| `{{ range .Items }}...{{ end }}` | `{% for _ in Items %}...{% endfor %}` |
| `{{ with .Value }}...{{ end }}` | `{% if Value %}...{% endif %}` |
| `{{/* Comment */}}` | `{# Comment #}` |

## Limitations

- Template inclusion is not supported.
- Some advanced Go template features may not be fully supported.
- The Jinja renderer is a simplified implementation and may not handle all Jinja AST constructs perfectly.

## Development

### Running Tests

```
cd go-to-jinja
python -m unittest discover tests
```

### Project Structure

- `src/go_to_jinja/go_ast.py`: Go template AST structures
- `src/go_to_jinja/go_parser.py`: Parser for Go templates
- `src/go_to_jinja/jinja_transformer.py`: Transformer for converting Go AST to Jinja AST
- `src/go_to_jinja/jinja_renderer.py`: Renderer for Jinja templates
- `src/go_to_jinja/main.py`: Main application logic and CLI interface
- `tests/`: Test cases

## License

This project is licensed under the MIT License - see the LICENSE file for details.