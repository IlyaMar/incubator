"""
Jinja transformer.

This module provides functionality to transform Go template AST to Jinja AST.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import jinja2
from jinja2 import nodes as jinja_nodes

from .go_ast import (
    Node, Template, Text, Action, Pipeline, Command, Variable,
    Literal, If, Range, With, Define, Block, Comment
)


class JinjaTransformer:
    """Transformer for converting Go template AST to Jinja AST."""
    
    def __init__(self):
        self.environment = jinja2.Environment()
        self.template_name = '<string>'
    
    def transform(self, node: Node) -> jinja_nodes.Node:
        """Transform a Go template AST node to a Jinja AST node."""
        return node.accept(self)
    
    def visit_template(self, node: Template) -> jinja_nodes.Template:
        """Transform a Template node."""
        body = []
        for child in node.nodes:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    body.extend(result)
                else:
                    body.append(result)
        
        return jinja_nodes.Template(body, lineno=1)
    
    def visit_text(self, node: Text) -> jinja_nodes.TemplateData:
        """Transform a Text node."""
        return jinja_nodes.TemplateData(node.value, lineno=1)
    
    def visit_action(self, node: Action) -> jinja_nodes.Output:
        """Transform an Action node."""
        expr = self.transform(node.pipeline)
        return jinja_nodes.Output([expr], lineno=1)
    
    def visit_pipeline(self, node: Pipeline) -> jinja_nodes.Node:
        """Transform a Pipeline node."""
        if len(node.commands) == 1:
            return self.transform(node.commands[0])
        
        # Handle pipeline as a series of filters
        result = self.transform(node.commands[0])
        
        for i in range(1, len(node.commands)):
            command = node.commands[i]
            if isinstance(command, Command):
                # Transform command to a filter
                filter_name = command.identifier
                args = []
                
                for arg in command.arguments:
                    args.append(self.transform(arg))
                
                result = jinja_nodes.Filter(
                    node=result,
                    name=jinja_nodes.Const(filter_name),
                    args=args,
                    kwargs=[],
                    dyn_args=None,
                    dyn_kwargs=None,
                    lineno=1
                )
            else:
                # If not a command, just transform and append
                result = jinja_nodes.Filter(
                    node=result,
                    name=jinja_nodes.Const('__pipe__'),
                    args=[self.transform(command)],
                    kwargs=[],
                    dyn_args=None,
                    dyn_kwargs=None,
                    lineno=1
                )
        
        return result
    
    def visit_command(self, node: Command) -> jinja_nodes.Call:
        """Transform a Command node."""
        args = []
        for arg in node.arguments:
            args.append(self.transform(arg))
        
        # Create a function call
        return jinja_nodes.Call(
            jinja_nodes.Name(node.identifier, 'load', lineno=1),
            args,
            [],
            None,
            None,
            lineno=1
        )
    
    def visit_variable(self, node: Variable) -> jinja_nodes.Node:
        """Transform a Variable node."""
        if node.name == '.':
            # The dot in Go templates refers to the current context
            if not node.fields:
                return jinja_nodes.Name('_', 'load', lineno=1)
            
            # Start with the first field
            result = jinja_nodes.Name(node.fields[0], 'load', lineno=1)
            
            # Add remaining fields as attribute lookups
            for field in node.fields[1:]:
                result = jinja_nodes.Getattr(result, field, 'load', lineno=1)
            
            return result
        else:
            # Start with the variable name
            result = jinja_nodes.Name(node.name, 'load', lineno=1)
            
            # Add fields as attribute lookups
            for field in node.fields:
                result = jinja_nodes.Getattr(result, field, 'load', lineno=1)
            
            return result
    
    def visit_literal(self, node: Literal) -> jinja_nodes.Const:
        """Transform a Literal node."""
        return jinja_nodes.Const(node.value, lineno=1)
    
    def visit_if(self, node: If) -> jinja_nodes.If:
        """Transform an If node."""
        test = self.transform(node.condition)
        body = []
        
        for child in node.body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    body.extend(result)
                else:
                    body.append(result)
        
        else_body = []
        for child in node.else_body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    else_body.extend(result)
                else:
                    else_body.append(result)
        
        return jinja_nodes.If(
            test=test,
            body=body,
            elif_=None,
            else_=else_body,
            lineno=1
        )
    
    def visit_range(self, node: Range) -> jinja_nodes.For:
        """Transform a Range node."""
        iter_expr = self.transform(node.sequence)
        
        # Determine target variable(s)
        if len(node.variables) == 0:
            # No explicit variables, use '_' as default
            target = jinja_nodes.Name('_', 'store', lineno=1)
        elif len(node.variables) == 1:
            # Single variable
            target = jinja_nodes.Name(node.variables[0], 'store', lineno=1)
        else:
            # Multiple variables (key, value)
            targets = []
            for var in node.variables:
                targets.append(jinja_nodes.Name(var, 'store', lineno=1))
            target = jinja_nodes.Tuple(targets, 'store', lineno=1)
        
        # Transform body
        body = []
        for child in node.body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    body.extend(result)
                else:
                    body.append(result)
        
        # Transform else body
        else_body = []
        for child in node.else_body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    else_body.extend(result)
                else:
                    else_body.append(result)
        
        return jinja_nodes.For(
            target=target,
            iter=iter_expr,
            body=body,
            else_=else_body,
            test=None,
            recursive=False,
            lineno=1
        )
    
    def visit_with(self, node: With) -> jinja_nodes.Node:
        """Transform a With node."""
        value_expr = self.transform(node.value)
        
        # Transform body
        body = []
        for child in node.body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    body.extend(result)
                else:
                    body.append(result)
        
        # Transform else body
        else_body = []
        for child in node.else_body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    else_body.extend(result)
                else:
                    else_body.append(result)
        
        if node.variable:
            # With variable assignment, create a set block
            assignment = jinja_nodes.Assign(
                jinja_nodes.Name(node.variable, 'store', lineno=1),
                value_expr,
                lineno=1
            )
            
            if else_body:
                # If there's an else clause, we need to use an If node
                return jinja_nodes.If(
                    test=value_expr,
                    body=[assignment] + body,
                    elif_=None,
                    else_=else_body,
                    lineno=1
                )
            else:
                # No else clause, just return the assignment and body
                return [assignment] + body
        else:
            # Without variable assignment, use an If node
            return jinja_nodes.If(
                test=value_expr,
                body=body,
                elif_=None,
                else_=else_body,
                lineno=1
            )
    
    def visit_define(self, node: Define) -> jinja_nodes.Macro:
        """Transform a Define node."""
        # Transform body
        body = []
        for child in node.body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    body.extend(result)
                else:
                    body.append(result)
        
        # Create a macro definition
        return jinja_nodes.Macro(
            name=node.name,
            args=[],
            defaults=[],
            body=body,
            lineno=1
        )
    
    def visit_block(self, node: Block) -> jinja_nodes.Block:
        """Transform a Block node."""
        # Transform body
        body = []
        for child in node.body:
            result = self.transform(child)
            if result is not None:
                if isinstance(result, list):
                    body.extend(result)
                else:
                    body.append(result)
        
        # Create a block
        return jinja_nodes.Block(
            name=node.name,
            body=body,
            scoped=False,
            lineno=1
        )
    
    def visit_comment(self, node: Comment) -> jinja_nodes.Comment:
        """Transform a Comment node."""
        return jinja_nodes.Comment(node.value, lineno=1)


def transform_template(template: Template) -> jinja_nodes.Template:
    """Transform a Go template AST to a Jinja AST."""
    transformer = JinjaTransformer()
    return transformer.transform(template)