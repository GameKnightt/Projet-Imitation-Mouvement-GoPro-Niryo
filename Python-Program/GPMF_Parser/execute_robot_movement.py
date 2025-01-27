import os
from pyniryo import *
import json
import time
import keyboard

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

# Suppression des fonctions convert_color_to_value, rgb_cycle et orange_blink qui ne sont plus nécessaires

def calibrate_robot(robot):
    """Calibration du robot si nécessaire"""
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
    """Configuration de l'outil et du TCP"""
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

def main():
    # Connexion au robot
    print("Connexion au robot...")
    robot = NiryoRobot("172.21.182.56")
    print("Robot connecté!")

    # Activer le mode autonome
    robot.set_arm_max_velocity(100)
    robot.set_learning_mode(False)

    try:
        # Calibration si nécessaire
        calibrate_robot(robot)

        # Configuration de l'outil et du TCP
        configure_tool(robot)

        # Ouvrir la pince au maximum
        print("Ouverture de la pince...")
        robot.open_gripper(speed=100)
        print("Pince ouverte!")

        # Chargement des mouvements
        print("Chargement des mouvements...")
        sequence_config = load_movements("niryo_test_gpmf.json")
        print(f"Nombre de mouvements chargés : {len(sequence_config['positions'])}")

        print("\nPréparation terminée!")
        print("Appuyez sur Entrée pour démarrer la séquence de mouvements...")
        keyboard.wait('enter')

        # Exécution des mouvements
        for position in sequence_config["positions"]:
            try:
                print(f"\nDéplacement vers: {position['name']}")
                robot.move_pose(*position["coordinates"])
                time.sleep(0.1)
            except Exception as e:
                print(f"Erreur lors du mouvement vers {position['name']}: {e}")
                break

    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")
    finally:
        # Réactiver le mode apprentissage
        robot.set_learning_mode(True)
        # Déconnecter le robot
        robot.close_connection()

if __name__ == "__main__":
    main()