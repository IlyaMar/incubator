"""
Tests for the Go template parser.
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


class TestGoParser(unittest.TestCase):
    """Test cases for the Go template parser."""

    def test_parse_text(self):
        """Test parsing plain text."""
        template_str = "Hello, world!"
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertEqual(len(ast.nodes), 1)
        self.assertIsInstance(ast.nodes[0], Text)
        self.assertEqual(ast.nodes[0].value, "Hello, world!")

    def test_parse_action(self):
        """Test parsing a simple action."""
        template_str = "Hello, {{ .Name }}!"
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertEqual(len(ast.nodes), 3)
        
        self.assertIsInstance(ast.nodes[0], Text)
        self.assertEqual(ast.nodes[0].value, "Hello, ")
        
        self.assertIsInstance(ast.nodes[1], Action)
        self.assertIsInstance(ast.nodes[1].pipeline, Pipeline)
        self.assertEqual(len(ast.nodes[1].pipeline.commands), 1)
        self.assertIsInstance(ast.nodes[1].pipeline.commands[0], Variable)
        self.assertEqual(ast.nodes[1].pipeline.commands[0].name, ".")
        self.assertEqual(ast.nodes[1].pipeline.commands[0].fields, ["Name"])
        
        self.assertIsInstance(ast.nodes[2], Text)
        self.assertEqual(ast.nodes[2].value, "!")

    def test_parse_if(self):
        """Test parsing an if statement."""
        template_str = """{{ if .Condition }}
  Condition is true
{{ else }}
  Condition is false
{{ end }}"""
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertEqual(len(ast.nodes), 1)
        
        self.assertIsInstance(ast.nodes[0], If)
        self.assertIsInstance(ast.nodes[0].condition, Pipeline)
        self.assertEqual(len(ast.nodes[0].condition.commands), 1)
        self.assertIsInstance(ast.nodes[0].condition.commands[0], Variable)
        self.assertEqual(ast.nodes[0].condition.commands[0].name, ".")
        self.assertEqual(ast.nodes[0].condition.commands[0].fields, ["Condition"])
        
        self.assertEqual(len(ast.nodes[0].body), 1)
        self.assertIsInstance(ast.nodes[0].body[0], Text)
        self.assertEqual(ast.nodes[0].body[0].value, "\n  Condition is true\n")
        
        self.assertEqual(len(ast.nodes[0].else_body), 1)
        self.assertIsInstance(ast.nodes[0].else_body[0], Text)
        self.assertEqual(ast.nodes[0].else_body[0].value, "\n  Condition is false\n")

    def test_parse_range(self):
        """Test parsing a range statement."""
        template_str = """{{ range .Items }}
  - {{ . }}
{{ end }}"""
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertEqual(len(ast.nodes), 1)
        
        self.assertIsInstance(ast.nodes[0], Range)
        self.assertIsInstance(ast.nodes[0].sequence, Variable)
        self.assertEqual(ast.nodes[0].sequence.name, ".")
        self.assertEqual(ast.nodes[0].sequence.fields, ["Items"])
        
        self.assertEqual(len(ast.nodes[0].body), 1)
        self.assertIsInstance(ast.nodes[0].body[0], Text)
        self.assertTrue("\n  - " in ast.nodes[0].body[0].value)

    def test_parse_with(self):
        """Test parsing a with statement."""
        template_str = """{{ with .User }}
  Name: {{ .Name }}
  Email: {{ .Email }}
{{ end }}"""
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertEqual(len(ast.nodes), 1)
        
        self.assertIsInstance(ast.nodes[0], With)
        self.assertIsInstance(ast.nodes[0].value, Variable)
        self.assertEqual(ast.nodes[0].value.name, ".")
        self.assertEqual(ast.nodes[0].value.fields, ["User"])
        
        self.assertEqual(len(ast.nodes[0].body), 3)
        self.assertIsInstance(ast.nodes[0].body[0], Text)
        self.assertTrue("\n  Name: " in ast.nodes[0].body[0].value)

    def test_parse_comment(self):
        """Test parsing a comment."""
        template_str = "Hello{{/* This is a comment */}}, world!"
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertEqual(len(ast.nodes), 3)
        
        self.assertIsInstance(ast.nodes[0], Text)
        self.assertEqual(ast.nodes[0].value, "Hello")
        
        self.assertIsInstance(ast.nodes[1], Comment)
        self.assertEqual(ast.nodes[1].value, " This is a comment ")
        
        self.assertIsInstance(ast.nodes[2], Text)
        self.assertEqual(ast.nodes[2].value, ", world!")

    def test_parse_complex_template(self):
        """Test parsing a more complex template."""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ .Title }}</title>
</head>
<body>
    <h1>{{ .Header }}</h1>
    
    {{ if .ShowItems }}
    <ul>
        {{ range .Items }}
        <li>{{ .Name }} - {{ .Price }}</li>
        {{ end }}
    </ul>
    {{ else }}
    <p>No items to display.</p>
    {{ end }}
    
    {{ with .Footer }}
    <footer>{{ . }}</footer>
    {{ end }}
</body>
</html>
"""
        ast = parse_template(template_str)
        
        self.assertIsInstance(ast, Template)
        self.assertTrue(len(ast.nodes) > 5)  # Should have multiple nodes
        
        # Check for specific node types in the AST
        node_types = [type(node) for node in ast.nodes]
        self.assertIn(Text, node_types)
        self.assertIn(Action, node_types)
        
        # Find the if node
        if_nodes = [node for node in ast.nodes if isinstance(node, If)]
        self.assertTrue(len(if_nodes) > 0)
        
        # Check the if node has a range node in its body
        if_node = if_nodes[0]
        range_nodes = [node for node in if_node.body if isinstance(node, Range)]
        self.assertTrue(len(range_nodes) > 0)


if __name__ == '__main__':
    unittest.main()