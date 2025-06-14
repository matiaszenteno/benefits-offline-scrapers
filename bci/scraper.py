#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper offline para BCI Beneficios
Extrae beneficios de BCI y los guarda en un archivo CSV
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import socket


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

def extract_benefit_info(element):
    """Extrae información de un beneficio desde el elemento"""
    try:
        benefit = {}
        
        # Extraer título - múltiples selectores posibles
        title_selectors = ["p.card__title", ".card__title", "h3", "h2"]
        for selector in title_selectors:
            try:
                title_element = element.find_element(By.CSS_SELECTOR, selector)
                benefit['title'] = title_element.text.strip()
                break
            except:
                continue
        
        if not benefit.get('title'):
            benefit['title'] = ''
        
        # Extraer descripción
        desc_selectors = ["p.card__bajada", ".card__bajada", "p"]
        for selector in desc_selectors:
            try:
                desc_element = element.find_element(By.CSS_SELECTOR, selector)
                text = desc_element.text.strip()
                if text and text != benefit.get('title', ''):
                    benefit['description'] = text
                    break
            except:
                continue
        
        if not benefit.get('description'):
            benefit['description'] = ''
        
        # Extraer URL
        try:
            if element.tag_name == 'a':
                benefit['url'] = element.get_attribute('href') or ''
            else:
                link_element = element.find_element(By.TAG_NAME, "a")
                benefit['url'] = link_element.get_attribute('href') or ''
        except:
            benefit['url'] = ''
        
        # Extraer oferta
        offer_selectors = ["p.badge-offer", ".badge-offer", ".badge"]
        for selector in offer_selectors:
            try:
                offer_element = element.find_element(By.CSS_SELECTOR, selector)
                offer_text = offer_element.text.strip()
                
                if 'cashback' in offer_text.lower():
                    benefit['offer_type'] = 'cashback'
                elif 'descuento' in offer_text.lower():
                    benefit['offer_type'] = 'descuento'
                elif 'cuotas' in offer_text.lower():
                    benefit['offer_type'] = 'cuotas'
                else:
                    benefit['offer_type'] = 'otro'
                
                benefit['offer_value'] = offer_text
                break
            except:
                continue
        
        if not benefit.get('offer_type'):
            benefit['offer_type'] = ''
            benefit['offer_value'] = ''
        
        # Extraer método de pago
        payment_selectors = ["span.badge", ".badge-pill"]
        for selector in payment_selectors:
            try:
                payment_element = element.find_element(By.CSS_SELECTOR, selector)
                text = payment_element.text.strip()
                if text and text not in ['cashback', 'descuento']:
                    benefit['payment_method'] = text
                    break
            except:
                continue
        
        if not benefit.get('payment_method'):
            benefit['payment_method'] = ''
        
        # Categorización
        title_lower = benefit['title'].lower()
        desc_lower = benefit['description'].lower()
        
        if any(word in title_lower or word in desc_lower for word in ['restaurant', 'comida', 'burger', 'starbucks', 'coca-cola']):
            benefit['category'] = 'Restaurantes'
        elif any(word in title_lower or word in desc_lower for word in ['salud', 'farmacia', 'salcobrand', 'seguro']):
            benefit['category'] = 'Salud y bienestar'
        elif any(word in title_lower or word in desc_lower for word in ['viaje', 'cuotas sin interés']):
            benefit['category'] = 'Viajes'
        elif any(word in title_lower or word in desc_lower for word in ['deporte', 'adidas', 'fitness']):
            benefit['category'] = 'Deportes'
        elif any(word in title_lower or word in desc_lower for word in ['oxxo', 'tienda', 'supermercado']):
            benefit['category'] = 'Supermercados'
        else:
            benefit['category'] = 'Beneficios BCI'
        
        return benefit
        
    except Exception as e:
        return None

def wait_for_benefits_to_load(driver, timeout=90):
    """Espera a que los beneficios se carguen dinámicamente via JavaScript/XHR"""
    try:
        # Esperar a que la aplicación Vue.js se inicialice
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#app"))
        )
        
        # Estrategia de espera con múltiples selectores
        for attempt in range(18):  # 18 intentos = 90 segundos máximo
            try:
                # Scroll para activar lazy loading
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                
                # Probar múltiples selectores basados en el HTML real
                selectors_to_try = [
                    "article.card-benefit-v2",
                    "div.carrousel__item",
                    "a[id-comercio]"
                ]
                
                for selector in selectors_to_try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 3:
                        # Verificar que tengan contenido real
                        valid_elements = 0
                        for elem in elements[:5]:
                            try:
                                # Buscar texto en diferentes lugares
                                text_found = False
                                for text_selector in ["p.card__title", ".card__title", "h3", "h2", "p"]:
                                    try:
                                        text_elem = elem.find_element(By.CSS_SELECTOR, text_selector)
                                        if text_elem.text.strip() and len(text_elem.text.strip()) > 5:
                                            text_found = True
                                            break
                                    except:
                                        continue
                                
                                if text_found:
                                    valid_elements += 1
                            except:
                                continue
                        
                        if valid_elements >= 3:
                            return True
                
                time.sleep(5)
                
            except:
                time.sleep(5)
        
        return False
        
    except:
        return False

def get_current_page_benefits(driver):
    """Extrae todos los beneficios de la página actual"""
    benefits = []
    
    try:
        # Intentar múltiples selectores basados en el HTML real
        selectors = [
            "article.card-benefit-v2",
            "div.carrousel__item",
            "a[id-comercio]"  # Basado en el HTML que viste
        ]
        
        benefit_elements = []
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                benefit_elements = elements
                break
        
        for element in benefit_elements:
            try:
                benefit = extract_benefit_info(element)
                if benefit and benefit.get('title'):
                    benefits.append(benefit)
            except:
                continue
        
        return benefits
        
    except:
        return []

def get_total_pages(driver):
    """Obtiene el número total de páginas"""
    try:
        paginator = driver.find_element(By.CSS_SELECTOR, "div.paginator")
        page_buttons = paginator.find_elements(By.CSS_SELECTOR, "button.paginator__button")
        
        max_page = 1
        for button in page_buttons:
            try:
                page_text = button.text.strip()
                if page_text.isdigit():
                    max_page = max(max_page, int(page_text))
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
        
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(2)  # Esperar a que inicie la navegación
        
        return True
        
    except:
        return False

def scrape_bci_benefits():
    """Función principal para hacer scraping de beneficios de BCI"""
    try:
        print("=== SCRAPER BCI BENEFICIOS ===")
        
        # Configurar Chrome
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--log-level=3')
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("detach", True)

        # Inicializar navegador
        try:
            service = Service(log_path=os.devnull)
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"Error inicializando navegador: {str(e)}")
            return []

        # Cargar página
        try:
            driver.get("https://www.bci.cl/beneficios/beneficios-bci")
        except Exception as e:
            print(f"Error cargando página: {str(e)}")
            driver.quit()
            return []
        
        # Esperar carga inicial
        if not wait_for_benefits_to_load(driver):
            print("Error: No se cargaron los beneficios")
            driver.quit()
            return []
        
        total_pages = get_total_pages(driver)
        all_benefits = []
        seen_titles = set()
        
        print(f"Procesando {total_pages} páginas...")
        
        for page_num in range(1, total_pages + 1):
            print(f"Página {page_num}/{total_pages}")
            
            if not wait_for_benefits_to_load(driver):
                continue
            
            page_benefits = get_current_page_benefits(driver)
            
            # Filtrar duplicados
            for benefit in page_benefits:
                title = benefit.get('title', '')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_benefits.append(benefit)
            
            # Navegar a siguiente página
            if page_num < total_pages:
                if not go_to_next_page(driver):
                    break
        
        driver.quit()
        print(f"Extraídos {len(all_benefits)} beneficios únicos")
        
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
                
                # Estadísticas por categoría
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