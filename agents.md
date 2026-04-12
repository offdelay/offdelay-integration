---
description: Project context for offdelay - Home Assistant integration and addon
---

# offdelay Project

This project is a **Home Assistant** ecosystem with two components:

1. **Home Assistant Custom Integration** (`custom_components/offdelay/`)
2. **Home Assistant Addon** (future step - will be added to `addon/`)

## Project Structure

```
offdelay/                    # Project root (will be renamed from offdelay-integration)
├── custom_components/        # HA custom component directory
│   └── offdelay/           # The custom integration code
├── addon/                   # HA Addon (future)
├── tests/                   # Unit tests
├── config/                  # Configuration schemas
└── scripts/                # Utility scripts
```

## Project Context

- **Type**: Home Assistant ecosystem (integration + addon)
- **Language**: Python
- **Framework**: Home Assistant Python integration framework

## Skills for This Project

When working on this project, agents should look for skills in the following order:

1. **Project-specific skills** (prefix: `home-assistant-*`)
   - e.g., `home-assistant-best-practices`
   - e.g., `home-assistant-unittest`
   - e.g., `home-assistant-addon` (for addon development)

2. **Generic skills** (no project prefix)
   - e.g., `unittest`, `python`, `api-development`, `docker`

## Agent Behavior

Agents working on this project should:
1. First load relevant skills (`skill` tool)
2. Look for skills matching "home-assistant" in the name
3. Also look for generic skills without project prefix
4. Follow Home Assistant integration patterns and best practices
5. When working on addon: also load addon-specific skills

## Key Project Directories

- `custom_components/offdelay/` - Main integration code (Python)
- `addon/` - Home Assistant Addon (future - Docker-based)
- `tests/` - Unit tests
- `config/` - Configuration schemas
- `scripts/` - Utility scripts