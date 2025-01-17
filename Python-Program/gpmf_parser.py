import os
from py_gpmf_parser.gopro_telemetry_extractor import GoProTelemetryExtractor

def extract_telemetry(filepath: str, output_file: str = None):
    """Extract telemetry from GoPro video file"""
    print(f"Processing file: {filepath}")

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return

    # If no output file specified, create one based on input filename
    if output_file is None:
        output_file = os.path.basename(filepath) + ".json"

    try:
        print("Creating telemetry extractor...")
        extractor = GoProTelemetryExtractor(filepath)
        
        print("Opening source file...")
        extractor.open_source()

        print("Extracting data to JSON...")
        extractor.extract_data_to_json(
            output_file, 
            ["ACCL", "GYRO", "GPS5", "GRAV", "MAGN", "CORI", "IORI"]
        )

        print("Closing source file...")
        extractor.close_source()

        print("✅ Telemetry extraction complete!")
        return True

    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        return False

if __name__ == "__main__":
    video_file = './video-files/test_gpmf.mp4'
    extract_telemetry(video_file)