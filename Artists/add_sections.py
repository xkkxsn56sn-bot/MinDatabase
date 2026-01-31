#!/usr/bin/env python3
"""
Section Heading Insertion Utility for MinDatabase Artist Files

This script inserts section headings (##) into markdown files by finding exact text matches
and replacing them with the text plus a heading. It's designed to add structure to flowing
prose that lacks formal section markers.

Usage:
    python3 add_sections.py <filename> [--dry-run]
    
    Arguments:
        filename    Path to the markdown file to process
        --dry-run   Preview changes without modifying the file
        
Example:
    python3 add_sections.py "Giotto di Bondone.md" --dry-run
    python3 add_sections.py "Coppo di Marcovaldo.md"

The script expects replacement patterns to be defined in the REPLACEMENTS dictionary below.
Edit this dictionary to customize section insertions for different files.
"""

import sys
import argparse
from pathlib import Path

# Define replacement patterns for each artist file
# Format: "filename": [(old_text, new_text), ...]
REPLACEMENTS = {
    "Giotto di Bondone.md": [
        ("early fourteenth-century Italy.\n\nGiotto's reputation drew", 
         "early fourteenth-century Italy.\n\n## Patrons and Commissions\n\nGiotto's reputation drew"),
        
        ("political and ecclesiastical boundaries.\n\nGiotto's painting style marked",
         "political and ecclesiastical boundaries.\n\n## Painting Style and Innovations\n\nGiotto's painting style marked"),
        
        ("visualizing the sacred.\n\nThe painter's artistic influences drew",
         "visualizing the sacred.\n\n## Artistic Influences\n\nThe painter's artistic influences drew"),
        
        ("for centuries.\n\nGiotto's travels, though not always",
         "for centuries.\n\n## Travels and Career\n\nGiotto's travels, though not always"),
        
        ("to achieve.\n\nIn the final phase of his life",
         "to achieve.\n\n## Death and Legacy\n\nIn the final phase of his life")
    ],
    # Add patterns for other artists here as needed
    # "Coppo di Marcovaldo.md": [
    #     ("pattern1", "pattern1\n\n## Section Title"),
    # ],
}


def add_sections(filepath, replacements, dry_run=False):
    """
    Add section headings to a markdown file using exact string replacement.
    
    Args:
        filepath: Path to the markdown file
        replacements: List of (old_text, new_text) tuples
        dry_run: If True, preview changes without writing to file
        
    Returns:
        Tuple of (success: bool, messages: list)
    """
    messages = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return False, [f"Error: File '{filepath}' not found"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    original_content = content
    replacements_made = 0
    
    for old_text, new_text in replacements:
        if old_text in content:
            content = content.replace(old_text, new_text, 1)  # Replace only first occurrence
            replacements_made += 1
            # Extract section title from new_text
            if "##" in new_text:
                section_title = new_text.split("##")[1].split("\n")[0].strip()
                messages.append(f"✓ Added section: {section_title}")
        else:
            messages.append(f"⚠ Pattern not found (skipped): {old_text[:60]}...")
    
    if replacements_made == 0:
        messages.append("No replacements made - all patterns already present or not found")
        return False, messages
    
    if dry_run:
        messages.append(f"\n[DRY RUN] Would make {replacements_made} replacement(s)")
        messages.append("Run without --dry-run to apply changes")
        return True, messages
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        messages.append(f"\n✓ Successfully updated '{filepath}' ({replacements_made} section(s) added)")
        return True, messages
    except Exception as e:
        return False, [f"Error writing file: {e}"]


def main():
    parser = argparse.ArgumentParser(
        description="Add section headings to MinDatabase artist markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 add_sections.py "Giotto di Bondone.md" --dry-run
  python3 add_sections.py "Coppo di Marcovaldo.md"
  
To add patterns for a new artist, edit the REPLACEMENTS dictionary in this script.
        """
    )
    parser.add_argument("filename", help="Name of the markdown file to process")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without modifying the file")
    
    args = parser.parse_args()
    
    # Get replacements for this file
    if args.filename not in REPLACEMENTS:
        print(f"Error: No replacement patterns defined for '{args.filename}'")
        print(f"\nAvailable patterns for:")
        for filename in REPLACEMENTS.keys():
            print(f"  - {filename}")
        print("\nTo add patterns for this file, edit the REPLACEMENTS dictionary in add_sections.py")
        sys.exit(1)
    
    replacements = REPLACEMENTS[args.filename]
    
    # Process the file
    success, messages = add_sections(args.filename, replacements, args.dry_run)
    
    # Print results
    for msg in messages:
        print(msg)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
