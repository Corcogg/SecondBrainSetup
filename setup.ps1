<#
.SYNOPSIS
  setup.ps1 — one-shot, idempotent installer for the second brain, Windows only.

.DESCRIPTION
  Normally run by Claude Code, not typed by hand. See INSTALL-windows.md for
  the runbook this script is one step of. Mirrors setup.sh step for step —
  see docs/ARCHITECTURE.md "Windows port — contract" before changing this file.

.PARAMETER NonInteractive
  Never prompt; fail with a clear message if keys are missing.

.PARAMETER SkipMcp
  Don't register the MCP server with Claude Code.

.PARAMETER SkipHooks
  Don't install the SessionStart/PreCompact/Stop hooks.

.PARAMETER SkipIndex
  Don't build the initial vector index.

.NOTES
  Env overrides:
    SECONDBRAIN_ROOT     install root (default: %USERPROFILE%\SecondBrain)
    BRAIN_SERVICE_LABEL  Task Scheduler task name (default: com.secondbrain.watcher)
    VOYAGE_API_KEY / ANTHROPIC_API_KEY  optional; the preferred path is to put
      them in <app>\.env (KEY=value lines) before running — setup reads that
      file and never needs the keys on a command line or in a chat message.
#>
[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [switch]$SkipMcp,
    [switch]$SkipHooks,
    [switch]$SkipIndex,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Console / Python UTF-8 so doctor's checkmarks render ────────────────────
$env:PYTHONUTF8 = '1'
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Some hosts (redirected output, certain CI runners) refuse this — not fatal.
}

$Total = 10

function Write-Step {
    param([int]$N, [string]$Title)
    Write-Host ("[{0}/{1}] {2}" -f $N, $Total, $Title)
}

function Fail {
    param([string]$Msg)
    [Console]::Error.WriteLine("  ERROR: $Msg")
    exit 1
}

function Warn {
    param([string]$Msg)
    [Console]::Error.WriteLine("  WARNING: $Msg")
}

function Ok {
    param([string]$Msg)
    Write-Host "  OK: $Msg"
}

if ($Help) {
    Write-Host "Usage: setup.ps1 [-NonInteractive] [-SkipMcp] [-SkipHooks] [-SkipIndex]"
    exit 0
}

$Interactive = -not ($NonInteractive.IsPresent -or [Console]::IsInputRedirected)

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
Write-Host "  Second Brain — Setup"
Write-Host "================================================="

# ── Step 1: Preflight ────────────────────────────────────────────────────────

Write-Step 1 "Preflight checks"

if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    Fail "this installer only supports 64-bit Windows on x64 (found: $($env:PROCESSOR_ARCHITECTURE)). chromadb has no win_arm64 wheel."
}

$ScriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($ScriptDir)) {
    $ScriptDir = Split-Path -Parent (Resolve-Path $MyInvocation.MyCommand.Path)
}
$ScriptDirFull = ([IO.Path]::GetFullPath($ScriptDir)).TrimEnd('\')
$AppFull = ([IO.Path]::GetFullPath($App)).TrimEnd('\')

if ($ScriptDirFull -ine $AppFull) {
    if (Test-Path -LiteralPath $App) {
        Fail "$App already exists and is not this folder. Remove it, or set SECONDBRAIN_ROOT to install elsewhere."
    }
    if ($Interactive) {
        $mvAns = Read-Host "  This repo isn't at $App yet. Move it there now? [Y/n]"
        if ($mvAns -match '^[nN]') {
            Fail "setup.ps1 must run from $App. Move it manually and re-run."
        }
        New-Item -ItemType Directory -Force -Path $SecondBrainRoot | Out-Null
        Move-Item -LiteralPath $ScriptDir -Destination $App
        Write-Host "  Moved to $App — re-launching setup.ps1 from there."
        $reArgs = @()
        if ($NonInteractive) { $reArgs += '-NonInteractive' }
        if ($SkipMcp) { $reArgs += '-SkipMcp' }
        if ($SkipHooks) { $reArgs += '-SkipHooks' }
        if ($SkipIndex) { $reArgs += '-SkipIndex' }
        $newScript = Join-Path $App 'setup.ps1'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $newScript @reArgs
        exit $LASTEXITCODE
    } else {
        Fail "setup.ps1 must run from $App (found: $ScriptDir). Move the folder and re-run, or set SECONDBRAIN_ROOT."
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "git is required. Install Git for Windows: winget install Git.Git"
}

$NeedClaude = -not ($SkipMcp.IsPresent -and $SkipHooks.IsPresent)
$ClaudePath = $null
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    $ClaudePath = $claudeCmd.Source
} else {
    $candidate = Join-Path $env:USERPROFILE '.local\bin\claude.exe'
    if (Test-Path -LiteralPath $candidate) {
        $ClaudePath = $candidate
    }
}
if ($NeedClaude -and -not $ClaudePath) {
    Fail "the 'claude' command is not on PATH (checked PATH and %USERPROFILE%\.local\bin\claude.exe). Install Claude Code, or re-run with -SkipMcp -SkipHooks."
}

$claudeNote = ""
if ($ClaudePath) {
    $claudeNote = ", claude at $ClaudePath"
}
Ok "Windows x64, install path is $App, git present$claudeNote."

# ── Step 2: uv ────────────────────────────────────────────────────────────────

Write-Step 2 "Checking for uv (Python package manager)"

$Uv = $null
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
    $Uv = $uvCmd.Source
} else {
    $uvCandidate = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
    if (Test-Path -LiteralPath $uvCandidate) {
        $Uv = $uvCandidate
    }
}
if (-not $Uv) {
    Write-Host "  uv not found — installing via the official installer..."
    try {
        Invoke-RestMethod -Uri 'https://astral.sh/uv/install.ps1' | Invoke-Expression
    } catch {
        Fail "uv installer failed: $($_.Exception.Message). See https://docs.astral.sh/uv/getting-started/installation/"
    }
    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCmd) {
        $Uv = $uvCmd.Source
    } elseif (Test-Path -LiteralPath $uvCandidate) {
        $Uv = $uvCandidate
    }
}
if (-not $Uv) {
    Fail "uv install did not put 'uv' on PATH or in %USERPROFILE%\.local\bin. See https://docs.astral.sh/uv/getting-started/installation/"
}
$uvVersion = & $Uv --version 2>&1
Ok "$uvVersion"

# ── Step 3: venv + dependencies ─────────────────────────────────────────────

Write-Step 3 "Python 3.11 virtual environment"

$VenvDir = Join-Path $App '.venv'
$PythonExe = Join-Path $VenvDir 'Scripts\python.exe'
$PythonwExe = Join-Path $VenvDir 'Scripts\pythonw.exe'

if (Test-Path -LiteralPath $VenvDir) {
    Write-Host "  $VenvDir already exists — skipping creation."
} else {
    & $Uv venv --python 3.11 $VenvDir
    if ($LASTEXITCODE -ne 0) { Fail "uv venv failed." }
    Write-Host "  Created $VenvDir"
}
& $Uv pip install --python $PythonExe -r (Join-Path $App 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Fail "uv pip install failed." }
Ok "dependencies installed from requirements.txt."

# ── Step 4: API keys ─────────────────────────────────────────────────────────

Write-Step 4 "API keys"

$EnvFile = Join-Path $App '.env'

function Resolve-Key {
    param([string]$VarName)

    $current = [Environment]::GetEnvironmentVariable($VarName, 'Process')
    if ([string]::IsNullOrEmpty($current) -and (Test-Path -LiteralPath $EnvFile)) {
        $line = Get-Content -LiteralPath $EnvFile | Where-Object { $_ -match "^$VarName=" } | Select-Object -First 1
        if ($line) {
            $eq = $line.IndexOf('=')
            $current = $line.Substring($eq + 1)
        }
    }
    if ([string]::IsNullOrEmpty($current) -and $Interactive) {
        $secure = Read-Host -Prompt "  Paste your $VarName (input hidden)" -AsSecureString
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            $current = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        } finally {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
    if ([string]::IsNullOrEmpty($current)) {
        [Console]::Error.WriteLine("  ERROR: $VarName is not set.")
        [Console]::Error.WriteLine("  Put it in $EnvFile as a line of the form $VarName=<your key> (see INSTALL-windows.md Step 3), then re-run.")
        exit 1
    }
    return $current
}

$VoyageKey = Resolve-Key 'VOYAGE_API_KEY'
$AnthropicKey = Resolve-Key 'ANTHROPIC_API_KEY'

$envBody = "VOYAGE_API_KEY=$VoyageKey`r`nANTHROPIC_API_KEY=$AnthropicKey`r`n"
[System.IO.File]::WriteAllText($EnvFile, $envBody, (New-Object System.Text.UTF8Encoding($false)))

$Owner = "$env:USERDOMAIN\$env:USERNAME"
$icaclsOut = & icacls $EnvFile /inheritance:r /grant:r "${Owner}:(R,W)" 2>&1
$icaclsStatus = $LASTEXITCODE
# Exit code only: icacls' status text is localized. doctor.py re-verifies the ACL itself.
if ($icaclsStatus -ne 0) {
    [Console]::Error.WriteLine("  ERROR: icacls did not confirm the lock on ${EnvFile}:")
    $icaclsOut | ForEach-Object { [Console]::Error.WriteLine("    $_") }
    exit 1
}
Ok "keys saved to $EnvFile (locked to $Owner only)."

# ── Step 5: Vault ────────────────────────────────────────────────────────────

Write-Step 5 "Vault"

New-Item -ItemType Directory -Force -Path (Join-Path $Vault 'memory\facts') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Vault 'memory\projects') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Vault 'memory\system') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Vault 'daily') | Out-Null

foreach ($f in @('SOUL.md', 'USER.md', 'MEMORY.md')) {
    $dst = Join-Path $Vault $f
    if (-not (Test-Path -LiteralPath $dst)) {
        Copy-Item -LiteralPath (Join-Path $App "templates\$f") -Destination $dst
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $Vault '.git'))) {
    & git -C $Vault init -q
    if ($LASTEXITCODE -ne 0) { Fail "git init failed in $Vault." }
}

$vaultGitignore = ".chroma/`n*.log`n.last_reconcile`nThumbs.db`n.DS_Store`n"
[System.IO.File]::WriteAllText((Join-Path $Vault '.gitignore'), $vaultGitignore, (New-Object System.Text.UTF8Encoding($false)))

$CfgPath = Join-Path $App 'brain_config.json'
if (-not (Test-Path -LiteralPath $CfgPath)) {
    Copy-Item -LiteralPath (Join-Path $App 'brain_config.example.json') -Destination $CfgPath
    Write-Host "  Created brain_config.json from the example."
}

# Always sync the install-determined fields (paths + service label) so the
# config file, not this script's env, is the single source of truth. Values
# are passed as argv, never text-substituted into the JSON.
$pyRoundTrip = @'
import json
import sys

cfg_path, app_dir, vault_dir, python_path, label = sys.argv[1:6]
with open(cfg_path) as f:
    cfg = json.load(f)
cfg["app_dir"] = app_dir
cfg["vault_dir"] = vault_dir
cfg["python"] = python_path
cfg["service_label"] = label
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
'@
$pyRoundTrip | & $PythonExe - $CfgPath $App $Vault $PythonExe $Label
if ($LASTEXITCODE -ne 0) { Fail "brain_config.json sync failed." }
Ok "brain_config.json paths and service label are current."

Ok "vault at $Vault (own git repo, no remote)."

# ── Step 6: Task Scheduler ───────────────────────────────────────────────────

Write-Step 6 "Background watcher (Task Scheduler)"

try {
    $TemplatePath = Join-Path $App 'windows\watcher-task.xml.template'
    $LogPath = Join-Path $Vault 'brain_watcher.log'
    $UserId = (& whoami).Trim()

    $templateContent = Get-Content -LiteralPath $TemplatePath -Raw
    # Literal .Replace (not -replace) so '$' in values is never a regex group,
    # and XML-escape every value so '&' in a username or path cannot break the document.
    $x = { param($v) [System.Security.SecurityElement]::Escape([string]$v) }
    $rendered = $templateContent
    $rendered = $rendered.Replace('__LABEL__', (& $x $Label))
    $rendered = $rendered.Replace('__APP__', (& $x $App))
    $rendered = $rendered.Replace('__PYTHONW__', (& $x $PythonwExe))
    $rendered = $rendered.Replace('__LOG__', (& $x $LogPath))
    $rendered = $rendered.Replace('__USERID__', (& $x $UserId))
    $rendered = $rendered -replace 'encoding="UTF-8"', 'encoding="UTF-16"'

    $RenderedPath = Join-Path $env:TEMP ("{0}-task.xml" -f ($Label -replace '[\\/:*?"<>|]', '_'))
    [System.IO.File]::WriteAllText($RenderedPath, $rendered, [System.Text.Encoding]::Unicode)

    $createOut = & schtasks /Create /F /TN $Label /XML $RenderedPath 2>&1
    $createStatus = $LASTEXITCODE
    Remove-Item -LiteralPath $RenderedPath -Force -ErrorAction SilentlyContinue

    if ($createStatus -ne 0) {
        Warn "schtasks /Create failed: $($createOut | Out-String). See INSTALL-windows.md failure branches (schtasks 'Access is denied')."
    } else {
        Ok "task '$Label' registered."
        $runOut = & schtasks /Run /TN $Label 2>&1
        if ($LASTEXITCODE -ne 0) {
            Warn "schtasks /Run failed: $($runOut | Out-String)"
        } else {
            Ok "watcher started ($Label)."
        }
    }
} catch {
    Warn "Task Scheduler setup raised an exception: $($_.Exception.Message)"
}

# ── Step 7: MCP registration ────────────────────────────────────────────────

if ($SkipMcp) {
    Write-Step 7 "MCP server registration (skipped: -SkipMcp)"
} else {
    Write-Step 7 "MCP server registration"
    & $ClaudePath mcp remove claude-brain --scope user 2>&1 | Out-Null
    & $ClaudePath mcp add --scope user claude-brain -- $PythonExe (Join-Path $App 'scripts\brain_mcp.py')
    if ($LASTEXITCODE -ne 0) { Fail "claude mcp add failed." }
    Ok "claude-brain registered (scope: user)."
}

# ── Step 8: Hooks ────────────────────────────────────────────────────────────

if ($SkipHooks) {
    Write-Step 8 "Claude Code hooks (skipped: -SkipHooks)"
} else {
    Write-Step 8 "Claude Code hooks"
    & $PythonExe (Join-Path $App 'scripts\install_hooks.py')
    if ($LASTEXITCODE -ne 0) { Fail "install_hooks.py failed." }
    Ok "hooks installed into %USERPROFILE%\.claude\settings.json (backed up first)."
}

# ── Step 9: Initial index ───────────────────────────────────────────────────

if ($SkipIndex) {
    Write-Step 9 "Initial vector index (skipped: -SkipIndex)"
} else {
    Write-Step 9 "Initial vector index"
    if (Test-Path -LiteralPath $EnvFile) {
        Get-Content -LiteralPath $EnvFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
            }
        }
    }
    & $PythonExe (Join-Path $App 'scripts\build_index.py')
    if ($LASTEXITCODE -ne 0) { Fail "build_index.py failed." }
    Ok "initial index built."
}

# ── Step 10: Doctor ──────────────────────────────────────────────────────────

Write-Step 10 "Health check"
$DoctorStatus = 0
try {
    & $PythonExe (Join-Path $App 'scripts\doctor.py')
    $DoctorStatus = $LASTEXITCODE
} catch {
    Warn "doctor.py raised an exception: $($_.Exception.Message)"
    $DoctorStatus = 1
}

Write-Host ""
Write-Host "================================================="
if ($DoctorStatus -eq 0) {
    Write-Host "  Setup complete — all checks green."
} else {
    Write-Host "  Setup finished with problems — see the red checks above."
}
Write-Host "================================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Fully quit Claude Code and Claude Desktop (right-click the tray icon and"
Write-Host "     Quit, or Task Manager if needed) and reopen them so they pick up the new"
Write-Host "     MCP server and hooks."
Write-Host "  2. In a new session, run /mcp — you should see 'claude-brain' with 5 tools."
Write-Host "  3. Vault:   $Vault"
Write-Host "  4. Log:     $Vault\brain_watcher.log"
Write-Host "  5. Re-run this script any time — it's safe (idempotent)."

exit $DoctorStatus
