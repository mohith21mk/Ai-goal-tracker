import re

# 1. SIDEBAR
with open('frontend/src/components/Sidebar.jsx', 'r', encoding='utf-8') as f:
    sidebar = f.read()

with open('old_sidebar.txt', 'r', encoding='utf-16') as f:
    old_sidebar = f.read()

# Extract old navItems
old_nav_match = re.search(r'(const rawNavItems = \[.*?\];)', old_sidebar, re.DOTALL)
if old_nav_match:
    sidebar = re.sub(r'const rawNavItems = \[.*?\];', old_nav_match.group(1).replace('\\', '\\\\'), sidebar, flags=re.DOTALL)
    # The new sidebar might not have rawNavItems, it had NAV_ITEMS? No, the new Sidebar had rawNavItems too.
    # Wait, the new Sidebar has: `const NAV_ITEMS = [` (wait, the old had `rawNavItems`). Let me check if new has `rawNavItems` or `NAV_ITEMS`.
    # I will replace whichever it has.
    sidebar = re.sub(r'const NAV_ITEMS = \[.*?\];', old_nav_match.group(1).replace('\\', '\\\\'), sidebar, flags=re.DOTALL)
    sidebar = sidebar.replace('NAV_ITEMS.map', 'rawNavItems.map')

# Extract old brand
old_brand_match = re.search(r'(<div className="sidebar-brand">.*?</div>)', old_sidebar, re.DOTALL)
if old_brand_match:
    sidebar = re.sub(r'<div className="sidebar-brand">.*?</div>', old_brand_match.group(1).replace('\\', '\\\\'), sidebar, count=1, flags=re.DOTALL)

# Extract old legacy card
old_legacy_match = re.search(r'(<div className="sidebar-legacy-card glass-panel">.*?</div>)', old_sidebar, re.DOTALL)
if old_legacy_match:
    sidebar = re.sub(r'<div className="sidebar-legacy-card glass-panel">.*?</div>', old_legacy_match.group(1).replace('\\', '\\\\'), sidebar, flags=re.DOTALL)

# Remove lucide imports
sidebar = re.sub(r'import \{.*?\} from \'lucide-react\';\n?', '', sidebar)

with open('frontend/src/components/Sidebar.jsx', 'w', encoding='utf-8') as f:
    f.write(sidebar)

# 2. TOPBAR
with open('frontend/src/components/TopBar.jsx', 'r', encoding='utf-8') as f:
    topbar = f.read()

topbar = re.sub(r'import \{.*?\} from \'lucide-react\';\n?', '', topbar)
topbar = re.sub(r'<Search size=\{.*?/>', '🔍', topbar)
topbar = re.sub(r'<Search className=.*?/>', '🔍', topbar)
topbar = re.sub(r'<Bell size=\{.*?/>', '🔔', topbar)
topbar = re.sub(r'<CheckCheck size=\{.*?/>', '✅', topbar)
topbar = re.sub(r'<Zap size=\{.*?/>', '⚡', topbar)
topbar = re.sub(r'<User size=\{.*?/>', '👤', topbar)
topbar = re.sub(r'<Settings2 size=\{.*?/>', '⚙️', topbar)
topbar = re.sub(r'<LogOut size=\{.*?/>', '🚪', topbar)

topbar = re.sub(r'<MessageCircle.*?/>', '💬', topbar)
topbar = re.sub(r'<Target.*?/>', '🎯', topbar)
topbar = re.sub(r'<Flame.*?/>', '🔥', topbar)
topbar = re.sub(r'<Info.*?/>', 'ℹ️', topbar)

with open('frontend/src/components/TopBar.jsx', 'w', encoding='utf-8') as f:
    f.write(topbar)

# 3. DASHBOARD
with open('frontend/src/pages/Dashboard.jsx', 'r', encoding='utf-8') as f:
    dashboard = f.read()

dashboard = re.sub(r'import \{.*?\} from \'lucide-react\';\n?', '', dashboard)
dashboard = re.sub(r'<CheckCircle2.*?/>', '"✅"', dashboard)
dashboard = re.sub(r'<Zap.*?/>', '"⚡"', dashboard)
dashboard = re.sub(r'<Rocket.*?/>', '"🚀"', dashboard)
dashboard = re.sub(r'<Target.*?/>', '"🎯"', dashboard)
dashboard = re.sub(r'<TrendingUp.*?/>', '"📈"', dashboard)
dashboard = re.sub(r'<TrendingDown.*?/>', '"📉"', dashboard)
dashboard = re.sub(r'<Wallet.*?/>', '"💰"', dashboard)
dashboard = re.sub(r'<Flame.*?/>', '"🔥"', dashboard)
dashboard = re.sub(r'<ArrowRight.*?/>', '→', dashboard)

# Fix quotes if they doubled up
dashboard = dashboard.replace('""', '"')

with open('frontend/src/pages/Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(dashboard)

# 4. SETTINGS
with open('frontend/src/pages/Settings.jsx', 'r', encoding='utf-8') as f:
    settings = f.read()
settings = re.sub(r'import \{.*?\} from \'lucide-react\';\n?', '', settings)
settings = re.sub(r'<Zap.*?/>', '⚡', settings)
settings = re.sub(r'<User.*?/>', '👤', settings)
settings = re.sub(r'<Settings2.*?/>', '⚙️', settings)
settings = re.sub(r'<LogOut.*?/>', '🚪', settings)
settings = re.sub(r'<Shield.*?/>', '🛡️', settings)
settings = re.sub(r'<Bell.*?/>', '🔔', settings)
settings = re.sub(r'<Moon.*?/>', '🌙', settings)
settings = re.sub(r'<Globe.*?/>', '🌐', settings)
settings = re.sub(r'<Lock.*?/>', '🔒', settings)
settings = re.sub(r'<Monitor.*?/>', '💻', settings)
settings = re.sub(r'<Smartphone.*?/>', '📱', settings)
settings = re.sub(r'<TriangleAlert.*?/>', '⚠️', settings)
settings = re.sub(r'<Key.*?/>', '🔑', settings)
settings = re.sub(r'<Eye.*?/>', '👁️', settings)
settings = re.sub(r'<EyeOff.*?/>', '🙈', settings)
settings = re.sub(r'<Mail.*?/>', '✉️', settings)
settings = re.sub(r'<ArrowRight.*?/>', '→', settings)

with open('frontend/src/pages/Settings.jsx', 'w', encoding='utf-8') as f:
    f.write(settings)

# 5. COMMUNITY
with open('frontend/src/pages/Community.jsx', 'r', encoding='utf-8') as f:
    comm = f.read()
comm = re.sub(r'import \{.*?\} from \'lucide-react\';\n?', '', comm)
comm = re.sub(r'<Globe.*?/>', '"🌐"', comm)
comm = re.sub(r'<MessageCircle.*?/>', '"💬"', comm)
comm = re.sub(r'<Trophy.*?/>', '"🏆"', comm)
comm = re.sub(r'<Brain.*?/>', '"🧠"', comm)
comm = re.sub(r'<HelpCircle.*?/>', '"❓"', comm)
comm = re.sub(r'<TriangleAlert.*?/>', '⚠️', comm)
comm = re.sub(r'<Trash2.*?/>', '🗑️', comm)
comm = re.sub(r'<Heart.*?/>', '❤️', comm)
comm = re.sub(r'<MessageSquare.*?/>', '💬', comm)

with open('frontend/src/pages/Community.jsx', 'w', encoding='utf-8') as f:
    f.write(comm)

print('Success')
