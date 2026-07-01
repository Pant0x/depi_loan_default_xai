import os
import re

html_path = 'frontend_web/templates/landing.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Map of exact alt names to the image filenames
pfps = {
    'Ezzeldeen Mahmoud Qutb': 'Ezzeldeen Mahmoud Qutb.jpg',
    'Karim Abdelmonem Fayez': 'Karim Abdelmonem Fayez.png',
    'Mostafa Ali': 'Mostafa Ali.png',
    'Mohammed Hassan': 'Mohammed Hassan.png',
    'Mohamed Ashraf': 'Mohamed Ashraf.png'
}

for name, filename in pfps.items():
    # Find the img tag with this alt
    pattern = rf'<img src="" alt="{name}" class="team-pfp-img" style="display: none;'
    replacement = rf'<img src="{{{{ url_for(\'static\', filename=\'images/team/{filename}\') }}}}" alt="{name}" class="team-pfp-img" style="'
    
    html = re.sub(pattern, replacement, html)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML updated successfully!")
