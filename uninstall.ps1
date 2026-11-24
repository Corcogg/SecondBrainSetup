<#
.SYNOPSIS
  uninstall.ps1 — removes the Task Scheduler watcher task, the MCP
  registration, and the Claude Code hooks. Never touches the vault (your
  notes) and, by default, never touches .env (your keys). Safe to re-run.

.PARAMETER Purge
  Also delete .venv and .env from the app folder (never the vault).

.PARAMETER SkipMcp
  Leave the Claude Code MCP registration alone.

.PARAMETER SkipHooks
  Leave the Claude Code hooks alone.

.NOTES
  Env overrides:
    SECONDBRAIN_ROOT     install root (default: %USERPROFILE%\SecondBrain)
    BRAIN_SERVICE_LABEL  Task Scheduler task name (default: com.secondbrain.watcher)
#>
[CmdletBinding()]
param(
    [switch]$Purge,
    [switch]$SkipMcp,
    [switch]$SkipHooks,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$env:PYTHONUTF8 = '1'
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # not fatal
}

if ($Help) {
    Write-Host "Usage: uninstall.ps1 [-Purge] [-SkipMcp] [-SkipHooks]"
    exit 0
}

$SecondBrainRoot = $env:SECONDBRAIN_ROOT
if ([string]::IsNullOrEmpty($SecondBrainRoot)) {
    $SecondBrainRoot = Join-Path $env:USERPROFILE 'SecondBrain'
}
$Label = $env:BRAIN_SERVICE_LABEL
if ([string]::IsNullOrEmpty($Label)) {
    $Label = 'com.secondbrain.watcher'
}
$App = Join-Path $SecondBrainRoot 'app'
$Vault = Join-Path $SecondBrainRoot 'vault'

Write-Host "================================================="
Write-Host "  Second Brain — Uninstall"
Write-Host "================================================="

# ── Watcher ───────────────────────────────────────────────────────────────

Write-Host "[1/4] Stopping background watcher..."
try {
    & schtasks /End /TN $Label 2>&1 | Out-Null
} catch {
    # ignore — task may not be running
}
$deleteOut = & schtasks /Delete /F /TN $Label 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Removed scheduled task '$Label'."
} else {
    Write-Host "  Nothing to remove (task '$Label' not found)."
}

# ── MCP ───────────────────────────────────────────────────────────────────

Write-Host "[2/4] Removing MCP registration..."
if ($SkipMcp) {
    Write-Host "  Skipped (-SkipMcp)."
} else {
    $claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
    $claudePath = $null
    if ($claudeCmd) {
        $claudePath = $claudeCmd.Source
    } else {
        $candidate = Join-Path $env:USERPROFILE '.local\bin\claude.exe'
        if (Test-Path -LiteralPath $candidate) {
            $claudePath = $candidate
        }
    }
    if ($claudePath) {
        & $claudePath mcp remove claude-brain --scope user 2>&1 | Out-Null
        Write-Host "  Removed 'claude-brain' from Claude Code (if it was registered)."
    } else {
        Write-Host "  'claude' not on PATH or in %USERPROFILE%\.local\bin — skipping (nothing registered to remove)."
    }
}

# ── Hooks ─────────────────────────────────────────────────────────────────

Write-Host "[3/4] Removing Claude Code hooks..."
if ($SkipHooks) {
    Write-Host "  Skipped (-SkipHooks)."
} else {
    $venvPython = Join-Path $App '.venv\Scripts\python.exe'
    $hooksInstaller = Join-Path $App 'scripts\install_hooks.py'
    if ((Test-Path -LiteralPath $venvPython) -and (Test-Path -LiteralPath $hooksInstaller)) {
        & $venvPython $hooksInstaller --uninstall
        Write-Host "  Hooks removed from %USERPROFILE%\.claude\settings.json (backed up first)."
    } else {
        Write-Host "  App venv/scripts not found — skipping (nothing to uninstall)."
    }
}

# ── Purge (optional) ─────────────────────────────────────────────────────

Write-Host "[4/4] App files..."
if ($Purge) {
    Remove-Item -LiteralPath (Join-Path $App '.venv') -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $App '.env') -Force -ErrorAction SilentlyContinue
    Write-Host "  -Purge: removed $App\.venv and $App\.env."
} else {
    Write-Host "  Left $App\.venv and $App\.env in place. Re-run with -Purge to remove them."
}

Write-Host ""
Write-Host "================================================="
Write-Host "  Uninstall complete."
Write-Host "================================================="
Write-Host ""
Write-Host "Your notes were NOT touched. They still live at:"
Write-Host "  $Vault"
Write-Host ""
Write-Host "To delete them permanently (this cannot be undone):"
Write-Host "  Remove-Item -Recurse -Force `"$Vault`""
Write-Host ""
Write-Host "To remove the app folder entirely:"
Write-Host "  Remove-Item -Recurse -Force `"$App`""
