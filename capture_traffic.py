#!/usr/bin/env python3
"""
Tuas Checkpoint Traffic Monitor
Captures traffic images from Singapore LTA DataMall API at scheduled times
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
LTA_API_KEY = os.environ.get('LTA_API_KEY', '')
API_URL = 'https://datamall2.mytransport.sg/ltaodataservice/Traffic-Imagesv2'
OUTPUT_DIR = Path('traffic_images')

# Tuas Checkpoint Camera IDs (from LTA DataMall)
# These are the camera IDs for Tuas area
TUAS_CAMERA_IDS = [
    '4703',  # Tuas Checkpoint (towards Malaysia)
    '4713',  # Tuas Second Link
    '4714',  # Tuas Second Link (alternative view)
]

def get_traffic_images():
    """Fetch traffic images from LTA DataMall API"""
    
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('value', [])
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []

def download_image(image_url, save_path):
    """Download image from URL and save to file"""
    
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Saved: {save_path}")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download {image_url}: {e}")
        return False

def capture_tuas_cameras():
    """Main function to capture Tuas checkpoint traffic images"""
    
    if not LTA_API_KEY:
        print("ERROR: LTA_API_KEY environment variable not set!")
        print("Please set your LTA DataMall API key in GitHub Secrets")
        return
    
    # Create output directory structure
    now = datetime.now()
    date_folder = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H-%M-%S')
    
    daily_dir = OUTPUT_DIR / date_folder
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Tuas Checkpoint Traffic Capture")
    print(f"Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Fetch all camera data
    cameras = get_traffic_images()
    
    if not cameras:
        print("No camera data received from API")
        return
    
    # Filter for Tuas cameras and download images
    tuas_cameras = [cam for cam in cameras if cam.get('CameraID') in TUAS_CAMERA_IDS]
    
    if not tuas_cameras:
        print(f"Warning: No Tuas cameras found. Saving all checkpoint cameras...")
        # Fallback: save all cameras with "Tuas" in location
        tuas_cameras = [cam for cam in cameras if 'tuas' in cam.get('Location', '').lower()]
    
    metadata = {
        'timestamp': now.isoformat(),
        'date': date_folder,
        'time': time_str,
        'cameras': []
    }
    
    for camera in tuas_cameras:
        camera_id = camera.get('CameraID')
        image_url = camera.get('ImageLink')
        location = camera.get('Location', 'Unknown')
        
        print(f"Camera {camera_id}: {location}")
        
        if image_url:
            # Save image with timestamp
            filename = f"camera_{camera_id}_{time_str}.jpg"
            save_path = daily_dir / filename
            
            if download_image(image_url, save_path):
                metadata['cameras'].append({
                    'camera_id': camera_id,
                    'location': location,
                    'filename': filename,
                    'image_url': image_url,
                    'latitude': camera.get('Latitude'),
                    'longitude': camera.get('Longitude')
                })
        else:
            print(f"  No image URL available")
    
    # Save metadata
    metadata_file = daily_dir / f"metadata_{time_str}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, indent=2, fp=f)
    
    print(f"\n✓ Captured {len(metadata['cameras'])} camera(s)")
    print(f"✓ Saved to: {daily_dir}")
    print(f"\n{'='*60}\n")
    
    # Generate summary report
    generate_summary()

def generate_summary():
    """Generate a summary report of all captured images"""
    
    if not OUTPUT_DIR.exists():
        return
    
    summary = {
        'last_updated': datetime.now().isoformat(),
        'total_days': 0,
        'total_captures': 0,
        'days': []
    }
    
    for date_dir in sorted(OUTPUT_DIR.iterdir()):
        if date_dir.is_dir():
            metadata_files = list(date_dir.glob('metadata_*.json'))
            image_files = list(date_dir.glob('camera_*.jpg'))
            
            summary['total_days'] += 1
            summary['total_captures'] += len(metadata_files)
            
            summary['days'].append({
                'date': date_dir.name,
                'captures': len(metadata_files),
                'images': len(image_files)
            })
    
    # Save summary
    summary_file = OUTPUT_DIR / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, indent=2, fp=f)
    
    # Generate README
    generate_readme(summary)

def generate_readme(summary):
    """Generate a README file with capture history"""
    
    readme_content = f"""# Tuas Checkpoint Traffic Monitor

Automated traffic monitoring for Singapore Tuas Checkpoint at 5 AM daily.

## Latest Capture
- **Last Updated**: {summary['last_updated']}
- **Total Days Monitored**: {summary['total_days']}
- **Total Captures**: {summary['total_captures']}

## Recent Captures

"""
    
    # Add recent days (last 7 days)
    for day in sorted(summary['days'], key=lambda x: x['date'], reverse=True)[:7]:
        readme_content += f"- **{day['date']}**: {day['captures']} capture(s), {day['images']} image(s)\n"
    
    readme_content += """

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
"""
    
    readme_file = OUTPUT_DIR / 'README.md'
    with open(readme_file, 'w') as f:
        f.write(readme_content)

if __name__ == '__main__':
    capture_tuas_cameras()
