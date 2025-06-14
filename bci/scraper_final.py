#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper BCI Final - Estrategia agresiva con múltiples fallbacks
"""

import csv
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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

def wait_and_interact(driver, max_wait=120):
    """Estrategia agresiva de espera e interacción"""
    print("Iniciando estrategia agresiva de espera...")
    
    # Esperar a que la página base cargue
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("✓ Página base cargada")
    except:
        print("✗ Error cargando página base")
        return False
    
    # Estrategia de interacción múltiple
    for attempt in range(max_wait // 5):  # Intentos cada 5 segundos
        try:
            print(f"Intento {attempt + 1}...")
            
            # Scroll agresivo
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Simular movimiento del mouse
            try:
                actions = ActionChains(driver)
                actions.move_by_offset(100, 100).perform()
                time.sleep(0.5)
                actions.move_by_offset(-100, -100).perform()
            except:
                pass
            
            # Buscar múltiples tipos de elementos
            selectors_to_check = [
                "div.carrousel__item",
                "article.card-benefit-v2", 
                "a[id-comercio]",
                ".card__title",
                "[class*='card']",
                "[class*='benefit']"
            ]
            
            for selector in selectors_to_check:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✓ Encontrados {len(elements)} elementos con selector: {selector}")
                        
                        # Verificar si tienen contenido
                        elements_with_content = 0
                        for elem in elements[:10]:
                            try:
                                text = elem.text.strip()
                                if text and len(text) > 10:
                                    elements_with_content += 1
                            except:
                                continue
                        
                        if elements_with_content >= 3:
                            print(f"✓ {elements_with_content} elementos con contenido válido")
                            return True
                        else:
                            print(f"Solo {elements_with_content} elementos con contenido")
                except Exception as e:
                    continue
            
            # Intentar hacer clic en elementos que puedan activar contenido
            try:
                clickable_elements = driver.find_elements(By.CSS_SELECTOR, "button, a, [onclick]")
                for elem in clickable_elements[:5]:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            driver.execute_script("arguments[0].click();", elem)
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass
            
            time.sleep(3)
            
        except Exception as e:
            print(f"Error en intento {attempt + 1}: {str(e)}")
            time.sleep(5)
    
    return False

def extract_any_benefit_info(element):
    """Extrae información de cualquier tipo de elemento"""
    try:
        benefit = {}
        
        # Buscar texto en cualquier lugar
        text_content = element.text.strip()
        if not text_content or len(text_content) < 10:
            return None
        
        # Intentar extraer título (primera línea o elemento más prominente)
        title_selectors = [
            "h1", "h2", "h3", "h4", "h5", "h6",
            ".title", ".card__title", "[class*='title']",
            "strong", "b", ".font-weight-bold"
        ]
        
        title_found = False
        for selector in title_selectors:
            try:
                title_elem = element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 5:
                    benefit['title'] = title_text
                    title_found = True
                    break
            except:
                continue
        
        if not title_found:
            # Usar la primera línea del texto como título
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 5 and len(line) < 100:
                    benefit['title'] = line
                    break
        
        if not benefit.get('title'):
            return None
        
        # Descripción (resto del texto)
        title = benefit.get('title', '')
        description_text = text_content.replace(title, '').strip()
        benefit['description'] = description_text[:500] if description_text else ''
        
        # URL
        try:
            if element.tag_name == 'a':
                benefit['url'] = element.get_attribute('href') or ''
            else:
                link = element.find_element(By.TAG_NAME, "a")
                benefit['url'] = link.get_attribute('href') or ''
        except:
            benefit['url'] = ''
        
        # Buscar ofertas en el texto
        text_lower = text_content.lower()
        if 'cashback' in text_lower:
            benefit['offer_type'] = 'cashback'
            # Extraer porcentaje
            import re
            match = re.search(r'(\d+%?\s*cashback)', text_content, re.IGNORECASE)
            if match:
                benefit['offer_value'] = match.group(1)
            else:
                benefit['offer_value'] = 'cashback'
        elif 'descuento' in text_lower:
            benefit['offer_type'] = 'descuento'
            match = re.search(r'(\d+%?\s*descuento)', text_content, re.IGNORECASE)
            if match:
                benefit['offer_value'] = match.group(1)
            else:
                benefit['offer_value'] = 'descuento'
        elif 'cuotas' in text_lower:
            benefit['offer_type'] = 'cuotas'
            benefit['offer_value'] = 'cuotas sin interés'
        else:
            benefit['offer_type'] = ''
            benefit['offer_value'] = ''
        
        # Modalidad
        if 'online' in text_lower:
            benefit['payment_method'] = 'Online'
        elif 'presencial' in text_lower:
            benefit['payment_method'] = 'Presencial'
        else:
            benefit['payment_method'] = ''
        
        # Categorización básica
        title_lower = benefit['title'].lower()
        desc_lower = benefit['description'].lower()
        
        if any(word in title_lower or word in desc_lower for word in ['burger', 'starbucks', 'coca-cola', 'restaurant', 'comida']):
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
        
        return benefit
        
    except:
        return None

def scrape_bci_aggressive():
    """Scraping agresivo de BCI"""
    print("=== SCRAPER BCI AGRESIVO ===")
    
    # Configurar Chrome con opciones menos restrictivas
    options = Options()
    # options.add_argument('--headless')  # Desactivado para debug
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        # Ejecutar script para ocultar webdriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Navegando a BCI...")
        driver.get("https://www.bci.cl/beneficios/beneficios-bci")
        
        # Esperar e interactuar agresivamente
        if not wait_and_interact(driver):
            print("No se pudo cargar contenido dinámico")
            
            # Último intento: buscar cualquier contenido
            print("Buscando cualquier contenido disponible...")
            all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
            print(f"Total de elementos en la página: {len(all_elements)}")
            
            # Buscar elementos con texto
            text_elements = []
            for elem in all_elements:
                try:
                    text = elem.text.strip()
                    if text and len(text) > 20 and len(text) < 1000:
                        text_elements.append(elem)
                except:
                    continue
            
            print(f"Elementos con texto: {len(text_elements)}")
            
            if not text_elements:
                driver.quit()
                return []
        
        # Extraer beneficios de cualquier elemento disponible
        print("Extrayendo beneficios...")
        
        all_selectors = [
            "div.carrousel__item",
            "article.card-benefit-v2",
            "a[id-comercio]",
            "[class*='card']",
            "[class*='benefit']",
            "div[class*='item']",
            "article",
            "section"
        ]
        
        all_benefits = []
        seen_titles = set()
        
        for selector in all_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Procesando {len(elements)} elementos con selector: {selector}")
                
                for elem in elements:
                    try:
                        benefit = extract_any_benefit_info(elem)
                        if benefit and benefit.get('title'):
                            title = benefit['title']
                            if title not in seen_titles and len(title) > 10:
                                seen_titles.add(title)
                                all_benefits.append(benefit)
                                print(f"  ✓ {title[:50]}...")
                    except:
                        continue
                        
                if all_benefits:
                    break  # Si encontramos beneficios, no seguir buscando
                    
            except Exception as e:
                print(f"Error con selector {selector}: {str(e)}")
                continue
        
        input("Presiona Enter para cerrar el navegador...")
        driver.quit()
        
        print(f"Total de beneficios extraídos: {len(all_benefits)}")
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
        benefits = scrape_bci_aggressive()
        
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