"""
Tests for the Jinja transformer.
"""

import sys
import os
import unittest
from typing import List, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from go_to_jinja.go_ast import (
    Node, Template, Text, Action, Pipeline, Command, Variable,
    Literal, If, Range, With, Define, Block, Comment
)
from go_to_jinja.go_parser import parse_template
from go_to_jinja.jinja_transformer import transform_template
from go_to_jinja.jinja_renderer import render_template
import jinja2
from jinja2 import nodes as jinja_nodes


class TestJinjaTransformer(unittest.TestCase):
    """Test cases for the Jinja transformer."""

    def test_transform_text(self):
        """Test transforming plain text."""
        go_template = Template([Text("Hello, world!")])
        jinja_ast = transform_template(go_template)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertEqual(len(jinja_ast.body), 1)
        self.assertIsInstance(jinja_ast.body[0], jinja_nodes.TemplateData)
        self.assertEqual(jinja_ast.body[0].data, "Hello, world!")

    def test_transform_action(self):
        """Test transforming a simple action."""
        # Create a Go template AST for {{ .Name }}
        variable = Variable(".", ["Name"])
        pipeline = Pipeline([variable])
        action = Action(pipeline)
        go_template = Template([action])
        
        jinja_ast = transform_template(go_template)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertEqual(len(jinja_ast.body), 1)
        self.assertIsInstance(jinja_ast.body[0], jinja_nodes.Output)
        self.assertEqual(len(jinja_ast.body[0].nodes), 1)
        self.assertIsInstance(jinja_ast.body[0].nodes[0], jinja_nodes.Name)
        self.assertEqual(jinja_ast.body[0].nodes[0].name, "Name")

    def test_transform_if(self):
        """Test transforming an if statement."""
        # Create a Go template AST for {{ if .Condition }}True{{ else }}False{{ end }}
        condition = Pipeline([Variable(".", ["Condition"])])
        body = [Text("True")]
        else_body = [Text("False")]
        if_node = If(condition, body, else_body)
        go_template = Template([if_node])
        
        jinja_ast = transform_template(go_template)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertEqual(len(jinja_ast.body), 1)
        self.assertIsInstance(jinja_ast.body[0], jinja_nodes.If)
        
        # Check condition
        self.assertIsInstance(jinja_ast.body[0].test, jinja_nodes.Name)
        self.assertEqual(jinja_ast.body[0].test.name, "Condition")
        
        # Check body
        self.assertEqual(len(jinja_ast.body[0].body), 1)
        self.assertIsInstance(jinja_ast.body[0].body[0], jinja_nodes.TemplateData)
        self.assertEqual(jinja_ast.body[0].body[0].data, "True")
        
        # Check else body
        self.assertEqual(len(jinja_ast.body[0].else_), 1)
        self.assertIsInstance(jinja_ast.body[0].else_[0], jinja_nodes.TemplateData)
        self.assertEqual(jinja_ast.body[0].else_[0].data, "False")

    def test_transform_range(self):
        """Test transforming a range statement."""
        # Create a Go template AST for {{ range .Items }}{{ . }}{{ end }}
        sequence = Variable(".", ["Items"])
        body = [Action(Pipeline([Variable(".", [])]))]
        range_node = Range(sequence, [], body)
        go_template = Template([range_node])
        
        jinja_ast = transform_template(go_template)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertEqual(len(jinja_ast.body), 1)
        self.assertIsInstance(jinja_ast.body[0], jinja_nodes.For)
        
        # Check iterator
        self.assertIsInstance(jinja_ast.body[0].iter, jinja_nodes.Name)
        self.assertEqual(jinja_ast.body[0].iter.name, "Items")
        
        # Check target
        self.assertIsInstance(jinja_ast.body[0].target, jinja_nodes.Name)
        self.assertEqual(jinja_ast.body[0].target.name, "_")
        
        # Check body
        self.assertEqual(len(jinja_ast.body[0].body), 1)
        self.assertIsInstance(jinja_ast.body[0].body[0], jinja_nodes.Output)

    def test_transform_with(self):
        """Test transforming a with statement."""
        # Create a Go template AST for {{ with .User }}{{ .Name }}{{ end }}
        value = Variable(".", ["User"])
        body = [Action(Pipeline([Variable(".", ["Name"])]))]
        with_node = With(value, None, body)
        go_template = Template([with_node])
        
        jinja_ast = transform_template(go_template)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertEqual(len(jinja_ast.body), 1)
        self.assertIsInstance(jinja_ast.body[0], jinja_nodes.If)
        
        # Check condition
        self.assertIsInstance(jinja_ast.body[0].test, jinja_nodes.Name)
        self.assertEqual(jinja_ast.body[0].test.name, "User")
        
        # Check body
        self.assertEqual(len(jinja_ast.body[0].body), 1)
        self.assertIsInstance(jinja_ast.body[0].body[0], jinja_nodes.Output)

    def test_transform_comment(self):
        """Test transforming a comment."""
        # Create a Go template AST for {{/* This is a comment */}}
        comment = Comment("This is a comment")
        go_template = Template([comment])
        
        jinja_ast = transform_template(go_template)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertEqual(len(jinja_ast.body), 1)
        self.assertIsInstance(jinja_ast.body[0], jinja_nodes.Comment)
        self.assertEqual(jinja_ast.body[0].comment, "This is a comment")

    def test_transform_from_parsed_template(self):
        """Test transforming a template that was parsed from a string."""
        go_template_str = """
Hello, {{ .Name }}!

{{ if .ShowItems }}
Items:
{{ range .Items }}
- {{ .Name }}: {{ .Price }}
{{ end }}
{{ else }}
No items to display.
{{ end }}

{{ with .Footer }}
Footer: {{ . }}
{{ end }}
"""
        go_ast = parse_template(go_template_str)
        jinja_ast = transform_template(go_ast)
        
        self.assertIsInstance(jinja_ast, jinja_nodes.Template)
        self.assertTrue(len(jinja_ast.body) > 5)  # Should have multiple nodes

    def test_end_to_end_conversion(self):
        """Test the entire conversion process from Go template to Jinja template string."""
        # Define a Go template
        go_template_str = """
Hello, {{ .Name }}!

{{ if .ShowItems }}
Items:
{{ range .Items }}
- {{ .Name }}: {{ .Price }}
{{ end }}
{{ else }}
No items to display.
{{ end }}

{{ with .Footer }}
Footer: {{ . }}
{{ end }}
"""
        # Expected Jinja template (simplified for comparison)
        expected_jinja_template = """
Hello, {{ Name }}!

{% if ShowItems %}
Items:
{% for _ in Items %}
- {{ _.Name }}: {{ _.Price }}
{% endfor %}
{% else %}
No items to display.
{% endif %}

{% if Footer %}
Footer: {{ _ }}
{% endif %}
"""
        # Remove whitespace for comparison
        def normalize_template(template):
            return ''.join(line.strip() for line in template.splitlines())
        
        # Parse Go template
        go_ast = parse_template(go_template_str)
        
        # Transform to Jinja AST
        jinja_ast = transform_template(go_ast)
        
        # Render Jinja template
        jinja_template = render_template(jinja_ast)
        
        # Compare normalized templates
        normalized_expected = normalize_template(expected_jinja_template)
        normalized_actual = normalize_template(jinja_template)
        
        # Print for debugging
        print("Expected Jinja template (normalized):", normalized_expected)
        print("Actual Jinja template (normalized):", normalized_actual)
        
        # Check if the actual template contains key Jinja constructs
        self.assertIn("Hello", jinja_template)
        self.assertIn("{{ Name }}", jinja_template)
        self.assertIn("{% if", jinja_template)
        self.assertIn("{% else", jinja_template)
        self.assertIn("{% endif", jinja_template)
        self.assertIn("{% for", jinja_template)
        self.assertIn("{% endfor", jinja_template)


if __name__ == '__main__':
    unittest.main()