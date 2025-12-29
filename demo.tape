Output demo.gif

Set FontSize 16
Set Width 1200
Set Height 600
Set Padding 20
Set FontFamily "Menlo"
Set Theme "Catppuccin Mocha"

# Setup
Hide
Type "docker compose up -d"
Enter
Sleep 2s
Type "clear"
Enter
Show

# Title
Type "# chromium-screenshots: The production-ready screenshot API"
Sleep 1s
Enter
Sleep 1s
Type "curl http://localhost:8000/health"
Enter
Sleep 1s

# Demo 1: Simple Screenshot
Type "# 1. Take a simple full-page screenshot"
Sleep 500ms
Enter
Type "curl 'http://localhost:8000/screenshot?url=https://github.com&type=full_page' -o github.png"
Enter
Sleep 3s

# Demo 2: The "Impossible" Auth Shot (using JSON)
Type "# 2. Inject localStorage to capture an authenticated SPA"
Sleep 500ms
Enter
Type "curl -X POST http://localhost:8000/screenshot "
Enter
Type "  -H 'Content-Type: application/json' "
Enter
Type "  -d '{ "
Enter
Type "    "url": "https://example.com/dashboard", "
Enter
Type "    "localStorage": {"auth_token": "secret_123"}, "
Enter
Type "    "dark_mode": true "
Enter
Type "  }' -o dashboard.png"
Enter
Sleep 2s

# Cleanup
Hide
Type "rm github.png dashboard.png"
Enter
Type "docker compose down"
Enter
Show
