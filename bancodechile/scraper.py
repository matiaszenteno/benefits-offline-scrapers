import csv
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def save_benefits_to_csv(benefits, filename='bancodechile/data/benefits_bancodechile.csv'):
    if not benefits:
        print("No hay beneficios para guardar")
        return False

    try:
        print(f"Guardando {len(benefits)} beneficios en {filename}...")
        fieldnames = [
            'id', 'title', 'description', 'bank', 'provider',
            'category', 'is_active', 'created_at', 'updated_at'
        ]
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, benefit in enumerate(benefits, 1):
                row = {
                    'id': i,
                    'title': benefit.get('title', ''),
                    'description': benefit.get('description', ''),
                    'bank': 'bancodechile',
                    'provider': 'Banco de Chile',
                    'category': benefit.get('category', 'Sin categoría'),
                    'is_active': 1,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                writer.writerow(row)
        print(f"✓ Todos los beneficios han sido guardados en {filename}")
        return True
    except Exception as e:
        print(f"✗ Error al guardar en CSV: {str(e)}")
        return False

def scrape_banco_chile_benefits():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    options.add_argument('--log-level=3')
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    service = Service(log_path=os.devnull)

    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("Navegador inicializado exitosamente")
    except Exception as e:
        print(f"Error al inicializar el navegador: {str(e)}")
        return []

    driver.get("https://sitiospublicos.bancochile.cl/personas/beneficios")

    # Esperar y seleccionar región
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "regionSearch"))
        )
        select_element = driver.find_element(By.ID, "regionSearch")
        select = Select(select_element)
        select.select_by_value("Metropolitana de Santiago")
        print("Región Metropolitana seleccionada")
    except Exception as e:
        print(f"Error al seleccionar región: {str(e)}")
        driver.quit()
        return []

    # Esperar que carguen los beneficios
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.card"))
        )
        print("Beneficios cargados")
    except Exception as e:
        print(f"Error esperando beneficios: {str(e)}")
        driver.quit()
        return []

    benefits = []
    seen_titles = set()
    pagina_actual = 1
    max_paginas = 50

    while pagina_actual <= max_paginas:
        print(f"\nProcesando página {pagina_actual}")

        try:
            benefit_elements = driver.find_elements(By.CSS_SELECTOR, "a.card")
            print(f"Encontrados {len(benefit_elements)} beneficios en la página {pagina_actual}")
        except Exception as e:
            print(f"Error al buscar beneficios: {str(e)}")
            break

        for element in benefit_elements:
            try:
                title = element.find_element(By.CSS_SELECTOR, "p.font-700.text-3.text-gray-dark").text.strip()
                if title in seen_titles:
                    continue
                description = element.find_element(By.CSS_SELECTOR, "p.overflow-ellipsis.mb-2.text-2.text-gray").text.strip()
                benefits.append({
                    'title': title,
                    'description': description,
                    'category': 'Beneficios Bancarios'
                })
                seen_titles.add(title)
            except Exception as e:
                print(f"Error procesando beneficio: {str(e)}")
                continue

        # Intentar click en flecha derecha para siguiente página
        try:
            boton_siguiente = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "i.icos-arrow-right-2.cursor-pointer"))
            )
            boton_siguiente.click()
            pagina_actual += 1
            print("Click en botón siguiente exitoso")
        except Exception as e:
            print(f"No se pudo hacer click en botón siguiente: {e}")

            print(f"Total beneficios extraídos: {len(benefits)}")
            driver.quit()
            return benefits

def main():
    benefits = scrape_banco_chile_benefits()
    if benefits:
        save_benefits_to_csv(benefits)

if __name__ == "__main__":
    main()
