"""
Jinja renderer.

This module provides functionality to render Jinja AST back to a template string.
"""

from typing import List, Dict, Any, Optional, Union
import jinja2
from jinja2 import nodes as jinja_nodes
from jinja2.compiler import generate


class JinjaRenderer:
    """Renderer for converting Jinja AST to a template string."""
    
    def __init__(self):
        self.environment = jinja2.Environment()
    
    def render(self, node: jinja_nodes.Node) -> str:
        """Render a Jinja AST node to a template string."""
        if not isinstance(node, jinja_nodes.Template):
            # Wrap non-template nodes in a template
            node = jinja_nodes.Template([node], lineno=1)
        
        # Generate Python code from the AST
        source = generate(node, self.environment, '<string>', '<string>')
        
        # Extract the template source from the generated code
        # This is a bit of a hack, but it works for simple templates
        template_lines = []
        in_template = False
        
        for line in source.splitlines():
            if line.strip().startswith('yield '):
                # Extract the yielded content
                content = line.strip()[6:].strip()
                if content.startswith("'") and content.endswith("'"):
                    # String literal
                    template_lines.append(eval(content))
                elif content.startswith('environment.filters'):
                    # Filter expression
                    template_lines.append('{{ ... | ... }}')
                elif content.startswith('environment.call'):
                    # Function call
                    template_lines.append('{{ ... }}')
                else:
                    # Other expression
                    template_lines.append('{{ ... }}')
            elif 'extend(' in line and 'blocks[' in line:
                # Block definition
                block_name = line.split('blocks[')[1].split(']')[0].strip("'")
                template_lines.append(f'{{% block {block_name} %}}')
            elif line.strip() == 'yield from child()':
                # End of block
                template_lines.append('{% endblock %}')
            elif 'if ' in line and not line.strip().startswith('#'):
                # If statement
                template_lines.append('{% if ... %}')
            elif line.strip() == 'else:':
                # Else statement
                template_lines.append('{% else %}')
            elif 'for ' in line and ' in ' in line and not line.strip().startswith('#'):
                # For loop
                template_lines.append('{% for ... in ... %}')
            elif line.strip() == 'if 0:' or line.strip() == 'if False:':
                # End of if or for
                template_lines.append('{% endif %}')
            elif line.strip() == 'if 1:' or line.strip() == 'if True:':
                # Continuation
                pass
            elif line.strip() == 'pass':
                # Empty block
                pass
        
        return ''.join(template_lines)


def render_template(node: jinja_nodes.Node) -> str:
    """Render a Jinja AST to a template string."""
    renderer = JinjaRenderer()
    return renderer.render(node)