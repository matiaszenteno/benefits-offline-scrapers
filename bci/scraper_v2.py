#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper BCI v2 - Basado en la estructura HTML real observada
"""

import csv
import os
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def save_benefits_to_csv(benefits, filename='data/benefits_bci.csv'):
    if not benefits:
        return False
    
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        fieldnames = [
            'id', 'title', 'description', 'bank', 'provider', 'category',
            'is_active', 'created_at', 'updated_at', 'url', 'offer_type',
            'offer_value', 'payment_method'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, benefit in enumerate(benefits, 1):
                row = {
                    'id': i,
                    'title': benefit.get('title', ''),
                    'description': benefit.get('description', ''),
                    'bank': 'bci',
                    'provider': 'Banco de Chile',
                    'category': benefit.get('category', 'Beneficios BCI'),
                    'is_active': 1,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'url': benefit.get('url', ''),
                    'offer_type': benefit.get('offer_type', ''),
                    'offer_value': benefit.get('offer_value', ''),
                    'payment_method': benefit.get('payment_method', '')
                }
                writer.writerow(row)
        
        return True
        
    except Exception as e:
        print(f"Error al guardar CSV: {str(e)}")
        return False

def extract_benefit_from_carrousel_item(item):
    """Extrae beneficio de un div.carrousel__item"""
    try:
        benefit = {}
        
        # Buscar el enlace principal
        try:
            link = item.find_element(By.TAG_NAME, "a")
            benefit['url'] = link.get_attribute('href') or ''
            
            # Buscar dentro del artículo
            article = link.find_element(By.TAG_NAME, "article")
            
            # Título
            try:
                title_elem = article.find_element(By.CSS_SELECTOR, "p.card__title")
                benefit['title'] = title_elem.text.strip()
            except:
                benefit['title'] = ''
            
            # Descripción
            try:
                desc_elems = article.find_elements(By.CSS_SELECTOR, "p.card__bajada")
                descriptions = []
                for desc in desc_elems:
                    text = desc.text.strip()
                    if text and text not in ['Hasta', 'Del', 'Todos los', 'De lunes a viernes']:
                        descriptions.append(text)
                benefit['description'] = ' '.join(descriptions)
            except:
                benefit['description'] = ''
            
            # Oferta
            try:
                offer_elem = article.find_element(By.CSS_SELECTOR, "p.badge-offer")
                offer_text = offer_elem.text.strip()
                
                if 'cashback' in offer_text.lower():
                    benefit['offer_type'] = 'cashback'
                elif 'descuento' in offer_text.lower():
                    benefit['offer_type'] = 'descuento'
                elif 'cuotas' in offer_text.lower():
                    benefit['offer_type'] = 'cuotas'
                else:
                    benefit['offer_type'] = 'otro'
                
                benefit['offer_value'] = offer_text
            except:
                benefit['offer_type'] = ''
                benefit['offer_value'] = ''
            
            # Modalidad de pago
            try:
                badge_elem = article.find_element(By.CSS_SELECTOR, "span.badge")
                benefit['payment_method'] = badge_elem.text.strip()
            except:
                benefit['payment_method'] = ''
            
        except:
            return None
        
        # Categorización
        title_lower = benefit['title'].lower()
        desc_lower = benefit['description'].lower()
        
        if any(word in title_lower or word in desc_lower for word in ['burger', 'starbucks', 'coca-cola', 'restaurant']):
            benefit['category'] = 'Restaurantes'
        elif any(word in title_lower or word in desc_lower for word in ['salcobrand', 'farmacia', 'seguro', 'salud']):
            benefit['category'] = 'Salud y bienestar'
        elif any(word in title_lower or word in desc_lower for word in ['viaje', 'cuotas sin interés']):
            benefit['category'] = 'Viajes'
        elif any(word in title_lower or word in desc_lower for word in ['adidas', 'deporte', 'fitness']):
            benefit['category'] = 'Deportes'
        elif any(word in title_lower or word in desc_lower for word in ['oxxo', 'supermercado', 'tienda']):
            benefit['category'] = 'Supermercados'
        else:
            benefit['category'] = 'Beneficios BCI'
        
        return benefit if benefit.get('title') else None
        
    except:
        return None

def wait_for_dynamic_content(driver, max_attempts=20):
    """Espera a que se cargue el contenido dinámico"""
    print("Esperando contenido dinámico...")
    
    for attempt in range(max_attempts):
        try:
            # Scroll para activar lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            
            # Buscar elementos carrousel__item con contenido
            items = driver.find_elements(By.CSS_SELECTOR, "div.carrousel__item")
            
            if len(items) >= 5:  # Al menos 5 elementos
                # Verificar que tengan contenido real
                valid_items = 0
                for item in items[:8]:
                    try:
                        title_elem = item.find_element(By.CSS_SELECTOR, "p.card__title")
                        if title_elem.text.strip() and len(title_elem.text.strip()) > 10:
                            valid_items += 1
                    except:
                        continue
                
                if valid_items >= 5:
                    print(f"✓ Contenido cargado: {len(items)} elementos, {valid_items} válidos")
                    return True
            
            print(f"Intento {attempt + 1}: {len(items)} elementos encontrados")
            time.sleep(3)
            
        except Exception as e:
            print(f"Error en intento {attempt + 1}: {str(e)}")
            time.sleep(3)
    
    return False

def get_page_benefits(driver):
    """Extrae beneficios de la página actual"""
    benefits = []
    
    try:
        items = driver.find_elements(By.CSS_SELECTOR, "div.carrousel__item")
        print(f"Procesando {len(items)} elementos...")
        
        for i, item in enumerate(items, 1):
            try:
                benefit = extract_benefit_from_carrousel_item(item)
                if benefit:
                    benefits.append(benefit)
                    print(f"  {i}. {benefit['title'][:50]}...")
            except Exception as e:
                print(f"  {i}. Error: {str(e)}")
        
        return benefits
        
    except Exception as e:
        print(f"Error obteniendo beneficios: {str(e)}")
        return []

def get_total_pages(driver):
    """Obtiene número total de páginas"""
    try:
        # Buscar botones de paginación
        page_buttons = driver.find_elements(By.CSS_SELECTOR, "button.paginator__button")
        
        max_page = 1
        for button in page_buttons:
            try:
                text = button.text.strip()
                if text.isdigit():
                    max_page = max(max_page, int(text))
            except:
                continue
        
        return max_page
    except:
        return 1

def go_to_next_page(driver):
    """Navega a la siguiente página"""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "button.paginator__button--right")
        
        if next_button.get_attribute("disabled"):
            return False
        
        # Hacer clic y esperar
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(3)
        
        return True
    except:
        return False

def scrape_bci_benefits():
    """Función principal de scraping"""
    print("=== SCRAPER BCI v2 ===")
    
    # Configurar Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--log-level=3')
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    try:
        service = Service(log_path=os.devnull)
        driver = webdriver.Chrome(service=service, options=options)
        
        print("Cargando página BCI...")
        driver.get("https://www.bci.cl/beneficios/beneficios-bci")
        
        # Esperar a que cargue el contenido dinámico
        if not wait_for_dynamic_content(driver):
            print("Error: No se cargó el contenido dinámico")
            driver.quit()
            return []
        
        # Obtener total de páginas
        total_pages = get_total_pages(driver)
        print(f"Total de páginas: {total_pages}")
        
        all_benefits = []
        seen_titles = set()
        
        # Procesar todas las páginas
        for page_num in range(1, total_pages + 1):
            print(f"\n--- Página {page_num}/{total_pages} ---")
            
            # Esperar a que cargue la página
            if not wait_for_dynamic_content(driver):
                print(f"Error cargando página {page_num}")
                continue
            
            # Extraer beneficios
            page_benefits = get_page_benefits(driver)
            
            # Filtrar duplicados
            new_benefits = 0
            for benefit in page_benefits:
                title = benefit.get('title', '')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_benefits.append(benefit)
                    new_benefits += 1
            
            print(f"Nuevos beneficios únicos: {new_benefits}")
            print(f"Total acumulado: {len(all_benefits)}")
            
            # Navegar a siguiente página
            if page_num < total_pages:
                if not go_to_next_page(driver):
                    print("No se pudo navegar a la siguiente página")
                    break
        
        driver.quit()
        print(f"\n✓ Scraping completado: {len(all_benefits)} beneficios únicos")
        
        return all_benefits
        
    except Exception as e:
        print(f"Error en scraping: {str(e)}")
        try:
            driver.quit()
        except:
            pass
        return []

def main():
    """Función principal"""
    try:
        benefits = scrape_bci_benefits()
        
        if benefits:
            success = save_benefits_to_csv(benefits)
            
            if success:
                print(f"✓ {len(benefits)} beneficios guardados en data/benefits_bci.csv")
                
                # Estadísticas
                categories = {}
                for benefit in benefits:
                    cat = benefit.get('category', 'Sin categoría')
                    categories[cat] = categories.get(cat, 0) + 1
                
                print("\nCategorías:")
                for cat, count in sorted(categories.items()):
                    print(f"  {cat}: {count}")
            else:
                print("Error al guardar beneficios")
        else:
            print("No se extrajeron beneficios")
            
    except KeyboardInterrupt:
        print("\nProceso interrumpido")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 