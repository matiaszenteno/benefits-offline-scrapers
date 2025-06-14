#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper offline para Entel Club
Extrae beneficios del Club Entel y los guarda en un archivo CSV
"""

import csv
import os
import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import socket

def test_internet_connection():
    """Prueba la conexión a internet"""
    try:
        print("Probando conexión a internet...")
        socket.gethostbyname('www.google.com')
        print("✓ Resolución DNS funcionando")
        
        response = requests.get('http://www.google.com', timeout=5)
        print(f"✓ Conexión HTTP funcionando (status code: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Error en la conexión a internet: {str(e)}")
        return False

def save_benefits_to_csv(benefits, filename='benefits_entel.csv'):
    """Guarda los beneficios en un archivo CSV"""
    if not benefits:
        print("No hay beneficios para guardar")
        return False
    
    try:
        # Crear directorio data si no existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        print(f"Guardando {len(benefits)} beneficios en {filename}...")
        
        # Definir las columnas del CSV (mismas que la base de datos)
        fieldnames = [
            'id',
            'title', 
            'description',
            'bank',
            'provider',
            'category',
            'is_active',
            'created_at',
            'updated_at',
            'url'  # Campo adicional para la URL del beneficio
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Escribir headers
            writer.writeheader()
            
            # Escribir beneficios
            for i, benefit in enumerate(benefits, 1):
                row = {
                    'id': i,
                    'title': benefit.get('title', ''),
                    'description': benefit.get('description', ''),
                    'bank': 'entel',
                    'provider': 'Entel',
                    'category': benefit.get('category', 'Club Entel'),
                    'is_active': 1,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'url': benefit.get('url', '')
                }
                writer.writerow(row)
                print(f"Beneficio {i}/{len(benefits)} guardado: {benefit.get('title', '')[:50]}...")
        
        print(f"✓ Todos los beneficios han sido guardados en {filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error al guardar en CSV: {str(e)}")
        return False

def extract_benefit_from_json(json_data):
    """Extrae información del beneficio desde el JSON embebido en el HTML"""
    try:
        # El JSON está en formato de string escapado, necesitamos parsearlo
        if isinstance(json_data, str):
            # Decodificar entidades HTML
            json_data = json_data.replace('&quot;', '"')
            data = json.loads(json_data)
        else:
            data = json_data
        
        if isinstance(data, list) and len(data) > 0:
            benefit_data = data[0]
            
            title = benefit_data.get('title', '')
            description = benefit_data.get('text', '')
            url = benefit_data.get('href', '')
            
            # Limpiar la descripción de markdown
            if description:
                description = re.sub(r'\*\*(.*?)\*\*', r'\1', description)  # Remover **texto**
                description = description.strip()
            
            return {
                'title': title,
                'description': description,
                'url': url
            }
    except Exception as e:
        print(f"Error al parsear JSON: {str(e)}")
        return None
    
    return None

def scrape_entel_benefits():
    """Función principal para hacer scraping de beneficios de Entel"""
    try:
        print("=== SCRAPER OFFLINE ENTEL CLUB ===")
        print("Iniciando proceso de scraping...")
        
        # Verificar conexión a internet
        if not test_internet_connection():
            print("Error: No hay conexión a internet")
            return []
        
        # Configurar Chrome
        print("\nConfigurando Chrome...")
        options = Options()
        options.add_argument('--headless')  # Cambiar a False si quieres ver el navegador
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--log-level=3')
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        
        print("Opciones de Chrome configuradas:")
        for arg in options.arguments:
            print(f"- {arg}")

        # Inicializar el navegador
        print("\nInicializando navegador...")
        try:
            service = Service(log_path=os.devnull)
            driver = webdriver.Chrome(service=service, options=options)
            print("✓ Navegador inicializado exitosamente")
        except Exception as e:
            print(f"✗ Error al inicializar el navegador: {str(e)}")
            print("Asegúrate de tener ChromeDriver instalado y en el PATH")
            return []

        # Abrir la página de beneficios de Entel
        print("\nAccediendo a la página de beneficios de Entel...")
        try:
            driver.get("https://www.entel.cl/beneficios/")
            print("✓ Página cargada exitosamente")
        except Exception as e:
            print(f"✗ Error al cargar la página: {str(e)}")
            driver.quit()
            return []
        
        # Esperar a que carguen los beneficios
        print("\nEsperando a que carguen los beneficios...")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "andino-card-general"))
            )
            print("✓ Beneficios cargados exitosamente")
        except Exception as e:
            print(f"✗ Error al esperar los beneficios: {str(e)}")
            print("Los selectores pueden haber cambiado")
            driver.quit()
            return []
        
        # Dar tiempo para que carguen todos los elementos
        print("\nEsperando 5 segundos para asegurar que todos los elementos estén cargados...")
        time.sleep(5)
        
        # Encontrar todos los beneficios
        benefits = []
        seen_titles = set()
        
        print(f"\n=== Extrayendo beneficios ===")
        
        try:
            # Buscar todos los elementos de tarjetas de beneficios
            benefit_elements = driver.find_elements(By.TAG_NAME, "andino-card-general")
            print(f"Encontrados {len(benefit_elements)} elementos de beneficios")
            
            for i, element in enumerate(benefit_elements, 1):
                try:
                    # Obtener el atributo eds-card que contiene el JSON con la información
                    eds_card_attr = element.get_attribute("eds-card")
                    
                    if eds_card_attr:
                        benefit_data = extract_benefit_from_json(eds_card_attr)
                        
                        if benefit_data and benefit_data['title']:
                            title = benefit_data['title']
                            
                            # Evitar duplicados
                            if title not in seen_titles:
                                benefits.append({
                                    'title': title,
                                    'description': benefit_data['description'],
                                    'url': benefit_data['url'],
                                    'category': 'Club Entel'
                                })
                                seen_titles.add(title)
                                print(f"Beneficio {len(benefits)} extraído: {title[:50]}...")
                            else:
                                print(f"Beneficio duplicado omitido: {title[:50]}...")
                    
                except Exception as e:
                    print(f"Error al procesar beneficio {i}: {str(e)}")
                    continue
            
            # También buscar beneficios en el banner principal si existen
            try:
                banner_elements = driver.find_elements(By.CSS_SELECTOR, "eds-card-general")
                print(f"Encontrados {len(banner_elements)} elementos de banner")
                
                for element in banner_elements:
                    try:
                        eds_card_attr = element.get_attribute("eds-card")
                        if eds_card_attr:
                            # El banner puede tener múltiples beneficios en un array
                            json_data = eds_card_attr.replace('&quot;', '"')
                            data = json.loads(json_data)
                            
                            if isinstance(data, list):
                                for item in data:
                                    title = item.get('title', '')
                                    if title and title not in seen_titles:
                                        description = item.get('text', '')
                                        # Limpiar markdown
                                        if description:
                                            description = re.sub(r'\*\*(.*?)\*\*', r'\1', description)
                                        
                                        benefits.append({
                                            'title': title,
                                            'description': description,
                                            'url': item.get('href', ''),
                                            'category': 'Club Entel - Destacados'
                                        })
                                        seen_titles.add(title)
                                        print(f"Beneficio destacado extraído: {title[:50]}...")
                    except Exception as e:
                        print(f"Error al procesar banner: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error al buscar beneficios en banner: {str(e)}")
        
        except Exception as e:
            print(f"✗ Error al buscar beneficios: {str(e)}")
        
        # Cerrar el navegador
        print("\nCerrando navegador...")
        try:
            driver.quit()
            print("✓ Navegador cerrado exitosamente")
        except Exception as e:
            print(f"✗ Error al cerrar el navegador: {str(e)}")
        
        print(f"\n=== RESUMEN ===")
        print(f"Total de beneficios extraídos: {len(benefits)}")
        
        return benefits
        
    except Exception as e:
        print(f"\nError general en el proceso: {str(e)}")
        return []

def main():
    """Función principal"""
    print("Iniciando scraper offline de Entel Club...")
    
    # Hacer scraping
    benefits = scrape_entel_benefits()
    
    if benefits:
        # Guardar en CSV
        success = save_benefits_to_csv(benefits, 'entel/data/benefits_entel.csv')
        
        if success:
            print(f"\n✓ Proceso completado exitosamente!")
            print(f"✓ Total de beneficios: {len(benefits)}")
        else:
            print(f"\n✗ Error al guardar el archivo CSV")
    else:
        print(f"\n✗ No se pudieron extraer beneficios")

if __name__ == "__main__":
    main() 