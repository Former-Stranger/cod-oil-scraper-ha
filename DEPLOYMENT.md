# Deployment Instructions

## What's Fixed?

The issue was that Home Assistant requires a specific repository structure:

```
Repository Root/
├── repository.yaml          # Required - tells HA this is an add-on repo
├── cod_oil_scraper/         # Add-on folder (must match slug in config.yaml)
│   ├── config.yaml          # Add-on configuration
│   ├── Dockerfile           # Container build
│   ├── build.yaml          # Multi-arch builds
│   ├── requirements.txt    # Python deps
│   ├── run.sh              # Entry point
│   ├── oil_scraper.py      # Scraper code
│   └── README.md           # Add-on docs
├── README.md               # Repository README
└── LICENSE                 # License file
```

## Deploy to GitHub

```bash
cd /Users/akalbfell/COD-OIL-Scraper-Fixed

# Initialize git
git init
git add .
git commit -m "Initial commit - HA add-on structure"

# Connect to your repo (replace existing content)
git remote add origin https://github.com/Former-Stranger/cod_oil_scraper.git

# Force push to replace everything
git push -f origin main
```

## Test in Home Assistant

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Click **⋮** (top right) → **Repositories**
3. Add: `https://github.com/Former-Stranger/cod_oil_scraper`
4. Refresh the page
5. Find "COD Oil Price Scraper" in the store
6. Install and configure

## File Structure Explained

### Repository Root Files

- **repository.yaml**: Tells HA this is an add-on repository
- **README.md**: User-facing documentation for the GitHub repo
- **LICENSE**: MIT license

### Add-on Folder (cod_oil_scraper/)

Contains everything needed to build and run the add-on:

- **config.yaml**: Add-on metadata and configuration schema
- **Dockerfile**: Container build instructions
- **build.yaml**: Multi-architecture build config
- **requirements.txt**: Python dependencies
- **run.sh**: Entry point that starts the scraper
- **oil_scraper.py**: The actual scraper code
- **README.md**: Add-on-specific documentation

## Why the Original Upload Failed

Your original upload had all files in the root directory without:
1. A `repository.yaml` file
2. The add-on files in a subdirectory matching the slug

Home Assistant couldn't recognize it as a valid add-on repository.

## Next Steps After Deploy

1. Test installation in Home Assistant
2. Verify the add-on builds and runs
3. Check logs for any errors
4. Optional: Create icons (icon.png, logo.png) and add to cod_oil_scraper folder
5. Optional: Create a GitHub release (v1.0.0)
