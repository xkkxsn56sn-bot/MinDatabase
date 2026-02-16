#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per aggiornare il layout di tutti i file degli artisti
Aggiunge il nuovo front matter con il layout artist-profile
"""

import os
import re
from pathlib import Path

def extract_frontmatter(content):
    """Estrae il front matter esistente dal contenuto"""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, content

def parse_frontmatter(fm_text):
    """Converte il front matter in un dizionario"""
    fm_dict = {}
    if not fm_text:
        return fm_dict
    
    for line in fm_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            fm_dict[key.strip()] = value.strip().strip('"\'')
    return fm_dict

def extract_dates_from_content(content):
    """Cerca di estrarre le date dal contenuto dell'articolo"""
    # Cerca pattern come "698 until his death in 721" o "(650-721)" 
    patterns = [
        r'(\d{3,4})[–-](\d{3,4})',  # 698-721 o 698–721
        r'\((\d{3,4})[–-](\d{3,4})\)',  # (698-721)
        r'ca\.?\s*(\d{3,4})[–-](\d{3,4})',  # ca. 698-721
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content[:1000])  # Cerca nei primi 1000 caratteri
        if match:
            return f"ca. {match.group(1)}–{match.group(2)}"
    
    return ""

def extract_century_from_path(filepath):
    """Estrae il secolo dal path del file"""
    path_parts = str(filepath).split(os.sep)
    for part in path_parts:
        if 'century' in part.lower():
            return part
    return ""

def create_new_frontmatter(old_fm, filepath, content):
    """Crea il nuovo front matter con tutti i campi necessari"""
    # Estrai informazioni dal vecchio front matter
    title = old_fm.get('title', filepath.stem)
    
    # Estrai il secolo dal path
    century = extract_century_from_path(filepath)
    
    # Cerca di estrarre le date dal contenuto
    dates = extract_dates_from_content(content)
    
    # Crea il nuovo front matter
    new_fm = {
        'layout': 'artist-profile',
        'title': f'"{title}"',
        'author': title,
        'period': century if century else 'Medieval',
        'category': 'artists',
        'role': 'Artist, Illuminator',  # Default - da personalizzare manualmente
        'dates': dates if dates else '',
        'key_works': [],
        'related_entries': []
    }
    
    return new_fm

def format_frontmatter(fm_dict):
    """Formatta il dizionario in YAML front matter"""
    lines = ['---']
    
    # Campi semplici
    simple_fields = ['layout', 'title', 'author', 'period', 'category', 'role']
    for field in simple_fields:
        if field in fm_dict and fm_dict[field]:
            lines.append(f'{field}: {fm_dict[field]}')
    
    # Dates (solo se presente)
    if 'dates' in fm_dict and fm_dict['dates']:
        lines.append(f'dates: "{fm_dict["dates"]}"')
    
    # Liste
    if 'key_works' in fm_dict:
        lines.append('key_works:')
        if fm_dict['key_works']:
            for work in fm_dict['key_works']:
                lines.append(f'  - "{work}"')
        else:
            lines.append('  # - "Opera principale"')
    
    if 'related_entries' in fm_dict:
        lines.append('related_entries:')
        if fm_dict['related_entries']:
            for entry in fm_dict['related_entries']:
                lines.append(f'  - "{entry}"')
        else:
            lines.append('  # - "Voce correlata"')
    
    lines.append('---')
    return '\n'.join(lines)

def update_artist_file(filepath):
    """Aggiorna un singolo file artista"""
    print(f"Elaborando: {filepath.name}")
    
    try:
        # Leggi il contenuto
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Estrai front matter esistente e contenuto
        old_fm_text, body = extract_frontmatter(content)
        old_fm = parse_frontmatter(old_fm_text)
        
        # Se già usa artist-profile, salta
        if old_fm.get('layout') == 'artist-profile':
            print(f"  ↳ Già aggiornato, salto")
            return False
        
        # Crea nuovo front matter
        new_fm = create_new_frontmatter(old_fm, filepath, body)
        new_fm_text = format_frontmatter(new_fm)
        
        # Crea nuovo contenuto
        new_content = f"{new_fm_text}\n\n{body.strip()}\n"
        
        # Salva
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ Aggiornato con successo")
        return True
        
    except Exception as e:
        print(f"  ✗ Errore: {e}")
        return False

def main():
    """Funzione principale"""
    # Trova la cartella Content/Artists
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    artists_dir = project_root / 'Content' / 'Artists'
    
    if not artists_dir.exists():
        print(f"❌ Cartella non trovata: {artists_dir}")
        return
    
    print(f"📁 Cerco file in: {artists_dir}")
    print("=" * 60)
    
    # Trova tutti i file .md nelle sottocartelle
    md_files = list(artists_dir.rglob('*.md'))
    
    if not md_files:
        print("❌ Nessun file .md trovato")
        return
    
    print(f"📄 Trovati {len(md_files)} file\n")
    
    # Aggiorna ogni file
    updated = 0
    skipped = 0
    
    for filepath in sorted(md_files):
        if update_artist_file(filepath):
            updated += 1
        else:
            skipped += 1
        print()
    
    # Riepilogo
    print("=" * 60)
    print(f"✅ Completato!")
    print(f"   Aggiornati: {updated}")
    print(f"   Saltati: {skipped}")
    print(f"   Totale: {len(md_files)}")
    print("\n⚠️  Ricorda di:")
    print("   1. Verificare i file modificati")
    print("   2. Personalizzare i campi 'role', 'key_works', 'related_entries'")
    print("   3. Fare commit e push delle modifiche")

if __name__ == '__main__':
    main()
