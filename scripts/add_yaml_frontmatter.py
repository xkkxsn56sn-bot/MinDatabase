#!/usr/bin/env python3
"""
Bulk YAML Front Matter Addition Script for MinDatabase Artist Files

This script automatically adds YAML front matter to all artist biography markdown files
that are missing it. It preserves the original content and adds proper Jekyll metadata.

Usage:
    python3 scripts/add_yaml_frontmatter.py

Author: Comet (Perplexity AI Assistant)
Date: 2026-02-15
"""

import os
import re
from pathlib import Path

def has_yaml_frontmatter(content):
    """Check if content already has YAML front matter."""
    return content.startswith('---\n') or content.startswith('---\r\n')

def extract_title_from_filename(filename):
    """Extract artist name from filename."""
    # Remove .md extension
    name = filename.replace('.md', '')
    return name

def get_century_from_path(filepath):
    """Extract century from directory path."""
    parts = filepath.parts
    for part in parts:
        if 'century' in part.lower():
            return part
    return "Unknown"

def add_frontmatter_to_file(filepath):
    """Add YAML front matter to a single markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has front matter
        if has_yaml_frontmatter(content):
            print(f"✓ Skipped (already has front matter): {filepath.name}")
            return False
        
        # Extract metadata
        title = extract_title_from_filename(filepath.name)
        period = get_century_from_path(filepath)
        
        # Create YAML front matter
        frontmatter = f"""---
layout: default
title: \"{title}\"
author: {title}
period: {period}
category: artists
---

"""
        
        # Combine front matter with original content
        new_content = frontmatter + content
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Added front matter: {filepath.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing {filepath.name}: {e}")
        return False

def process_artists_directory():
    """Process all artist files in Content/Artists directory."""
    # Get repository root (assuming script is in scripts/ folder)
    repo_root = Path(__file__).parent.parent
    artists_dir = repo_root / 'Content' / 'Artists'
    
    if not artists_dir.exists():
        print(f"Error: Artists directory not found at {artists_dir}")
        return
    
    print(f"Searching for artist biography files in: {artists_dir}\n")
    
    # Find all .md files recursively
    md_files = list(artists_dir.rglob('*.md'))
    
    if not md_files:
        print("No markdown files found.")
        return
    
    print(f"Found {len(md_files)} markdown files.\n")
    
    # Process each file
    modified_count = 0
    skipped_count = 0
    
    for filepath in sorted(md_files):
        if add_frontmatter_to_file(filepath):
            modified_count += 1
        else:
            skipped_count += 1
    
    print(f"\n" + "="*60)
    print(f"Summary:")
    print(f"  Modified: {modified_count} files")
    print(f"  Skipped:  {skipped_count} files")
    print(f"  Total:    {len(md_files)} files")
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("MinDatabase - Bulk YAML Front Matter Addition")
    print("="*60 + "\n")
    
    process_artists_directory()
    
    print("\nScript completed successfully!")
    print("\nNext steps:")
    print("1. Review the changes with: git diff")
    print("2. Commit the changes: git add Content/Artists/")
    print("3. Push to trigger Jekyll build: git commit -m 'Add YAML front matter to all artist files' && git push")
