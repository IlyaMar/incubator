#!/usr/bin/env python3
"""
Example script to convert the example templates.
"""

import os
import sys
import argparse

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from go_to_jinja.go_parser import parse_template
from go_to_jinja.jinja_transformer import transform_template
from go_to_jinja.jinja_renderer import render_template


def convert_file(input_file, output_file=None):
    """Convert a Go template file to a Jinja template file."""
    print(f"Converting {input_file}...")
    
    # Read input file
    with open(input_file, 'r') as f:
        input_content = f.read()
    
    # Parse Go template
    go_ast = parse_template(input_content)
    
    # Transform to Jinja AST
    jinja_ast = transform_template(go_ast)
    
    # Render Jinja template
    jinja_template = render_template(jinja_ast)
    
    # Write output
    if output_file:
        with open(output_file, 'w') as f:
            f.write(jinja_template)
        print(f"Output written to {output_file}")
    else:
        print("\nConverted template:")
        print("=" * 80)
        print(jinja_template)
        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert example Go templates to Jinja templates'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for converted templates'
    )
    
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all .tmpl files in the examples directory
    for filename in os.listdir(script_dir):
        if filename.endswith('.tmpl'):
            input_file = os.path.join(script_dir, filename)
            
            if args.output_dir:
                # Create output directory if it doesn't exist
                if not os.path.exists(args.output_dir):
                    os.makedirs(args.output_dir)
                
                # Create output file path
                output_file = os.path.join(
                    args.output_dir,
                    os.path.splitext(filename)[0] + '.j2'
                )
                
                convert_file(input_file, output_file)
            else:
                convert_file(input_file)


if __name__ == '__main__':
    main()