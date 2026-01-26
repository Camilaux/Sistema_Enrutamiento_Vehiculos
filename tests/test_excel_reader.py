"""
Script de prueba para verificar la lectura del archivo Excel.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path para poder importar desde src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.excel_reader import leer_escenario, listar_escenarios_disponibles


def main():
    filepath = "../data/datos_prueba_enrutamiento.xlsx"
    
    try:
        # Listar escenarios disponibles
        print("=" * 60)
        print("Escenarios disponibles:")
        escenarios = listar_escenarios_disponibles(filepath)
        print(f"  {escenarios}")
        print()
        
        # Probar lectura de cada escenario
        for escenario in escenarios:
            print("=" * 60)
            print(f"Escenario: {escenario}")
            print("=" * 60)
            
            vehiculos, pedidos = leer_escenario(filepath, escenario)
            
            print(f"\nVehículos ({len(vehiculos)}):")
            for v in vehiculos:
                print(f"  - {v.id}: Capacidad {v.capacidad_kg} kg, "
                      f"Origen ({v.latitud_origen}, {v.longitud_origen})")
            
            print(f"\nPedidos ({len(pedidos)}):")
            for p in pedidos[:5]:  # Mostrar solo los primeros 5
                print(f"  - {p.id}: Peso {p.peso_kg} kg, "
                      f"Destino ({p.latitud_destino}, {p.longitud_destino}), "
                      f"Ventana {p.ventana_inicio}-{p.ventana_fin}, "
                      f"Prioridad {p.prioridad}")
            if len(pedidos) > 5:
                print(f"  ... y {len(pedidos) - 5} pedidos más")
            print()
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
