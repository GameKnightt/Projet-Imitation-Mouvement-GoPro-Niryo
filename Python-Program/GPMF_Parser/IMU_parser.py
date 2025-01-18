import json
import matplotlib.pyplot as plt
import numpy as np
import os


def get_gyro_accel_data(imu_json):
    """Extract and flatten gyroscopic, accelerometer, and time data from the IMU data .json file"""
    print(f"Reading JSON file: {os.path.basename(imu_json)}")
    with open(imu_json, 'r') as f:
        imu_data = json.load(f)

    print("Extracting gyroscope and accelerometer data...")
    data = []

    for entry in imu_data:
        if "Gyroscope" in entry and "3-axis gyroscope" in entry["Gyroscope"]:
            gyro_data = entry["Gyroscope"]["3-axis gyroscope"]
        else:
            gyro_data = []

        if "Accelerometer" in entry and "3-axis accelerometer" in entry["Accelerometer"]:
            accel_data = entry["Accelerometer"]["3-axis accelerometer"]
        else:
            accel_data = []

        if "Interval in ms" in entry:
            start_time, end_time = map(int, entry["Interval in ms"].strip("()").split(", "))
            interval_duration = end_time - start_time
            sample_interval = interval_duration / 199
        else:
            start_time = 0
            sample_interval = 0

        for i in range(len(gyro_data)):
            timestamp = start_time + i * sample_interval
            data_entry = {
                "3-axis gyroscope": gyro_data[i] if i < len(gyro_data) else None,
                "3-axis accelerometer": accel_data[i] if i < len(accel_data) else None,
                "Timestamp in ms": timestamp
            }
            data.append(data_entry)

    return data


def reorder_data(data, base_filename):
    print(f"Reordering data axes for {base_filename}")
    output_dir = os.path.join(os.path.dirname(__file__), "2-Reorder-IMU-Data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"reordered_{base_filename}")
    
    print("Reorganizing axis orientations...")
    # Data order in gyro and accel is Y, -X, Z and we want X, Y, Z
    for entry in data:
        gyro = entry["3-axis gyroscope"]
        accel = entry["3-axis accelerometer"]
        entry["3-axis gyroscope"] = [-gyro[1], gyro[0], gyro[2]]
        entry["3-axis accelerometer"] = [-accel[1], accel[0], accel[2]]

    print(f"Saving reordered data to: {os.path.basename(output_path)}")
    # Write the reordered data to a JSON file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

    return data


def get_gravity_data(imu_json):
    """Extract and flatten gravity data from the IMU data .json file"""
    # Utiliser un chemin absolu
    imu_json = r'c:\Users\alexy\Dropbox\PC\Desktop\IUT Nantes\GEII\BUT_3\SAé6-GoPro_Niryo\Projet-Imitation-Mouvement-GoPro-Niryo\gopro-telemetry2json\IMU_test.json'
    with open(imu_json, 'r') as f:
        imu_data = json.load(f)

    gravity_data = []
    gravity_timestamps = []

    for entry in imu_data:
        if "Gravity Vector" in entry:
            gravity_vector = entry["Gravity Vector"]["Gravity Vector"]
            timestamp = entry["Gravity Vector"]["Timestamp in microseconds"] / 1000.0  # Convert to milliseconds
            sample_interval = 1001 / 59  # 60 samples over 1001ms interval

            for i, vector in enumerate(gravity_vector):
                gravity_data.append(vector)
                gravity_timestamps.append(timestamp + i * sample_interval)

    return gravity_data, gravity_timestamps


def plot_data(data):
    """Plot gyroscope and accelerometer data"""
    timestamps = [entry["Timestamp in ms"] for entry in data]
    gyro_x = [entry["3-axis gyroscope"][0] for entry in data]
    gyro_y = [entry["3-axis gyroscope"][1] for entry in data]
    gyro_z = [entry["3-axis gyroscope"][2] for entry in data]
    accel_x = [entry["3-axis accelerometer"][0] for entry in data]
    accel_y = [entry["3-axis accelerometer"][1] for entry in data]
    accel_z = [entry["3-axis accelerometer"][2] for entry in data]

    plt.figure(figsize=(12, 6))

    plt.subplot(2, 1, 1)
    plt.plot(timestamps, gyro_x, label='Gyro X')
    plt.plot(timestamps, gyro_y, label='Gyro Y')
    plt.plot(timestamps, gyro_z, label='Gyro Z')
    plt.title('Gyroscope Data')
    plt.xlabel('Timestamp (ms)')
    plt.ylabel('Gyroscope (rad/s)')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(timestamps, accel_x, label='Accel X')
    plt.plot(timestamps, accel_y, label='Accel Y')
    plt.plot(timestamps, accel_z, label='Accel Z')
    plt.title('Accelerometer Data')
    plt.xlabel('Timestamp (ms)')
    plt.ylabel('Accelerometer (m/s²)')
    plt.legend()

    plt.tight_layout()
    plt.show()


# Example usage
if __name__ == "__main__":
    input_dir = os.path.join(os.path.dirname(__file__), "1-IMU-Json-Extract")
    for json_file in os.listdir(input_dir):
        if json_file.endswith('.json'):
            input_path = os.path.join(input_dir, json_file)
            data = get_gyro_accel_data(input_path)
            data = reorder_data(data, json_file)
            #plot_data(data)
