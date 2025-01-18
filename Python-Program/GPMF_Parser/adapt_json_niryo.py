import json
import numpy as np
import os

def gyro_to_rpy(gyro):
    # Placeholder function to convert gyroscope data to Roll, Pitch, Yaw
    roll = gyro[0]
    pitch = gyro[1]
    yaw = gyro[2]
    return roll, pitch, yaw

def accel_to_xyz(accel):
    # Placeholder function to convert accelerometer data to X, Y, Z positions
    x = accel[0]
    y = accel[1]
    z = accel[2]
    return x, y, z

def convert_to_robot_format(data):
    movements = {}
    for i, entry in enumerate(data):
        gyro = entry["3-axis gyroscope"]
        accel = entry["3-axis accelerometer"]
        timestamp = entry["Timestamp in ms"]

        # Convert gyroscope and accelerometer data to Roll, Pitch, Yaw and X, Y, Z
        roll, pitch, yaw = gyro_to_rpy(gyro)
        x, y, z = accel_to_xyz(accel)

        movement = [x, y, z, roll, pitch, yaw]
        movements[f"movement_{i}"] = movement
    
    return movements

def save_movements_to_json(movements, base_filename):
    output_dir = os.path.join(os.path.dirname(__file__), "3-Json-adapt-niryo-movement")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"niryo_{base_filename}")
    
    with open(output_path, 'w') as f:
        json.dump(movements, f, indent=4)

# Example usage
if __name__ == "__main__":
    input_dir = os.path.join(os.path.dirname(__file__), "2-Reorder-IMU-Data")
    for json_file in os.listdir(input_dir):
        if json_file.endswith('.json'):
            input_path = os.path.join(input_dir, json_file)
            with open(input_path, 'r') as f:
                data = json.load(f)
            movements = convert_to_robot_format(data)
            save_movements_to_json(movements, json_file)
