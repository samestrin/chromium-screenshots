# 🚀 Social Media Posts

Here are some draft posts to help you share your project!

## 🐦 Twitter / X

**Option 1 (Developer Focused)**
Struggling to screenshot authenticated SPAs automatically? 📸

Most tools break when auth tokens live in localStorage. So I built one that doesn't.

Introducing chromium-screenshots:
✅ Inject localStorage/cookies
✅ Full-page captures
✅ MCP Server for Claude/AI agents
✅ Docker-ready

GitHub: https://github.com/samestrin/chromium-screenshots

#python #playwright #devtools #mcp #ai

---

**Option 2 (AI/MCP Focused)**
Just updated my Chromium Screenshot tool with native MCP support! 🤖✨

Now you can give Claude (or any MCP client) actual "eyes" on your web apps.
- "Take a screenshot of the dashboard"
- "Check if dark mode is broken"

It handles the auth tokens so your agent doesn't get stuck at the login screen.

Repo: https://github.com/samestrin/chromium-screenshots

## 💼 LinkedIn

**Subject: Solving the "Screenshotting Authenticated SPAs" Problem**

I've been working on a tool to solve a specific pain point in my automation workflows: taking high-fidelity screenshots of web apps that use client-side authentication (like Wasp, Firebase, or OpenSaaS).

Standard tools often fail because they can't easily inject `localStorage` or `sessionStorage` tokens. You end up with a screenshot of the login page instead of the dashboard.

**Chromium Screenshots** fixes this. It's a containerized service that lets you:
1.  Inject auth states (Cookies & LocalStorage)
2.  Capture full-page scrolling screenshots
3.  Integrate directly with AI agents via the Model Context Protocol (MCP)

I've just polished the repo with full docs, CI/CD, and examples.

Check it out on GitHub: https://github.com/samestrin/chromium-screenshots

#webdevelopment #automation #playwright #python #mcp #ai

## 🦀 Reddit (r/python, r/webdev, r/selfhosted)

**Title: I built a screenshot API that actually handles localStorage auth (and has MCP support)**

Hey everyone,

I needed a way to automate screenshots of my Wasp-based projects, but I kept hitting a wall: most screenshot APIs assume auth happens via Cookies. My apps (and many modern SPAs) store session tokens in `localStorage`.

So I built a simple, containerized service using FastAPI and Playwright to handle this.

**What it does:**
*   **Deep Auth Injection**: You can pass `localStorage` or `cookies` in the API request, and it injects them before navigation.
*   **MCP Support**: It runs as a Model Context Protocol server, so you can hook it up to Claude or other agents to give them "vision" of your authenticated apps.
*   **Dockerized**: easy to spin up alongside your other services.

It's been a lifesaver for my dev workflows and debugging AI agents.

Repo is here if anyone needs something similar: https://github.com/samestrin/chromium-screenshots

Feedback welcome!
