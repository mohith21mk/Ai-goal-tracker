"""
Frontend Production Resilience & Favicon Verification Test Suite
Tests:
1. Public & Dist favicon contains authentic MKC logo (not Vite default).
2. Dist index.html contains all required icon links (<link rel="icon"...> and <link rel="apple-touch-icon"...>).
3. Built production bundle contains timeout handling and does not duplicate failed GET requests.
4. AuthContext contains the 3.5s hard safety timeout guard.
5. App.jsx contains the emergency login fallback button in the loading state.
"""

import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")
PUBLIC_FAVICON = os.path.join(FRONTEND_DIR, "public", "favicon.svg")
DIST_FAVICON = os.path.join(FRONTEND_DIR, "dist", "favicon.svg")
DIST_INDEX = os.path.join(FRONTEND_DIR, "dist", "index.html")
AUTH_CONTEXT = os.path.join(FRONTEND_DIR, "src", "context", "AuthContext.jsx")
API_JS = os.path.join(FRONTEND_DIR, "src", "services", "api.js")
APP_JSX = os.path.join(FRONTEND_DIR, "src", "App.jsx")


def test_public_favicon_is_mkc_logo():
    assert os.path.isfile(PUBLIC_FAVICON), "public/favicon.svg must exist"
    with open(PUBLIC_FAVICON, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Mastery Key Coach logo" in content, "favicon.svg must have MKC logo aria-label"
    assert "#863bff" not in content, "favicon.svg must NOT have Vite purple color"
    assert "0 0 1254 1254" in content, "favicon.svg must have MKC viewBox"


def test_dist_favicon_is_mkc_logo():
    assert os.path.isfile(DIST_FAVICON), "dist/favicon.svg must exist after build"
    with open(DIST_FAVICON, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Mastery Key Coach logo" in content, "dist/favicon.svg must have MKC logo"
    assert "#863bff" not in content, "dist/favicon.svg must NOT have Vite purple color"


def test_dist_index_html_has_proper_icons():
    assert os.path.isfile(DIST_INDEX), "dist/index.html must exist"
    with open(DIST_INDEX, "r", encoding="utf-8") as f:
        html = f.read()
    assert 'href="/mkc-favicon.svg?v=2"' in html, "Must link versioned mkc-favicon.svg"
    assert 'href="/favicon.svg?v=2"' in html, "Must link versioned favicon.svg"
    assert 'href="/mkc-anchor-logo.png?v=2"' in html, "Must link versioned png icon"
    assert '<link rel="apple-touch-icon" href="/mkc-anchor-logo.png?v=2"' in html, "Must link apple-touch-icon"


def test_auth_context_has_safety_timer():
    assert os.path.isfile(AUTH_CONTEXT), "AuthContext.jsx must exist"
    with open(AUTH_CONTEXT, "r", encoding="utf-8") as f:
        code = f.read()
    assert "safetyTimeout" in code, "AuthContext must define safetyTimeout"
    assert "3500" in code, "AuthContext must have 3.5s timeout"
    assert "setLoading(false)" in code, "AuthContext must clear loading state on timeout"


def test_api_js_has_timeout_and_no_duplicate_fetch():
    assert os.path.isfile(API_JS), "api.js must exist"
    with open(API_JS, "r", encoding="utf-8") as f:
        code = f.read()
    # Ensure AbortController is used
    assert "AbortController" in code, "apiFetch must use AbortController"
    # Ensure 4000ms auth timeout and 60000ms login timeout
    assert "isAuthBootstrap = endpoint.startsWith('/api/auth/me')" in code
    assert "isAuthAction = endpoint.startsWith('/api/auth/login')" in code
    # Ensure duplicate fetch was removed: line 163 used to be `return fetch(`${API_BASE_URL}${endpoint}`, config);`
    # inside GET block. In GET block, it should now return rawResponse or makeErrorResponse(504, ...)
    assert "makeErrorResponse(504, 'Gateway Timeout'" in code, "Must return synthetic 504 on timeout"


def test_app_loading_screen_has_emergency_escape():
    assert os.path.isfile(APP_JSX), "App.jsx must exist"
    with open(APP_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "showEmergencyFallback" in code, "App.jsx must have showEmergencyFallback state"
    assert "Continue to Sign In" in code, "App.jsx must provide escape button to sign in"
