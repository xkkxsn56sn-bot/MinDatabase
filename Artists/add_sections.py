#!/usr/bin/env python3

with open("Giotto di Bondone.md", "r", encoding="utf-8") as f:
    content = f.read()

# Inserisci i titoli delle sezioni
replacements = [
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
]

for old, new in replacements:
    content = content.replace(old, new)

with open("Giotto di Bondone.md", "w", encoding="utf-8") as f:
    f.write(content)

print("Titoli delle sezioni aggiunti con successo!")
