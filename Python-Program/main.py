import cv2 #Video processing
import json
import requests
import asyncio
from open_gopro import * # GoPro control
#from gpmf_parser import * # GPMF parser for telemetry data
from pyniryo import * # Robot control
import numpy as np # Data processing
import pandas as pd # Data processing

# Additional useful imports from standard library
import time
from pathlib import Path
from datetime import datetime

# Change the serial number to a string
gopro = WiredGoPro("910")

async def get_gopro_info():
    try:
        print("Connecting to GoPro...")
        await gopro.open()
        await asyncio.sleep(2)  # Ensure stable connection

        # Add keep alive command
        print("🔄 Setting keep alive...")
        await gopro.http_command.set_keep_alive()
        await asyncio.sleep(1)

        #Enable the usb control
        gopro.http_command.wired_usb_control(control=1)

        print("Getting camera information...")
        info = await gopro.http_command.get_camera_info()
        
        # Create a dictionary with relevant information and timestamp
        camera_data = {
            "timestamp": datetime.now().isoformat(),
            "camera_info": {
                "model": info.model_name,
                "firmware_version": info.firmware_version,
                "serial_number": info.serial_number,
                "ap_ssid": info.ap_ssid,
                "ap_mac": info.ap_mac
            }
        }

        # Save to JSON file with timestamp in filename
        filename = f"gopro_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(camera_data, f, indent=4)
        
        print(f"Camera information saved to {filename}")
        return camera_data

    except Exception as e:
        print(f"Error getting camera information: {str(e)}")
        return None
    finally:
        await gopro.close()
        print("Connection closed")

if __name__ == "__main__":
    asyncio.run(get_gopro_info())

