"""
Go template AST structures.

This module defines the Abstract Syntax Tree (AST) structures for Go text templates.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union


class Node(ABC):
    """Base class for all AST nodes."""
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor to process this node."""
        pass


class Template(Node):
    """Root node representing a complete template."""
    
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
    
    def accept(self, visitor):
        return visitor.visit_template(self)


class Text(Node):
    """Node representing plain text content."""
    
    def __init__(self, value: str):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_text(self)


class Action(Node):
    """Node representing a Go template action ({{ ... }})."""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def accept(self, visitor):
        return visitor.visit_action(self)


class Pipeline(Node):
    """Node representing a pipeline of commands."""
    
    def __init__(self, commands: List[Node]):
        self.commands = commands
    
    def accept(self, visitor):
        return visitor.visit_pipeline(self)


class Command(Node):
    """Node representing a command in a pipeline."""
    
    def __init__(self, identifier: str, arguments: List[Node] = None):
        self.identifier = identifier
        self.arguments = arguments or []
    
    def accept(self, visitor):
        return visitor.visit_command(self)


class Variable(Node):
    """Node representing a variable reference."""
    
    def __init__(self, name: str, fields: List[str] = None):
        self.name = name
        self.fields = fields or []
    
    def accept(self, visitor):
        return visitor.visit_variable(self)


class Literal(Node):
    """Node representing a literal value (string, number, etc.)."""
    
    def __init__(self, value: Any, type_: str):
        self.value = value
        self.type = type_  # 'string', 'number', 'boolean'
    
    def accept(self, visitor):
        return visitor.visit_literal(self)


class If(Node):
    """Node representing an if statement."""
    
    def __init__(self, condition: Node, body: List[Node], else_body: List[Node] = None):
        self.condition = condition
        self.body = body
        self.else_body = else_body or []
    
    def accept(self, visitor):
        return visitor.visit_if(self)


class Range(Node):
    """Node representing a range statement."""
    
    def __init__(self, sequence: Node, variables: List[str], body: List[Node], else_body: List[Node] = None):
        self.sequence = sequence
        self.variables = variables
        self.body = body
        self.else_body = else_body or []
    
    def accept(self, visitor):
        return visitor.visit_range(self)


class With(Node):
    """Node representing a with statement."""
    
    def __init__(self, value: Node, variable: Optional[str], body: List[Node], else_body: List[Node] = None):
        self.value = value
        self.variable = variable
        self.body = body
        self.else_body = else_body or []
    
    def accept(self, visitor):
        return visitor.visit_with(self)


class Define(Node):
    """Node representing a define statement."""
    
    def __init__(self, name: str, body: List[Node]):
        self.name = name
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_define(self)


class Block(Node):
    """Node representing a block statement."""
    
    def __init__(self, name: str, body: List[Node]):
        self.name = name
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_block(self)


class Comment(Node):
    """Node representing a comment."""
    
    def __init__(self, value: str):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_comment(self)