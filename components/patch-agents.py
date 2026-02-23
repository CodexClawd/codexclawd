#!/usr/bin/env python3
"""
Patch all OpenClaw agent configs to enable context retention hooks.

Adds to each agent's config.json:
- pre_prompt_hook: semantic-recall.py
- post_compaction_hook: post-compaction-injector.py
"""

import json
from pathlib import Path
import shutil
import sys

WORKSPACE = Path("/home/boss/.openclaw/workspace")
AGENTS_DIR = WORKSPACE / "agents"
HOOKS_DIR = WORKSPACE / "components"

pre_prompt_hook = str(HOOKS_DIR / "semantic-recall.py")
post_compaction_hook = str(HOOKS_DIR / "post-compaction-injector.py")

def patch_agent_config(agent_path):
    config_file = agent_path / "agent" / "config.json"
    if not config_file.exists():
        print(f"  ⚠️  No config.json in {agent_path.name}")
        return False

    # Backup
    backup = config_file.with_suffix(".json.backup")
    shutil.copy2(config_file, backup)

    # Load
    with open(config_file, "r") as f:
        config = json.load(f)

    # Modify
    changed = False
    if "pre_prompt_hook" not in config:
        config["pre_prompt_hook"] = pre_prompt_hook
        changed = True
    if "post_compaction_hook" not in config:
        config["post_compaction_hook"] = post_compaction_hook
        changed = True

    if changed:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"  ✅ Patched {agent_path.name}")
        return True
    else:
        print(f"  ℹ️  {agent_path.name} already had hooks")
        return False

def main():
    agents = list(AGENTS_DIR.iterdir())
    if not agents:
        print("No agents found in workspace/agents/")
        sys.exit(1)

    print(f"Found {len(agents)} agents. Patching...")
    patched = 0
    for agent_dir in agents:
        if agent_dir.is_dir():
            if patch_agent_config(agent_dir):
                patched += 1

    print(f"\nDone. {patched} agents patched. Backups saved as *.backup")
    print("\nNext steps:")
    print("1. Ensure hooks are executable: chmod +x components/*.py")
    print("2. Add cron jobs for hourly summarizer and vector rebuild")
    print("3. Run: components/vector-memory.py rebuild")
    print("4. Restart OpenClaw gateway: openclaw gateway restart")

if __name__ == "__main__":
    main()
