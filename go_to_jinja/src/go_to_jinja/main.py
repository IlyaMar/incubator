"""
Main application module.

This module provides the main entry point for the go-to-jinja application.
"""

import sys
import os
import argparse
import logging
from typing import Optional, List, Dict, Any

from .go_parser import parse_template
from .jinja_transformer import transform_template
from .jinja_renderer import render_template


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def convert_template(input_content: str) -> str:
    """Convert a Go template to a Jinja template."""
    logging.debug("Parsing Go template...")
    go_ast = parse_template(input_content)
    
    logging.debug("Transforming to Jinja AST...")
    jinja_ast = transform_template(go_ast)
    
    logging.debug("Rendering Jinja template...")
    jinja_template = render_template(jinja_ast)
    
    return jinja_template


def process_file(input_file: str, output_file: Optional[str] = None) -> bool:
    """Process a single file."""
    try:
        logging.info(f"Processing file: {input_file}")
        
        # Read input file
        with open(input_file, 'r') as f:
            input_content = f.read()
        
        # Convert template
        jinja_template = convert_template(input_content)
        
        # Write output
        if output_file:
            with open(output_file, 'w') as f:
                f.write(jinja_template)
            logging.info(f"Output written to: {output_file}")
        else:
            print(jinja_template)
            logging.info("Output written to stdout")
        
        return True
    
    except Exception as e:
        logging.error(f"Error processing file {input_file}: {str(e)}")
        return False


def process_directory(input_dir: str, output_dir: str, recursive: bool = False) -> bool:
    """Process all files in a directory."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    success = True
    
    for item in os.listdir(input_dir):
        input_path = os.path.join(input_dir, item)
        output_path = os.path.join(output_dir, item)
        
        if os.path.isfile(input_path):
            # Process file
            if item.endswith('.tmpl') or item.endswith('.tpl') or item.endswith('.gotmpl'):
                # Change extension to .j2 for Jinja templates
                output_path = os.path.splitext(output_path)[0] + '.j2'
                if not process_file(input_path, output_path):
                    success = False
        elif os.path.isdir(input_path) and recursive:
            # Process subdirectory recursively
            if not process_directory(input_path, output_path, recursive):
                success = False
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Go templates to Jinja templates'
    )
    
    parser.add_argument(
        'input',
        help='Input file or directory'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file or directory (default: stdout for single file, or input directory with .j2 extension)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process directories recursively'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Process input
    if os.path.isfile(args.input):
        # Process single file
        if not process_file(args.input, args.output):
            sys.exit(1)
    elif os.path.isdir(args.input):
        # Process directory
        output_dir = args.output if args.output else args.input
        if not process_directory(args.input, output_dir, args.recursive):
            sys.exit(1)
    else:
        logging.error(f"Input not found: {args.input}")
        sys.exit(1)
    
    logging.info("Conversion completed successfully")


if __name__ == '__main__':
    main()