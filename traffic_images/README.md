# Tuas Checkpoint Traffic Monitor

Automated traffic monitoring for Singapore Tuas Checkpoint at 5 AM daily.

## Latest Capture
- **Last Updated**: 2026-01-23T04:47:29.183221+08:00
- **Total Days Monitored**: 4
- **Total Captures**: 17

## Recent Captures

- **2026-01-23**: 2 capture(s), 0 image(s)
- **2026-01-22**: 7 capture(s), 27 image(s)
- **2026-01-21**: 4 capture(s), 12 image(s)
- **2026-01-20**: 4 capture(s), 12 image(s)


## Camera Locations

This project monitors the following Tuas checkpoint cameras:
- Tuas Checkpoint (towards Malaysia)
- Tuas Second Link
- Alternative checkpoint views

## Data Structure

```
traffic_images/
├── YYYY-MM-DD/
│   ├── camera_XXXX_HH-MM-SS.jpg
│   ├── metadata_HH-MM-SS.json
│   └── ...
└── summary.json
```

## Image Analysis

To analyze traffic patterns:
1. Browse to specific date folders
2. Compare images across different days at the same time
3. Check metadata files for camera details and timestamps

## How to Use

1. View images directly in GitHub by navigating to date folders
2. Download entire repository to analyze locally
3. Use metadata JSON files to correlate images with exact timestamps

---

*Automated by GitHub Actions - Runs daily at 5:00 AM Singapore Time (SGT)*
