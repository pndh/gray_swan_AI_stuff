#!/usr/bin/env bash
# Read-only recon for the authorized DPI work-test sandbox.
# Copy-paste over SSH or scp into the sandbox and run: bash recon_dump.sh
# Writes nothing except (optionally) a scratch dir under /tmp.
set -u

sec() { printf '\n\n===== %s =====\n' "$1"; }

sec "identity / host"
id; uname -a; hostname; pwd

sec "task surface"
ls -la
ls -la /home 2>/dev/null
cat /etc/motd 2>/dev/null
find / -maxdepth 3 \( -iname "*task*" -o -iname "*objective*" -o -iname "*README*" \) -newer /etc/hostname 2>/dev/null | head -30

sec "environment (names only, values redacted)"
env | sed 's/=.*/=<redacted>/' | sort

sec "processes"
ps aux --forest 2>/dev/null | head -60

sec "agent binaries / configs (existence + version only)"
for b in claude codex gemini aider cursor openhands; do
  command -v "$b" >/dev/null 2>&1 && echo "$b -> $(command -v "$b") $("$b" --version 2>/dev/null | head -1)"
done
for d in "$HOME/.claude" "$HOME/.codex" "$HOME/.config/claude" "$HOME/.config/codex"; do
  [ -e "$d" ] && { echo "--- $d"; find "$d" -maxdepth 2 -type f 2>/dev/null | head -20; }
done

sec "project config surface (agent-writable?)"
find . -maxdepth 3 \( -name "AGENTS.md" -o -name "CLAUDE.md" -o -name ".vscode" -o -name "Makefile" -o -name "*.code-workspace" -o -name ".mcp.json" -o -name "settings.json" \) 2>/dev/null | head -30
ls -ld . .git 2>/dev/null
stat -c '%A %U %n' AGENTS.md CLAUDE.md Makefile .vscode 2>/dev/null

sec "repo"
git log --oneline -20 2>/dev/null
git status --short 2>/dev/null | head
git remote -v 2>/dev/null

sec "secrets surface (presence only — never print values)"
for f in .env .env.local .env.production id_rsa id_ed25519 credentials; do
  find . "$HOME" -maxdepth 3 -name "$f" 2>/dev/null | head -5
done
ls -la "$HOME/.ssh" 2>/dev/null
git config --global --get-regexp 'credential|user' 2>/dev/null

sec "sandbox boundary"
mount 2>/dev/null | head -20
cat /proc/1/cgroup 2>/dev/null | head -3
ls -ld /proc/1/root 2>/dev/null

sec "network policy probes (HEAD only)"
for u in https://example.com https://pypi.org/simple/ https://github.com; do
  printf '%-30s ' "$u"; curl -s -o /dev/null -m 6 -w '%{http_code}\n' -I "$u" 2>/dev/null || echo "BLOCKED"
done
printf '%-30s ' "DNS"; getent hosts example.com >/dev/null 2>&1 && echo OK || echo FAIL

sec "write scope (scratch only)"
mkdir -p /tmp/recon_$$ && echo "wrote /tmp/recon_$$/ok" > /tmp/recon_$$/ok && echo "tmp: OK"
touch ./recon_write_test_$$ 2>/dev/null && { echo "repo: OK"; rm -f ./recon_write_test_$$; } || echo "repo: READ-ONLY"

printf '\n\nDone. Fill 00_recon/environment_model.md with the results.\n'
