import cv2 #Video processing
import json
import requests
import asyncio
from open_gopro import * # GoPro control
from gpmf_parser import * # GPMF parser for telemetry data
from pyniryo import * # Robot control
import numpy as np # Data processing
import pandas as pd # Data processing

# Additional useful imports from standard library
import time
from pathlib import Path

# Change the serial number to a string
gopro = WiredGoPro("C3464225067910")

async def main():
    try:
        # Initialize and connect to the GoPro via USB
        print("Connecting to GoPro...")
        await gopro.open()
        # Wait for the GoPro to be ready
        gopro.http_command.get_media_list()
        print("GoPro connected successfully!")

        # Wait for user input before taking photo
        input("Press ENTER to take a photo...")
        
        # Take a photo
        print("Taking photo...")
        gopro.http_command.set_shutter(shutter=True)
        time.sleep(1)  # Wait for the photo to be taken
        gopro.http_command.set_shutter(shutter=False)
        print("Photo taken!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

