import re

# 1. SIDEBAR
with open('frontend/src/components/Sidebar.jsx', 'r', encoding='utf-8') as f:
    sidebar = f.read()

# Remove multiline lucide-react imports
sidebar = re.sub(r'import\s+\{.*?\}\s+from\s+[\'"]lucide-react[\'"];', '', sidebar, flags=re.DOTALL)
# Also the unused array was probably kept
sidebar = re.sub(r'const NAV_ITEMS = \[.*?\];', '', sidebar, flags=re.DOTALL)

with open('frontend/src/components/Sidebar.jsx', 'w', encoding='utf-8') as f:
    f.write(sidebar)

# 2. TOPBAR
with open('frontend/src/components/TopBar.jsx', 'r', encoding='utf-8') as f:
    topbar = f.read()

topbar = re.sub(r'import\s+\{.*?\}\s+from\s+[\'"]lucide-react[\'"];', '', topbar, flags=re.DOTALL)
topbar = re.sub(r'<UserPlus.*?/>', '"👤+"', topbar)
topbar = re.sub(r'<MessageSquare.*?/>', '"💬"', topbar)
topbar = re.sub(r'<Sparkles.*?/>', '"✨"', topbar)
topbar = re.sub(r'<CheckCircle2.*?/>', '"✅"', topbar)
topbar = re.sub(r'<ClipboardList.*?/>', '"📋"', topbar)
topbar = re.sub(r'<SunMoon.*?/>', '"🌗"', topbar)

# Fix previously replaced ones that might have been outside quotes if they were in JSX brackets
# Actually, TopBar mostly used icons like {getNotificationIcon(n.type)} returning <Icon />
# I already replaced them with emojis. Wait, if it returns an emoji it should be returned as a string or wrapped in a span.
# In JS, return 💬 is invalid, return "💬" is valid.
# Let's fix missing quotes on emojis in JS blocks:
topbar = re.sub(r'return 💬', 'return "💬"', topbar)
topbar = re.sub(r'return 🎯', 'return "🎯"', topbar)
topbar = re.sub(r'return 🔥', 'return "🔥"', topbar)
topbar = re.sub(r'return ℹ️', 'return "ℹ️"', topbar)

with open('frontend/src/components/TopBar.jsx', 'w', encoding='utf-8') as f:
    f.write(topbar)

# 3. DASHBOARD
with open('frontend/src/pages/Dashboard.jsx', 'r', encoding='utf-8') as f:
    dashboard = f.read()

dashboard = re.sub(r'import\s+\{.*?\}\s+from\s+[\'"]lucide-react[\'"];', '', dashboard, flags=re.DOTALL)

with open('frontend/src/pages/Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(dashboard)

# 4. SETTINGS
with open('frontend/src/pages/Settings.jsx', 'r', encoding='utf-8') as f:
    settings = f.read()

settings = re.sub(r'import\s+\{.*?\}\s+from\s+[\'"]lucide-react[\'"];', '', settings, flags=re.DOTALL)

# Fix missing quotes around emojis replaced in JSX where they were components
# E.g. <span className="settings-card-icon">⚠️</span> is fine in JSX.
# But {⚠️} is not fine. Let's find occurrences of {⚠️} and make them {"⚠️"}
settings = re.sub(r'\{([⚡👤⚙️🚪🛡️🔔🌙🌐🔒💻📱⚠️🔑👁️🙈✉️→]+)\}', r'{"\1"}', settings)

# Specifically for Settings.jsx line 332:
# It's probably `icon={<TriangleAlert/>}` becoming `icon={⚠️}`.
settings = settings.replace('icon={⚠️}', 'icon={"⚠️"}')
settings = settings.replace('icon={🔔}', 'icon={"🔔"}')
settings = settings.replace('icon={⚡}', 'icon={"⚡"}')
settings = settings.replace('icon={👤}', 'icon={"👤"}')
settings = settings.replace('icon={⚙️}', 'icon={"⚙️"}')
settings = settings.replace('icon={🚪}', 'icon={"🚪"}')
settings = settings.replace('icon={🛡️}', 'icon={"🛡️"}')
settings = settings.replace('icon={🌙}', 'icon={"🌙"}')
settings = settings.replace('icon={🌐}', 'icon={"🌐"}')
settings = settings.replace('icon={🔒}', 'icon={"🔒"}')
settings = settings.replace('icon={💻}', 'icon={"💻"}')
settings = settings.replace('icon={📱}', 'icon={"📱"}')
settings = settings.replace('icon={🔑}', 'icon={"🔑"}')
settings = settings.replace('icon={👁️}', 'icon={"👁️"}')
settings = settings.replace('icon={🙈}', 'icon={"🙈"}')
settings = settings.replace('icon={✉️}', 'icon={"✉️"}')

with open('frontend/src/pages/Settings.jsx', 'w', encoding='utf-8') as f:
    f.write(settings)

print("Success")
