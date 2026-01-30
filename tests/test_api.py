"""
Script de prueba para verificar que la API REST funciona correctamente.
"""
import requests
import sys
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
DATA_FILE = Path(__file__).parent.parent / "data" / "datos_prueba_enrutamiento.xlsx"

def test_health():
    """Prueba el endpoint de health check."""
    print("=" * 60)
    print("Probando endpoint /health")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor. Asegúrate de que esté corriendo (python src/main.py).")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_escenarios():
    """Prueba el endpoint para listar escenarios."""
    print("\n" + "=" * 60)
    print("Probando endpoint /api/escenarios")
    print("=" * 60)
    try:
        with open(DATA_FILE, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/escenarios",
                files={'file': f}
            )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_enrutar(escenario="E1"):
    """Prueba el endpoint de enrutamiento."""
    print("\n" + "=" * 60)
    print(f"Probando endpoint /api/enrutar con escenario {escenario}")
    print("=" * 60)
    try:
        with open(DATA_FILE, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/enrutar?escenario={escenario}",
                files={'file': f}
            )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Escenario: {result.get('escenario')}")
            print(f"Total pedidos: {result.get('metricas_generales', {}).get('total_pedidos')}")
            print(f"Vehículos: {len(result.get('vehiculos', []))}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Iniciando pruebas (Asegúrate de tener el servidor corriendo)...")
    
    tests = [
        ("Health Check", test_health),
        ("Listar Escenarios", test_list_escenarios),
        ("Enrutar E1", lambda: test_enrutar("E1")),
    ]
    
    results = []
    # Si falla el health check, abortamos
    if not test_health():
        sys.exit(1)
        
    # Ejecutar resto de pruebas
    for name, test_func in tests:
        if name == "Health Check": continue 
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Error en {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Resumen de pruebas:")
    print("=" * 60)
    print("[PASS] - Health Check") # Ya pasó
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
