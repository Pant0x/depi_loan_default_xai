import os, re

landing_path = 'frontend_web/templates/landing.html'
with open(landing_path, 'r', encoding='utf-8') as f:
    landing_content = f.read()

arch_start = landing_content.find('<!-- Architecture Section (Scroll Target) -->')
footer_start = landing_content.find('<!-- Footer -->', arch_start)

arch_html = landing_content[arch_start:footer_start]
head_html = landing_content[:landing_content.find('<body')]
footer_html = landing_content[footer_start:]

header_html = """<body class="min-h-full flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
    <!-- Navbar -->
    <header class="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div class="nav-container" style="max-width: 1400px;">
            <a href="/" class="logo-section" style="text-decoration:none;">
                <div class="logo-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                <span class="logo-text">LOAN XAI SYSTEM</span>
            </a>
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <a href="/" class="nav-link">Back to Home</a>
            </div>
        </div>
    </header>
"""

arch_page_content = head_html + header_html + '\n    <main class="main-layout" style="padding-bottom: 2rem;">\n' + arch_html + '\n    </main>\n' + footer_html

with open('frontend_web/templates/architecture.html', 'w', encoding='utf-8') as f:
    f.write(arch_page_content)

new_landing_content = landing_content[:arch_start] + '\n' + footer_html
with open(landing_path, 'w', encoding='utf-8') as f:
    f.write(new_landing_content)

print('Done')
