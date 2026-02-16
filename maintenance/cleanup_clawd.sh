#!/usr/bin/env bash
# Safe disk cleanup for Clawd — preserves memory snapshots
# Dry-run by default; pass --execute to actually delete

set -euo pipefail

DRY_RUN=true
if [[ "${1:-}" == "--execute" ]]; then
  DRY_RUN=false
fi

echo "=== Clawd Disk Cleanup ==="
echo "Dry run: $DRY_RUN"
df -h /home || true

# 1) Docker cleanup (if docker installed)
if command -v docker &>/dev/null; then
  echo -e "\n--- Docker cleanup ---"
  if $DRY_RUN; then
    echo "Would remove stopped containers:"
    docker ps -a --filter "status=exited" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}" | head -20
    echo "Would remove dangling images:"
    docker images --filter "dangling=true" --format "table {{.ID}}\t{{.Repository}}\t{{.Tag}}" | head -20
  else
    echo "Removing stopped containers..."
    docker container prune -f
    echo "Removing dangling images..."
    docker image prune -f
  fi
fi

# 2) Apt cache cleanup
echo -e "\n--- APT cache cleanup ---"
if $DRY_RUN; then
  echo "Would clean apt cache (approx $(du -sh /var/cache/apt 2>/dev/null || echo "unknown"))"
else
  apt-get clean
fi

# 3) Old log files in /var/log (older than 90 days)
echo -e "\n--- Old /var/log archives cleanup (>90 days) ---"
find /var/log -type f \( -name "*.gz" -o -name "*.log.*" \) -mtime +90 2>/dev/null | while read -r f; do
  if $DRY_RUN; then
    echo "Would delete: $f ($(du -h "$f" 2>/dev/null | cut -f1))"
  else
    rm -f "$f"
  fi
done

# 4) Journalctl vacuum (keep last 14 days)
echo -e "\n--- Journalctl vacuum (keep last 14 days) ---"
if $DRY_RUN; then
  echo "Would run: journalctl --vacuum-time=14d"
  echo "Current journal size: $(du -sh /var/log/journal 2>/dev/null || echo "journal not found")"
else
  journalctl --vacuum-time=14d
fi

# 5) Temporary files in /tmp and user cache (older than 7 days)
echo -e "\n--- Temporary files cleanup (>7 days) ---"
for dir in /tmp /var/tmp "$HOME/.cache" "$HOME/.npm" "$HOME/.local/share/Trash"; do
  if [[ -d "$dir" ]]; then
    if $DRY_RUN; then
      echo "Would clean: $dir"
      find "$dir" -type f -mtime +7 2>/dev/null | wc -l | xargs echo "  files older than 7 days:"
    else
      find "$dir" -type f -mtime +7 -delete 2>/dev/null || true
      find "$dir" -type d -empty -delete 2>/dev/null || true
    fi
  fi
done

# 6) Core dumps (if any)
echo -e "\n--- Core dumps cleanup ---"
if $DRY_RUN; then
  echo "Would remove core.* files in /var/lib/systemd/coredump"
  ls -lh /var/lib/systemd/coredump/core.* 2>/dev/null || echo "No core dumps found"
else
  rm -f /var/lib/systemd/coredump/core.* 2>/dev/null || true
fi

echo -e "\n=== Cleanup finished ==="
df -h /home || true
