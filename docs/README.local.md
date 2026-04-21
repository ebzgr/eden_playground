# Local docs server

Opening HTML files via `file://` breaks loading JSON (`fetch(...)`) in most browsers. Use a local server instead.

## Start

From the repo root:

```powershell
cd .\docs
.\serve.ps1
```

Then open `http://localhost:5173/index.html`.

## Options

```powershell
# Choose a different port
.\serve.ps1 -Port 8080

# Start without auto-opening the browser
.\serve.ps1 -NoOpen
```

