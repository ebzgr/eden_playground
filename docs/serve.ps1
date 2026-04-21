param(
  [int]$Port = 5173,
  [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

function Test-Command([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Open-Browser([string]$Url) {
  if ($NoOpen) { return }
  try { Start-Process $Url | Out-Null } catch {}
}

function Start-PythonServer {
  Write-Host "Starting Python server on http://localhost:$Port/ (root: docs/)" -ForegroundColor Cyan
  Open-Browser "http://localhost:$Port/index.html"
  python -m http.server $Port
}

function Start-NodeServer {
  Write-Host "Starting Node server on http://localhost:$Port/ (root: docs/)" -ForegroundColor Cyan
  Open-Browser "http://localhost:$Port/index.html"

  # npx will download http-server if not present; no global install required
  npx --yes http-server . -p $Port -c-1 --silent
}

if (Test-Command 'python') {
  Start-PythonServer
  exit 0
}

if (Test-Command 'py') {
  Write-Host "Starting Python (py launcher) server on http://localhost:$Port/ (root: docs/)" -ForegroundColor Cyan
  Open-Browser "http://localhost:$Port/index.html"
  py -m http.server $Port
  exit 0
}

if (Test-Command 'node' -and (Test-Command 'npx')) {
  Start-NodeServer
  exit 0
}

Write-Host "Could not find Python or Node to start a local server." -ForegroundColor Yellow
Write-Host "Install one of these, then re-run:" -ForegroundColor Yellow
Write-Host "  - Python: https://www.python.org/downloads/" -ForegroundColor Yellow
Write-Host "  - Node.js: https://nodejs.org/" -ForegroundColor Yellow
exit 1

