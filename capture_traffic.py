#!/usr/bin/env python3
"""
Tuas Checkpoint Traffic Monitor
Captures traffic images from Singapore LTA DataMall API at scheduled times
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configuration
LTA_API_KEY = os.environ.get('LTA_API_KEY', '')
API_URL = 'https://datamall2.mytransport.sg/ltaodataservice/Traffic-Imagesv2'
OUTPUT_DIR = Path('traffic_images')

# Checkpoint Camera IDs (from LTA DataMall)
# Monitoring both Tuas and Woodlands checkpoints
CHECKPOINT_CAMERA_IDS = [
    '2701',  # Woodlands Causeway (Towards Johor)
    '2702',  # Woodlands Checkpoint
    '4703',  # Tuas Second Link
    '4713',  # Tuas Checkpoint
    '4714',  # AYE (Tuas) - Near West Coast Walk
]

def get_traffic_images():
    """Fetch traffic images from LTA DataMall API"""
    
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }
    
    try:
        print("Fetching camera data from LTA API...")
        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        cameras = data.get('value', [])
        print(f"✓ Retrieved {len(cameras)} cameras from API")
        return cameras
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching data from API: {e}")
        return []

def download_image(image_url, save_path):
    """Download image from URL and save to file"""
    
    try:
        print(f"  Downloading from: {image_url[:80]}...")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Verify we got actual image data
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            print(f"  ✗ Warning: Response is not an image (content-type: {content_type})")
            return False
        
        # Verify content size
        content_length = len(response.content)
        if content_length < 1000:  # Images should be at least 1KB
            print(f"  ✗ Warning: Image too small ({content_length} bytes)")
            return False
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        # Verify file was written
        if save_path.exists() and save_path.stat().st_size > 0:
            print(f"  ✓ Saved: {save_path.name} ({content_length:,} bytes)")
            return True
        else:
            print(f"  ✗ Failed to write file: {save_path}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"  ✗ Timeout downloading image")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to download: {str(e)[:100]}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {str(e)[:100]}")
        return False

def capture_checkpoint_cameras():
    """Main function to capture checkpoint traffic images"""
    
    if not LTA_API_KEY:
        print("ERROR: LTA_API_KEY environment variable not set!")
        print("Please set your LTA DataMall API key in GitHub Secrets")
        return
    
    # Create output directory structure
    # Use Singapore timezone (UTC+8)
    singapore_tz = timezone(timedelta(hours=8))
    now = datetime.now(singapore_tz)
    date_folder = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H-%M-%S')
    
    daily_dir = OUTPUT_DIR / date_folder
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Singapore Checkpoint Traffic Capture")
    print(f"Date/Time (SGT): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Fetch all camera data
    cameras = get_traffic_images()
    
    if not cameras:
        print("No camera data received from API")
        return
    
    # Filter for checkpoint cameras
    checkpoint_cameras = [cam for cam in cameras if cam.get('CameraID') in CHECKPOINT_CAMERA_IDS]
    
    if not checkpoint_cameras:
        print(f"Warning: No checkpoint cameras found with specified IDs.")
        print(f"Searching for checkpoint cameras by location...")
        # Fallback: search by location name
        checkpoint_cameras = [cam for cam in cameras 
                            if any(keyword in cam.get('Location', '').lower() 
                                  for keyword in ['tuas', 'woodlands', 'causeway'])]
        print(f"Found {len(checkpoint_cameras)} cameras by location")
    
    metadata = {
        'timestamp': now.isoformat(),
        'date': date_folder,
        'time': time_str,
        'timezone': 'Asia/Singapore (SGT)',
        'cameras': []
    }
    
    successful_downloads = 0
    failed_downloads = 0
    
    for camera in checkpoint_cameras:
        camera_id = camera.get('CameraID')
        image_url = camera.get('ImageLink')
        location = camera.get('Location', 'Unknown')
        
        print(f"\nCamera {camera_id}: {location}")
        
        if image_url:
            # Save image with date and timestamp
            filename = f"camera_{camera_id}_{date_folder}_{time_str}.jpg"
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
                successful_downloads += 1
            else:
                print(f"  ✗ Skipping camera {camera_id} - download failed")
                failed_downloads += 1
        else:
            print(f"  ✗ No image URL available for camera {camera_id}")
            failed_downloads += 1
    
    # Save metadata
    metadata_file = daily_dir / f"metadata_{date_folder}_{time_str}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, indent=2, fp=f)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✓ Successful downloads: {successful_downloads}")
    print(f"  ✗ Failed downloads: {failed_downloads}")
    print(f"  📁 Saved to: {daily_dir}")
    
    if successful_downloads == 0:
        print(f"\n⚠ WARNING: No images were successfully downloaded!")
        print(f"   Check the error messages above for details.")
        print(f"   Common issues:")
        print(f"   - Image URLs expired (LTA links expire after 5 mins)")
        print(f"   - API rate limiting")
        print(f"   - Network connectivity issues")
    
    print(f"{'='*60}\n")
    
    # Generate summary report
    generate_summary()

def generate_summary():
    """Generate a summary report of all captured images"""
    
    if not OUTPUT_DIR.exists():
        return
    
    summary = {
        'last_updated': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'timezone': 'Asia/Singapore (SGT)',
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
    
    readme_content = f"""# Singapore Checkpoint Traffic Monitor

Automated traffic monitoring for Singapore checkpoints (Tuas & Woodlands).

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

This project monitors the following checkpoint cameras:

### Tuas Checkpoint
- Camera 4703: Tuas Second Link
- Camera 4713: Tuas Checkpoint
- Camera 4714: AYE (Tuas) - Near West Coast Walk

### Woodlands Checkpoint
- Camera 2701: Woodlands Causeway (Towards Johor)
- Camera 2702: Woodlands Checkpoint

## Data Structure

```
traffic_images/
├── YYYY-MM-DD/
│   ├── camera_XXXX_YYYY-MM-DD_HH-MM-SS.jpg
│   ├── metadata_YYYY-MM-DD_HH-MM-SS.json
│   └── ...
└── summary.json
```

## Filename Format

Files are named with both date and time (Singapore timezone):
- `camera_4703_2026-01-23_05-30-45.jpg`
  - Camera ID: 4703
  - Date: 2026-01-23
  - Time: 05:30:45 SGT

## Image Analysis

To analyze traffic patterns:
1. Browse to specific date folders
2. Compare images across different days at the same time
3. Compare Tuas vs Woodlands checkpoint traffic
4. Check metadata files for camera details and timestamps

## How to Use

1. View images directly in GitHub by navigating to date folders
2. Download entire repository to analyze locally
3. Use metadata JSON files to correlate images with exact timestamps

---

*Automated by GitHub Actions - Captures at multiple times daily (Singapore Time)*
"""
    
    readme_file = OUTPUT_DIR / 'README.md'
    with open(readme_file, 'w') as f:
        f.write(readme_content)

if __name__ == '__main__':
    capture_checkpoint_cameras()
