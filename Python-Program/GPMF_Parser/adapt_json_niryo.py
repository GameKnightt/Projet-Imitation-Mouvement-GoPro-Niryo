import numpy as np
import os
import json
from scipy import integrate
from scipy.signal import butter, filtfilt
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

class IMUProcessor:
    def __init__(self, dt=0.01):
        self.dt = dt
        self.kf = self._init_kalman_filter()
        # Paramètres du filtre passe-haut
        self.cutoff_freq = 0.1  # Fréquence de coupure à 0.1 Hz
        self.filter_order = 2   # Ordre du filtre
        
    def _init_kalman_filter(self):
        """Initialize Kalman filter for 3D position tracking"""
        kf = KalmanFilter(dim_x=9, dim_z=3)  # State: [x, y, z, vx, vy, vz, ax, ay, az]
        
        # State transition matrix
        kf.F = np.array([
            [1, 0, 0, self.dt, 0, 0, 0.5*self.dt**2, 0, 0],
            [0, 1, 0, 0, self.dt, 0, 0, 0.5*self.dt**2, 0],
            [0, 0, 1, 0, 0, self.dt, 0, 0, 0.5*self.dt**2],
            [0, 0, 0, 1, 0, 0, self.dt, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, self.dt, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, self.dt],
            [0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Measurement matrix (we only measure acceleration)
        kf.H = np.array([
            [0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Process noise
        kf.Q = Q_discrete_white_noise(3, self.dt, 0.1, block_size=3)
        
        # Measurement noise
        kf.R = np.eye(3) * 0.1
        
        # Initial state uncertainty
        kf.P *= 1000
        
        return kf

    def apply_highpass_filter(self, data):
        """Applique un filtre passe-haut Butterworth sur les données"""
        nyquist = 1.0 / (2.0 * self.dt)
        normal_cutoff = self.cutoff_freq / nyquist
        b, a = butter(self.filter_order, normal_cutoff, btype='high', analog=False)
        
        filtered_data = np.zeros_like(data)
        for i in range(3):  # Pour chaque axe x,y,z
            filtered_data[:, i] = filtfilt(b, a, data[:, i])
            
        return filtered_data

    def integrate_acceleration(self, accel_data):
        """
        Intègre l'accélération filtrée deux fois pour obtenir la position
        """
        dt = self.dt
        time = np.arange(0, len(accel_data) * dt, dt)
        
        # Conversion en array numpy et application du filtre passe-haut
        accel_array = np.array(accel_data)
        filtered_accel = self.apply_highpass_filter(accel_array)
        
        # Première intégration: accélération -> vitesse
        velocity = np.zeros((len(filtered_accel), 3))
        for i in range(3):
            # Utilisation de cumulative_trapezoid au lieu de cumtrapz
            velocity[:, i] = integrate.cumulative_trapezoid(
                filtered_accel[:, i],
                time,
                initial=0
            )
        
        # Deuxième intégration: vitesse -> position
        position = np.zeros((len(velocity), 3))
        for i in range(3):
            # Utilisation de cumulative_trapezoid au lieu de cumtrapz
            position[:, i] = integrate.cumulative_trapezoid(
                velocity[:, i],
                time,
                initial=0
            )
            
        return velocity, position

    def process_acceleration(self, accel_data, sampling_rate=1.0):
        """Process acceleration data and return filtered positions"""
        # Obtention de la position à partir de l'accélération filtrée et intégrée
        velocity, raw_position = self.integrate_acceleration(accel_data)
        
        positions = []
        filtered_data = []
        
        # Resample data based on sampling rate
        step = int(1.0 / sampling_rate / self.dt)
        
        for i in range(0, len(accel_data), step):
            acc = np.array(accel_data[i])
            
            # Update Kalman filter with both acceleration and integrated position
            self.kf.predict()
            self.kf.update(acc)
            
            # Combine raw integrated position with Kalman filter estimate
            kalman_pos = self.kf.x[:3]
            filtered_pos = 0.3 * raw_position[i] + 0.7 * kalman_pos  # Weighted average
            filtered_data.append(filtered_pos.tolist())
            
        return filtered_data

def convert_to_robot_format(imu_data, sampling_rate=1.0):
    """Convert IMU data to Niryo robot format"""
    processor = IMUProcessor()
    
    # Extract acceleration and gyro data from the correct structure
    accel_data = []
    gyro_data = []
    
    try:
        # Debug print pour voir la structure des données
        print("DEBUG: Structure of first IMU data entry:", json.dumps(imu_data[0] if imu_data else {}, indent=2))
        
        for entry in imu_data:
            # Vérifier si les données sont dans la structure correcte
            if isinstance(entry, dict):
                # Essayer différentes structures possibles
                if "Accelerometer" in entry and "Gyroscope" in entry:
                    accel = entry["Accelerometer"].get("3-axis accelerometer", [])
                    gyro = entry["Gyroscope"].get("3-axis gyroscope", [])
                elif "3-axis accelerometer" in entry and "3-axis gyroscope" in entry:
                    accel = entry["3-axis accelerometer"]
                    gyro = entry["3-axis gyroscope"]
                else:
                    print(f"Warning: Skipping entry with unknown structure: {list(entry.keys())}")
                    continue

                # Traitement des données accéléromètre
                if isinstance(accel, list):
                    if accel and isinstance(accel[0], list):
                        # Si nous avons une liste de listes, prenons la première mesure
                        accel = accel[0]
                    if len(accel) == 3:
                        try:
                            accel = [float(x) for x in accel]
                            accel_data.append(accel)
                        except (ValueError, TypeError) as e:
                            print(f"Warning: Could not convert acceleration data: {e}")
                            continue

                # Traitement des données gyroscope
                if isinstance(gyro, list):
                    if gyro and isinstance(gyro[0], list):
                        # Si nous avons une liste de listes, prenons la première mesure
                        gyro = gyro[0]
                    if len(gyro) == 3:
                        try:
                            gyro = [float(x) for x in gyro]
                            gyro_data.append(gyro)
                        except (ValueError, TypeError) as e:
                            print(f"Warning: Could not convert gyroscope data: {e}")
                            continue

        if not accel_data or not gyro_data:
            print("DEBUG: No data collected.")
            print(f"Accelerometer data count: {len(accel_data)}")
            print(f"Gyroscope data count: {len(gyro_data)}")
            raise ValueError("No valid acceleration or gyroscope data found in input")

        print(f"DEBUG: Successfully collected {len(accel_data)} data points")
        
        # Conversion en tableau numpy pour le traitement
        accel_data = np.array(accel_data, dtype=np.float64)
        gyro_data = np.array(gyro_data, dtype=np.float64)
        
        # Process acceleration to get positions
        positions = processor.process_acceleration(accel_data, sampling_rate)
        
        # Convert to robot movements
        movements = {}
        step = int(1.0/sampling_rate/0.01)
        
        print(f"DEBUG: Processing {len(positions)} positions and {len(gyro_data)} gyro data points")
        
        for i, (pos, gyro) in enumerate(zip(positions, gyro_data[::step])):
            try:
                # Vérification et conversion des positions
                if isinstance(pos, (list, np.ndarray)):
                    if isinstance(pos[0], (list, np.ndarray)):
                        pos = pos[0]
                    
                    # Conversion en mètres (au lieu de millimètres)
                    # Les positions sont normalisées entre -1 et 1 puis ajustées à la zone de travail du robot
                    pos_x = float(pos[0]) / 1000.0  # Conversion en mètres
                    pos_y = float(pos[1]) / 1000.0
                    pos_z = float(pos[2]) / 1000.0
                else:
                    print(f"Warning: Invalid position data at index {i}: {pos}")
                    continue

                # Ajustement aux limites de l'espace de travail du Niryo
                x = np.clip(pos_x, -0.5, 0.5)  # Limites en mètres
                y = np.clip(pos_y, -0.5, 0.5)
                z = np.clip(pos_z, 0.1, 0.5)
                
                # Conversion des angles du gyroscope en radians
                # On garde les angles en radians au lieu de les convertir en degrés
                if isinstance(gyro, (list, np.ndarray)):
                    roll = float(gyro[0])  # Déjà en radians
                    pitch = float(gyro[1])
                    yaw = float(gyro[2])
                else:
                    print(f"Warning: Invalid gyro data at index {i}: {gyro}")
                    continue
                
                # Limites des angles en radians
                roll = np.clip(roll, -np.pi, np.pi)
                pitch = np.clip(pitch, -np.pi/2, np.pi/2)
                yaw = np.clip(yaw, -np.pi, np.pi)
                
                # Stockage des valeurs avec la précision appropriée
                movements[f"movement_{i}"] = {
                    "coordinates": [
                        round(x, 6),
                        round(y, 6),
                        round(z, 6),
                        round(roll, 6),
                        round(pitch, 6),
                        round(yaw, 6)
                    ]
                }
                
                if i % 100 == 0:
                    print(f"DEBUG: Processed movement {i}")
                    
            except (ValueError, TypeError, IndexError) as e:
                print(f"Warning: Error processing movement at index {i}: {str(e)}")
                print(f"Position data: {pos}")
                print(f"Gyro data: {gyro}")
                continue

        print(f"DEBUG: Final movements count: {len(movements)}")
        if len(movements) == 0:
            raise ValueError("No valid movements were generated")
            
        return movements
    
    except Exception as e:
        print(f"Error processing IMU data: {str(e)}")
        raise

def save_movements_to_json(movements, filename_base):
    """Save processed movements to JSON file"""
    # Créer le dossier s'il n'existe pas
    output_dir = os.path.join(os.path.dirname(__file__), "3-Json-adapt-niryo-movement")
    os.makedirs(output_dir, exist_ok=True)
    
    # Correction du nom de fichier
    filename_base = filename_base.replace('.json', '')  # Enlever l'extension .json si présente
    output_file = os.path.join(output_dir, f"niryo_{filename_base}.json")
    
    try:
        with open(output_file, 'w') as f:
            json.dump(movements, f, indent=4)
        print(f"Successfully saved movements to {output_file}")
    except Exception as e:
        print(f"Error saving movements to {output_file}: {str(e)}")

def load_and_process_imu_data(input_file):
    """Load IMU data from JSON and process it"""
    try:
        with open(input_file, 'r') as f:
            imu_data = json.load(f)
        
        movements = convert_to_robot_format(imu_data)
        filename_base = input_file.split('/')[-1].replace('.json', '')
        save_movements_to_json(movements, filename_base)
        
        return True
    except Exception as e:
        print(f"Error processing IMU data: {str(e)}")
        return False

# Example usage
if __name__ == "__main__":
    input_dir = os.path.join(os.path.dirname(__file__), "2-Reorder-IMU-Data")
    for json_file in os.listdir(input_dir):
        if json_file.endswith('.json'):
            input_path = os.path.join(input_dir, json_file)
            load_and_process_imu_data(input_path)
