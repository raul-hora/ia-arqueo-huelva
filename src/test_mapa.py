import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import os

# Usamos el archivo MDT02 que tienes en la carpeta mdt
# He copiado el nombre exacto de tu captura de pantalla
archivo_nombre = "MDT02-ETRS89-HU29-0982-3-COB2.tif"
ruta = os.path.join("..", "datos", "mdt", archivo_nombre)

print(f"Buscando archivo en: {os.path.abspath(ruta)}")

try:
    with rasterio.open(ruta) as dataset:
        print("-" * 30)
        print(f"✅ ÉXITO: Archivo abierto correctamente")
        print(f"📍 Sistema de Coordenadas (CRS): {dataset.crs}")
        print(f"📏 Dimensiones: {dataset.width} x {dataset.height} píxeles")
        print("-" * 30)

        # Visualización
        plt.figure(figsize=(10, 8))
        show(dataset, cmap='terrain', title="MDT Trigueros - Huelva")
        plt.show()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nSugerencia: Comprueba que estás ejecutando el script desde la carpeta 'src'")