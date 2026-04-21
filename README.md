# eden_playground

**eden_playground** is a small static website for **Marketing for Betterment's playground**: a research + awareness platform that makes manipulative marketing techniques more visible through immersive, art-driven “worlds”, and documents the conceptual, ethical, and methodology layers behind that work.

## What’s in this repo

- `docs/`: the site (static HTML/CSS/JS) and its wiki-style navigation.
- `Documents/`: reference PDFs used by the project.

## View locally

Opening the HTML files via `file://` will usually break JSON loading (`fetch(...)`). Start the local server:

```powershell
cd .\docs
.\serve.ps1
```

Then open `http://localhost:5173/index.html`.

