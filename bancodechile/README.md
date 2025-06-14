# Scraper Offline Banco de Chile

Este script permite extraer beneficios del sitio web de Banco de Chile y guardarlos en un archivo CSV.

## Requisitos

1. **Python 3.7+**
2. **Google Chrome** instalado
3. **ChromeDriver** (se puede instalar automáticamente con webdriver-manager)

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements_scraper.txt
```

2. Si no tienes ChromeDriver instalado, puedes usar webdriver-manager para instalarlo automáticamente:
```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
```

## Uso

### Ejecución básica
```bash
python scraper_offline_bancodechile.py
```

### Configuración

El script está configurado para:
- Ejecutarse en modo headless (sin ventana del navegador)
- Procesar las primeras 3 páginas de beneficios
- Guardar los resultados en `benefits_bancodechile.csv`

### Personalización

Para modificar el comportamiento del script, puedes editar las siguientes variables en `scraper_offline_bancodechile.py`:

```python
# Cambiar a False para ver el navegador en acción
options.add_argument('--headless')

# Cambiar el número de páginas a procesar
max_paginas = 3

# Cambiar el nombre del archivo de salida
save_benefits_to_csv(benefits, 'mi_archivo_personalizado.csv')
```

## Archivo de salida

El script genera un archivo CSV con las siguientes columnas:
- `id`: ID único del beneficio
- `title`: Título del beneficio
- `description`: Descripción del beneficio
- `bank`: Banco (siempre "bancodechile")
- `provider`: Proveedor (siempre "Banco de Chile")
- `category`: Categoría del beneficio
- `is_active`: Estado activo (siempre 1)
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización

## Solución de problemas

### Error de ChromeDriver
Si obtienes un error relacionado con ChromeDriver:
1. Asegúrate de tener Google Chrome instalado
2. Instala ChromeDriver manualmente o usa webdriver-manager
3. Verifica que ChromeDriver esté en tu PATH

### Error de conexión
Si obtienes errores de conexión:
1. Verifica tu conexión a internet
2. Comprueba que el sitio web esté disponible
3. Considera usar un proxy si es necesario

### Selectores CSS obsoletos
Si el script no encuentra elementos:
1. Los selectores CSS pueden haber cambiado en el sitio web
2. Inspecciona el sitio web para encontrar los nuevos selectores
3. Actualiza los selectores en el código

## Notas importantes

- El script respeta los tiempos de carga del sitio web
- Incluye manejo de errores robusto
- Guarda automáticamente el progreso en caso de errores
- Es compatible con las mismas columnas que la base de datos original 