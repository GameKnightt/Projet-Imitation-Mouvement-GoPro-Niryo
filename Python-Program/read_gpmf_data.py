import json
from pathlib import Path
from datetime import datetime
from gpmf_parser import *  # GPMF parser for telemetry data

def extract_gpmf_data(video_path: str, output_path: str = None):
    """Extract GPMF data from a local video file"""
    try:
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"❌ File not found: {video_path}")
            return

        print(f"📊 Extracting GPMF data from {video_path}...")
        
        # Create output path if not specified
        if output_path is None:
            output_path = Path(f"gpmf_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        else:
            output_path = Path(output_path)

        # Parse GPMF data from video file
        parser = Parser(str(video_path))
        gpmf_data = parser.parse_telemetry()

        # Save to JSON file
        with open(output_path, 'w') as f:
            json.dump(gpmf_data, f, indent=4)
        print(f"✅ GPMF data saved to {output_path}")

    except Exception as e:
        print(f"❌ Error extracting GPMF data: {str(e)}")

if __name__ == "__main__":
    # Chemin relatif vers le fichier vidéo dans le projet
    video_file = "video-files/test_gpmf.mp4"
    output_file = "gpmf_output.json"
    
    extract_gpmf_data(video_file, output_file)

