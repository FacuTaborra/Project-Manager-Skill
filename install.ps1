#Requires -Version 5.1
# claude-pm-skill installer (Windows PowerShell).
# Copies SKILL.md and pm.py to ~/.claude/skills/pm/ and seeds the secret file.

$ErrorActionPreference = "Stop"

$RepoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir  = if ($env:CLAUDE_DIR) { $env:CLAUDE_DIR } else { Join-Path $HOME ".claude" }
$SkillDir   = Join-Path $ClaudeDir "skills\pm"
$SecretsDir = Join-Path $ClaudeDir "secrets"
$SecretFile = Join-Path $SecretsDir "linear-pak.env"
$ExampleFile = Join-Path $RepoRoot "examples\linear-pak.env.example"

Write-Host "claude-pm-skill installer"
Write-Host "  repo:    $RepoRoot"
Write-Host "  target:  $SkillDir"

if (-not (Test-Path $ClaudeDir)) {
    Write-Host ""
    Write-Host "WARN: $ClaudeDir does not exist." -ForegroundColor Yellow
    Write-Host "      Install Claude Code first: https://docs.anthropic.com/claude/docs/claude-code"
    Write-Host "      Continuing anyway - directories will be created."
}

New-Item -ItemType Directory -Path $SkillDir -Force | Out-Null
Copy-Item -Path (Join-Path $RepoRoot "SKILL.md") -Destination (Join-Path $SkillDir "SKILL.md") -Force
Copy-Item -Path (Join-Path $RepoRoot "pm.py")    -Destination (Join-Path $SkillDir "pm.py")    -Force
Write-Host "  + $SkillDir\SKILL.md"
Write-Host "  + $SkillDir\pm.py"

# Sync the src/claude_pm package (mirror — remove stale first)
$SrcSkillDir = Join-Path $SkillDir "src"
$PkgTarget   = Join-Path $SrcSkillDir "claude_pm"
$PkgSource   = Join-Path $RepoRoot "src\claude_pm"
New-Item -ItemType Directory -Path $SrcSkillDir -Force | Out-Null
if (Test-Path $PkgTarget) { Remove-Item -Path $PkgTarget -Recurse -Force }
Copy-Item -Path $PkgSource -Destination $PkgTarget -Recurse -Force
Write-Host "  + $PkgTarget\ (package)"

New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null

if (Test-Path $SecretFile) {
    Write-Host "  = $SecretFile (kept existing)"
} else {
    Copy-Item -Path $ExampleFile -Destination $SecretFile -Force
    Write-Host "  + $SecretFile (template - edit it to add your real key)"
}

Write-Host ""
Write-Host "Installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit $SecretFile and replace REPLACE_ME with your Linear PAK."
Write-Host "     Get one at https://linear.app/settings/api (scope: read + write)."
Write-Host "  2. Verify with: python $SkillDir\pm.py doctor"
Write-Host "  3. Open Claude Code in any project and run: /pm"
