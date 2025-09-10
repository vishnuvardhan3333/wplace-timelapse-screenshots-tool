#!/usr/bin/env python3
"""
Simple Autonomous Screenshot Tool for Blue Marble/wplace.live

Interactive prompts for all required inputs.
Takes screenshots at specified intervals using Blue Marble coordinate system.
"""

import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, List
import schedule
import requests
from PIL import Image
from io import BytesIO
import sys
import re
from urllib.parse import urlparse, parse_qs

# Constants
TILE_SIZE_PX = 1000

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_screenshot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def detect_tile_server_from_wplace_url(wplace_url: str) -> str:
    """
    Detect the correct tile server URL from a wplace.live URL.
    """
    try:
        parsed = urlparse(wplace_url)
        query_params = parse_qs(parsed.query)
        
        season = None
        
        # Check for explicit season parameter
        if 's' in query_params:
            season = query_params['s'][0]
        elif 'season' in query_params:
            season = query_params['season'][0]
        
        # Detect from coordinates if no explicit season
        if season is None:
            # Check for lat/lng coordinates
            lat = query_params.get('lat', [None])[0]
            lng = query_params.get('lng', [None])[0]
            
            if lat and lng:
                try:
                    lat_val = float(lat)
                    lng_val = float(lng)
                    
                    # India region - uses s0
                    if 6 <= lat_val <= 37 and 68 <= lng_val <= 97:
                        season = '0'
                        logger.info("Detected India region, using season 0")
                    # Europe region
                    elif 35 <= lat_val <= 71 and -10 <= lng_val <= 40:
                        season = '1'
                        logger.info("Detected Europe region, using season 1")
                    # North America region
                    elif 15 <= lat_val <= 72 and -168 <= lng_val <= -52:
                        season = '2'
                        logger.info("Detected North America region, using season 2")
                    else:
                        season = '0'
                        logger.info(f"Unknown region, using season 0")
                except ValueError:
                    season = '0'
            else:
                season = '0'
        
        base_url = f"https://backend.wplace.live/files/s{season}/tiles"
        logger.info(f"Using tile server: {base_url}")
        return base_url
        
    except Exception as e:
        logger.warning(f"Error parsing URL: {e}. Using default season 0.")
        return "https://backend.wplace.live/files/s0/tiles"


def build_season_bases(base_url: str) -> List[str]:
    """Build fallback URLs for different seasons."""
    match = re.match(r'^(.*/s)([0-9]+)(/tiles.*)$', base_url)
    if not match:
        return [base_url]
    
    prefix, current_season, suffix = match.groups()
    current_s = int(current_season)
    
    season_urls = [base_url]
    priority_seasons = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    for s in priority_seasons:
        if s != current_s:
            season_urls.append(f"{prefix}{s}{suffix}")
    
    return season_urls


def compute_absolute_pixel(tx: int, ty: int, px: int, py: int) -> Tuple[int, int]:
    """Convert Blue Marble tile coordinates to absolute pixel coordinates."""
    return (tx * TILE_SIZE_PX + px, ty * TILE_SIZE_PX + py)


def fetch_tile_with_fallback(base_urls: List[str], tile_x: int, tile_y: int, timeout: int = 30) -> Optional[bytes]:
    """Fetch a tile with season fallback."""
    headers = {
        'Referer': 'https://wplace.live/',
        'Origin': 'https://wplace.live',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    for base_url in base_urls:
        # Try normal x/y format first
        url = f"{base_url.rstrip('/')}/{tile_x}/{tile_y}.png"
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return response.content
            elif response.status_code == 404:
                # Try swapped y/x format
                url_swapped = f"{base_url.rstrip('/')}/{tile_y}/{tile_x}.png"
                response = requests.get(url_swapped, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response.content
                continue
            else:
                continue
                
        except requests.RequestException:
            continue
    
    return None


def take_screenshot(start_tx: int, start_ty: int, start_px: int, start_py: int,
                   end_tx: int, end_ty: int, end_px: int, end_py: int,
                   base_url: str, output_dir: str) -> Optional[str]:
    """Take a screenshot of the specified region."""
    logger.info(f"Taking screenshot from ({start_tx},{start_ty},{start_px},{start_py}) to ({end_tx},{end_ty},{end_px},{end_py})")
    
    # Convert to absolute coordinates
    abs_start_x, abs_start_y = compute_absolute_pixel(start_tx, start_ty, start_px, start_py)
    abs_end_x, abs_end_y = compute_absolute_pixel(end_tx, end_ty, end_px, end_py)
    
    # Validate coordinates
    if abs_end_x < abs_start_x or abs_end_y < abs_start_y:
        logger.error("End coordinates must be greater than or equal to start coordinates")
        return None
    
    # Calculate dimensions
    total_width = (abs_end_x - abs_start_x) + 1
    total_height = (abs_end_y - abs_start_y) + 1
    
    # Determine tile ranges
    tile_start_x = abs_start_x // TILE_SIZE_PX
    tile_start_y = abs_start_y // TILE_SIZE_PX
    tile_end_x = abs_end_x // TILE_SIZE_PX
    tile_end_y = abs_end_y // TILE_SIZE_PX
    
    logger.info(f"Screenshot dimensions: {total_width}x{total_height}")
    
    # Build season URLs for fallback
    season_urls = build_season_bases(base_url)
    
    # Create canvas
    canvas = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    
    # Fetch and composite tiles
    tiles_fetched = 0
    tiles_total = (tile_end_x - tile_start_x + 1) * (tile_end_y - tile_start_y + 1)
    
    for ty in range(tile_start_y, tile_end_y + 1):
        for tx in range(tile_start_x, tile_end_x + 1):
            tile_data = fetch_tile_with_fallback(season_urls, tx, ty)
            if tile_data:
                try:
                    tile_img = Image.open(BytesIO(tile_data))
                    
                    # Calculate position on canvas
                    tile_abs_x = tx * TILE_SIZE_PX
                    tile_abs_y = ty * TILE_SIZE_PX
                    left = tile_abs_x - abs_start_x
                    top = tile_abs_y - abs_start_y
                    
                    # Paste tile onto canvas
                    canvas.paste(tile_img, (left, top))
                    tiles_fetched += 1
                    
                except Exception as e:
                    logger.error(f"Error processing tile {tx},{ty}: {e}")
    
    logger.info(f"Successfully fetched {tiles_fetched}/{tiles_total} tiles")
    
    if tiles_fetched == 0:
        logger.error("No tiles were fetched. Check coordinates and connection.")
        return None
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    
    # Save screenshot
    try:
        canvas.save(filepath, "PNG")
        logger.info(f"Screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving screenshot: {e}")
        return None


def parse_coordinates(coord_string: str) -> Tuple[int, int, int, int]:
    """Parse coordinate string with or without braces: '(Tl X: 1471, Tl Y: 923, Px X: 63, Px Y: 995)' or 'Tl X: 1471, Tl Y: 923, Px X: 63, Px Y: 995'"""
    try:
        # Remove braces if present and strip whitespace
        cleaned = coord_string.strip().strip('()')
        
        # Extract numbers using regex - more flexible pattern
        pattern = r'Tl X:\s*(\d+).*?Tl Y:\s*(\d+).*?Px X:\s*(\d+).*?Px Y:\s*(\d+)'
        match = re.search(pattern, cleaned)
        
        if match:
            tx, ty, px, py = map(int, match.groups())
            return tx, ty, px, py
        else:
            raise ValueError("Invalid coordinate format")
    except Exception:
        raise ValueError("Could not parse coordinates. Please use format: (Tl X: 1471, Tl Y: 923, Px X: 63, Px Y: 995) or without braces")


def get_user_inputs():
    """Get all inputs from user via interactive prompts."""
    print("=== Blue Marble Autonomous Screenshot Tool ===")
    print()
    
    # Get wplace URL
    while True:
        url = input("Enter wplace.live URL: ").strip()
        if url and ('wplace.live' in url):
            break
        print("Please enter a valid wplace.live URL")
    
    # Get start coordinates
    while True:
        start_input = input("Enter START coordinates (copy from Blue Marble): ").strip()
        try:
            start_tx, start_ty, start_px, start_py = parse_coordinates(start_input)
            print(f"✓ Parsed: Tl X: {start_tx}, Tl Y: {start_ty}, Px X: {start_px}, Px Y: {start_py}")
            break
        except ValueError as e:
            print(f"Error: {e}")
            print("Example: (Tl X: 1471, Tl Y: 923, Px X: 63, Px Y: 995)")
    
    # Get end coordinates
    while True:
        end_input = input("Enter END coordinates (copy from Blue Marble): ").strip()
        try:
            end_tx, end_ty, end_px, end_py = parse_coordinates(end_input)
            print(f"✓ Parsed: Tl X: {end_tx}, Tl Y: {end_ty}, Px X: {end_px}, Px Y: {end_py}")
            break
        except ValueError as e:
            print(f"Error: {e}")
            print("Example: (Tl X: 1471, Tl Y: 923, Px X: 63, Px Y: 995)")
    
    # Get output directory
    output_dir = input("Enter output directory (default: screenshots): ").strip()
    if not output_dir:
        output_dir = "screenshots"
    
    # Get interval
    while True:
        interval_input = input("Enter screenshot interval in seconds (e.g., 3600 for 1 hour): ").strip()
        try:
            interval = int(interval_input)
            if interval > 0:
                break
            else:
                print("Interval must be greater than 0")
        except ValueError:
            print("Please enter a valid number")
    
    return url, (start_tx, start_ty, start_px, start_py), (end_tx, end_ty, end_px, end_py), output_dir, interval


def run_screenshot_job(start_coords, end_coords, base_url, output_dir):
    """Run screenshot job."""
    try:
        start_tx, start_ty, start_px, start_py = start_coords
        end_tx, end_ty, end_px, end_py = end_coords
        
        result = take_screenshot(
            start_tx, start_ty, start_px, start_py,
            end_tx, end_ty, end_px, end_py,
            base_url, output_dir
        )
        if result:
            logger.info(f"Screenshot job completed: {result}")
        else:
            logger.error("Screenshot job failed")
    except Exception as e:
        logger.error(f"Error in screenshot job: {e}")


def main():
    try:
        # Get inputs from user
        url, start_coords, end_coords, output_dir, interval = get_user_inputs()
        
        # Detect tile server
        base_url = detect_tile_server_from_wplace_url(url)
        
        print()
        print("=== Configuration ===")
        print(f"URL: {url}")
        print(f"Start: Tl X: {start_coords[0]}, Tl Y: {start_coords[1]}, Px X: {start_coords[2]}, Px Y: {start_coords[3]}")
        print(f"End: Tl X: {end_coords[0]}, Tl Y: {end_coords[1]}, Px X: {end_coords[2]}, Px Y: {end_coords[3]}")
        print(f"Output: {output_dir}")
        print(f"Interval: {interval} seconds")
        print(f"Tile server: {base_url}")
        print()
        
        # Take initial screenshot
        logger.info("Taking initial screenshot...")
        run_screenshot_job(start_coords, end_coords, base_url, output_dir)
        
        # Schedule recurring screenshots
        logger.info(f"Scheduling screenshots every {interval} seconds. Press Ctrl+C to stop.")
        schedule.every(interval).seconds.do(run_screenshot_job, start_coords, end_coords, base_url, output_dir)
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping screenshot service...")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
