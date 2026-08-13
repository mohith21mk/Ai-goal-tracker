import os
import re

MAPPINGS = {
    '🔍': '<Search size={18} strokeWidth={1.8} />',
    '🔔': '<Bell size={18} strokeWidth={1.8} />',
    '✅': '<CheckCircle2 size={18} strokeWidth={1.8} />',
    '⚡': '<Zap size={18} strokeWidth={1.8} />',
    '👤': '<User size={18} strokeWidth={1.8} />',
    '⚙️': '<Settings2 size={18} strokeWidth={1.8} />',
    '🚪': '<LogOut size={18} strokeWidth={1.8} />',
    '👤+': '<UserPlus size={18} strokeWidth={1.8} />',
    '💬': '<MessageSquare size={18} strokeWidth={1.8} />',
    '✨': '<Sparkles size={18} strokeWidth={1.8} />',
    '📋': '<ClipboardList size={18} strokeWidth={1.8} />',
    '🌗': '<SunMoon size={18} strokeWidth={1.8} />',
    '🎯': '<Target size={18} strokeWidth={1.8} />',
    '🔥': '<Flame size={18} strokeWidth={1.8} />',
    'ℹ️': '<Info size={18} strokeWidth={1.8} />',
    '🚀': '<Rocket size={18} strokeWidth={1.8} />',
    '📈': '<TrendingUp size={18} strokeWidth={1.8} />',
    '📉': '<TrendingDown size={18} strokeWidth={1.8} />',
    '💰': '<Wallet size={18} strokeWidth={1.8} />',
    '→': '<ArrowRight size={18} strokeWidth={1.8} />',
    '🧠': '<Brain size={18} strokeWidth={1.8} />',
    '🛡️': '<Shield size={18} strokeWidth={1.8} />',
    '🌙': '<Moon size={18} strokeWidth={1.8} />',
    '🌐': '<Globe size={18} strokeWidth={1.8} />',
    '🔒': '<Lock size={18} strokeWidth={1.8} />',
    '💻': '<Monitor size={18} strokeWidth={1.8} />',
    '📱': '<Smartphone size={18} strokeWidth={1.8} />',
    '⚠️': '<TriangleAlert size={18} strokeWidth={1.8} />',
    '🔑': '<Key size={18} strokeWidth={1.8} />',
    '👁️': '<Eye size={18} strokeWidth={1.8} />',
    '🙈': '<EyeOff size={18} strokeWidth={1.8} />',
    '✉️': '<Mail size={18} strokeWidth={1.8} />',
    '🏆': '<Trophy size={18} strokeWidth={1.8} />',
    '❓': '<HelpCircle size={18} strokeWidth={1.8} />',
    '🗑️': '<Trash2 size={18} strokeWidth={1.8} />',
    '❤️': '<Heart size={18} strokeWidth={1.8} />',
}

IMPORTS_NEEDED = {
    'Search', 'Bell', 'CheckCircle2', 'Zap', 'User', 'Settings2', 'LogOut', 
    'UserPlus', 'MessageSquare', 'Sparkles', 'ClipboardList', 'SunMoon', 
    'Target', 'Flame', 'Info', 'Rocket', 'TrendingUp', 'TrendingDown', 
    'Wallet', 'ArrowRight', 'Brain', 'Shield', 'Moon', 'Globe', 'Lock', 
    'Monitor', 'Smartphone', 'TriangleAlert', 'Key', 'Eye', 'EyeOff', 
    'Mail', 'Trophy', 'HelpCircle', 'Trash2', 'Heart'
}

def process_file(filepath):
    if not os.path.exists(filepath):
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    used_imports = set()
    new_content = content
    
    # Simple replace
    for emoji, tag in MAPPINGS.items():
        # Replace string literal emojis
        if f'"{emoji}"' in new_content:
            new_content = new_content.replace(f'"{emoji}"', tag)
            used_imports.add(tag.split(' ')[0].replace('<', ''))
        # Replace JSX raw emojis
        if emoji in new_content:
            new_content = new_content.replace(emoji, tag)
            used_imports.add(tag.split(' ')[0].replace('<', ''))
            
    if used_imports:
        import_stmt = f"import {{ {', '.join(sorted(list(used_imports)))} }} from 'lucide-react';\n"
        # Add after last import
        imports = re.findall(r'^import .*?;?\n', new_content, re.MULTILINE)
        if imports:
            last_import = imports[-1]
            new_content = new_content.replace(last_import, last_import + import_stmt)
        else:
            new_content = import_stmt + new_content
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

files_to_process = [
    'frontend/src/components/TopBar.jsx',
    'frontend/src/components/Sidebar.jsx',
    'frontend/src/pages/Dashboard.jsx',
    'frontend/src/pages/Settings.jsx',
    'frontend/src/pages/Community.jsx',
    'frontend/src/components/StatCard.jsx',
    'frontend/src/components/MissionCard.jsx',
    'frontend/src/components/AICoachCard.jsx',
    'frontend/src/components/MasteryPlanCard.jsx',
]

for f in files_to_process:
    process_file(f)

print("Lucide upgrade complete")
