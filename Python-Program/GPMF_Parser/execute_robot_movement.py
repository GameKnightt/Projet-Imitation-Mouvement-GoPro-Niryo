import os
from pyniryo import *
import json
import time

def load_movements(filename):
    """Charge les mouvements depuis le fichier JSON"""
    file_path = os.path.join(os.path.dirname(__file__), "3-Json-adapt-niryo-movement", filename)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            # Convertir les données en format séquence
            sequence = {
                "positions": [
                    {
                        "name": key,  # Utiliser le nom original du mouvement (movement_X)
                        "coordinates": movement["coordinates"]
                    }
                    for key, movement in data.items()
                ]
            }
            sequence["positions"].sort(key=lambda x: int(x["name"].split("_")[1]))  # Trier par numéro de mouvement
            return sequence
    except FileNotFoundError:
        print(f"Erreur: Le fichier {file_path} n'existe pas")
        raise
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier {file_path} n'est pas un JSON valide")
        raise
    except Exception as e:
        print(f"Erreur lors du chargement du fichier: {str(e)}")
        raise

def calibrate_robot(robot):
    """
    Procédure de calibration du robot.
    Importante pour assurer la précision des mouvements.
    """
    while True:
        response = input("Voulez-vous calibrer le robot ? (o/n): ").lower()
        if response in ['o', 'n']:
            if response == 'o':
                print("Démarrage de la calibration...")
                robot.calibrate_auto()
                print("Calibration terminée!")
            break
        print("Veuillez répondre par 'o' pour oui ou 'n' pour non.")

def configure_tool(robot):
    """
    Configuration de l'outil et du TCP (Tool Center Point).
    
    Options:
    1. Pince (gripper)
    2. Ventouse (vacuum)
    
    Ajuste les paramètres TCP en fonction de l'outil sélectionné.
    """
    # Définition des TCPs
    VACUUM_TCP = [0.05, 0, 0, 0, 0, 0]  # TCP pour la ventouse
    GRIPPER_TCP = [0.085, 0, 0, 0, 0, 0]  # TCP pour la pince

    while True:
        print("\nSélection de l'outil:")
        print("1. Pince")
        print("2. Ventouse")
        tool_type = input("Choisissez l'outil (1/2): ")
        
        if tool_type in ['1', '2']:
            # Sélection du TCP en fonction de l'outil
            selected_tcp = VACUUM_TCP if tool_type == "2" else GRIPPER_TCP
            tool_name = "Ventouse" if tool_type == "2" else "Pince"

            # Configuration du TCP
            print("\nConfiguration du TCP...")
            robot.reset_tcp()
            print('TCP Reset')
            robot.set_tcp(selected_tcp)
            print(f'TCP Set pour {tool_name}')
            robot.enable_tcp(True)
            print('TCP Activé')
            break
        print("Choix invalide. Veuillez sélectionner 1 ou 2.")

def execute_sequence(robot, sequence_file):
    """
    Exécute une séquence de mouvements à partir d'un fichier JSON
    Args:
        robot: Instance du robot Niryo
        sequence_file: Nom du fichier JSON contenant la séquence
    """
    try:
        # Charger la séquence
        movements = load_movements(sequence_file)
        total_positions = len(movements['positions'])
        
        print(f"\n=== Exécution de la séquence de mouvements ===")
        print(f"Nombre total de positions: {total_positions}")
        
        # Attendre la confirmation initiale de l'utilisateur
        input("\nAppuyez sur Entrée pour démarrer la séquence...")
        
        # Ouvrir la pince au maximum avant de commencer
        print("\nOuverture de la pince...")
        robot.open_gripper(speed=500)
        print("Pince ouverte!")
        
        # Exécuter chaque mouvement automatiquement
        for i, position in enumerate(movements['positions'], 1):
            try:
                print(f"\nExécution mouvement {i}/{total_positions}: {position['name']}")
                coordinates = position['coordinates']
                # Exécuter le mouvement
                robot.move_pose(*coordinates)
                
            except Exception as e:
                print(f"Erreur lors du mouvement {i}: {str(e)}")
                choice = input("Continuer la séquence? (o/n): ")
                if choice.lower() != 'o':
                    break
        
        print("\n=== Séquence terminée ===")
        
    except Exception as e:
        print(f"Erreur lors de l'exécution de la séquence: {str(e)}")
        raise

def main():
    # Connexion au robot
    print("Connexion au robot...")
    robot = NiryoRobot("172.21.182.56")
    print("Robot connecté!")

    try:
        # Calibration si nécessaire
        calibrate_robot(robot)

        # Configuration de l'outil et du TCP
        configure_tool(robot)

        # Désactiver le mode apprentissage et configurer la vitesse
        robot.set_arm_max_velocity(100)  # Augmenter de 100 à 150%
        robot.set_learning_mode(False)

        # Sélection et exécution de la séquence
        sequence_dir = os.path.join(os.path.dirname(__file__), "3-Json-adapt-niryo-movement")
        sequences = [f for f in os.listdir(sequence_dir) if f.endswith('.json')]
        
        print("\nSéquences disponibles:")
        for i, seq in enumerate(sequences, 1):
            print(f"{i}. {seq}")
            
        while True:
            try:
                choice = input("\nChoisissez le numéro de la séquence à exécuter (ou 'q' pour quitter): ")
                if choice.lower() == 'q':
                    break
                    
                index = int(choice) - 1
                if 0 <= index < len(sequences):
                    selected_sequence = sequences[index]
                    execute_sequence(robot, selected_sequence)
                    break
                else:
                    print("Choix invalide. Veuillez réessayer.")
            except ValueError:
                print("Veuillez entrer un numéro valide.")

    except Exception as e:
        print(f"Erreur: {str(e)}")
    finally:
        #Fermer la connexion
        robot.close_connection()

if __name__ == "__main__":
    main()