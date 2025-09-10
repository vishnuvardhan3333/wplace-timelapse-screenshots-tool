# 📸 Blue Marble Autonomous Screenshot Tool

A simple, interactive Python tool that automatically captures screenshots from wplace.live at regular intervals using Blue Marble's coordinate system.

## ✨ Features

- **🎯 Interactive Setup**: Simple prompts guide you through configuration
- **📋 Copy-Paste Friendly**: Directly paste coordinates from Blue Marble (with or without braces)
- **🌍 Smart Region Detection**: Automatically detects the correct tile server based on your wplace.live URL
- **⏰ Scheduled Capture**: Takes screenshots at your specified interval
- **🔄 Robust Tile Fetching**: Handles missing tiles and network issues gracefully
- **📁 Organized Output**: Saves timestamped screenshots in your chosen directory

## 🚀 Quick Start

### Prerequisites
```bash
pip install requests pillow schedule
```

### Usage
Simply run the script and follow the interactive prompts:
```bash
python auto_snap.py
```

## 📝 Interactive Setup Process

The tool will prompt you for:

1. **🌐 wplace.live URL**: Paste the URL from your browser
2. **📍 Start Coordinates**: Copy-paste from Blue Marble (e.g., `(Tl X: 1470, Tl Y: 923, Px X: 600, Px Y: 400)`)
3. **📍 End Coordinates**: Define the bottom-right corner of your capture area
4. **📁 Output Directory**: Where to save screenshots (default: `screenshots`)
5. **⏱️ Interval**: How often to take screenshots (in seconds)

### Example Session
```
=== Blue Marble Autonomous Screenshot Tool ===

Enter wplace.live URL: https://wplace.live/?lat=17.309&lng=78.585&zoom=12.7
Enter START coordinates (copy from Blue Marble): (Tl X: 1470, Tl Y: 923, Px X: 600, Px Y: 400)
✓ Parsed: Tl X: 1470, Tl Y: 923, Px X: 600, Px Y: 400
Enter END coordinates (copy from Blue Marble): (Tl X: 1471, Tl Y: 924, Px X: 200, Px Y: 800)
✓ Parsed: Tl X: 1471, Tl Y: 924, Px X: 200, Px Y: 800
Enter output directory (default: screenshots): my_screenshots
Enter screenshot interval in seconds (e.g., 3600 for 1 hour): 1800

=== Configuration ===
URL: https://wplace.live/?lat=17.309&lng=78.585&zoom=12.7
Start: Tl X: 1470, Tl Y: 923, Px X: 600, Px Y: 400
End: Tl X: 1471, Tl Y: 924, Px X: 200, Px Y: 800
Output: my_screenshots
Interval: 1800 seconds
Tile server: https://backend.wplace.live/files/s0/tiles

Taking initial screenshot...
2025-09-10 14:30:00,123 - INFO - Taking screenshot from (1470,923,600,400) to (1471,924,200,800)
2025-09-10 14:30:02,456 - INFO - Screenshot saved: my_screenshots/screenshot_2025-09-10_14-30-02.png
2025-09-10 14:30:02,457 - INFO - Scheduling screenshots every 1800 seconds. Press Ctrl+C to stop.
```

## 🎯 How to Get Coordinates from Blue Marble

1. Open Blue Marble userscript on wplace.live
2. Click on a pixel to see coordinates in the UI
3. Copy the displayed coordinates (including braces): `(Tl X: 1470, Tl Y: 923, Px X: 600, Px Y: 400)`
4. Paste directly into the tool - it handles the braces automatically!

## 📊 Coordinate System

The tool uses Blue Marble's tile-based coordinate system:
- **Tl X, Tl Y**: Tile coordinates (each tile is 1000×1000 pixels)
- **Px X, Px Y**: Pixel coordinates within the tile (0-999)

## 🔧 Advanced Features

### Region Detection
Automatically detects the correct wplace.live tile server based on your URL:
- **India**: Detects from lat/lng coordinates (uses season s0)
- **Europe**: Geographic detection (uses season s1)
- **North America**: Geographic detection (uses season s2)
- **Fallback**: Tries multiple seasons if tiles aren't found

### Output Format
- Screenshots saved as PNG files
- Timestamped filenames: `screenshot_YYYY-MM-DD_HH-MM-SS.png`
- Automatic directory creation
- Detailed logging to `autonomous_screenshot.log`

### Error Handling
- Validates coordinate formats
- Handles missing tiles gracefully
- Network timeout protection
- Automatic retry with different tile servers

## 🛑 Stopping the Tool

Press **Ctrl+C** to gracefully stop the screenshot service. The tool will finish the current operation before exiting.

## 📁 Output

- **Screenshots**: Saved in your specified directory with timestamps
- **Logs**: Detailed operation log in `autonomous_screenshot.log`
- **Status**: Real-time progress information in the console

## 🔍 Troubleshooting

**No tiles found?**
- Verify your coordinates are correct
- Check that the wplace.live URL loads the correct region
- Ensure stable internet connection

**Coordinate parsing errors?**
- Copy coordinates exactly from Blue Marble
- Format: `(Tl X: 1470, Tl Y: 923, Px X: 600, Px Y: 400)`
- Tool accepts with or without braces

**Network issues?**
- Tool automatically retries with different tile servers
- Check logs for detailed error information

## 💡 Use Cases

- **Art Project Monitoring**: Track changes in collaborative pixel art
- **Region Documentation**: Create time-lapse sequences of specific areas
- **Community Events**: Monitor special events or competitions

## 🎨 Example Screenshot Scenarios

- **Small Detail**: `(Tl X: 1470, Tl Y: 923, Px X: 900, Px Y: 900)` to `(Tl X: 1470, Tl Y: 923, Px X: 999, Px Y: 999)` - 100×100 pixel area
- **Single Tile**: `(Tl X: 1470, Tl Y: 923, Px X: 0, Px Y: 0)` to `(Tl X: 1470, Tl Y: 923, Px X: 999, Px Y: 999)` - Full 1000×1000 tile
- **Multi-Tile Area**: `(Tl X: 1470, Tl Y: 923, Px X: 500, Px Y: 500)` to `(Tl X: 1472, Tl Y: 925, Px X: 500, Px Y: 500)` - Large region

---

**Built for the Blue Marble community** 🌍✨
