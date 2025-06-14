#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug version del scraper BCI para diagnosticar problemas de carga
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_bci_page():
    """Debug de la página de BCI"""
    print("=== DEBUG SCRAPER BCI ===")
    
    # Configurar Chrome (sin headless para ver qué pasa)
    options = Options()
    # options.add_argument('--headless')  # Comentado para debug
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        print("Navegando a BCI...")
        driver.get("https://www.bci.cl/beneficios/beneficios-bci")
        
        print("Esperando 10 segundos para carga inicial...")
        time.sleep(10)
        
        print("Verificando elementos en la página...")
        
        # Verificar si existe #app
        try:
            app = driver.find_element(By.CSS_SELECTOR, "#app")
            print(f"✓ #app encontrado")
        except:
            print("✗ #app NO encontrado")
        
        # Verificar contenedor de beneficios
        try:
            benefits_wrap = driver.find_element(By.CSS_SELECTOR, "div.benefits__wrap")
            print(f"✓ div.benefits__wrap encontrado")
        except:
            print("✗ div.benefits__wrap NO encontrado")
        
        # Verificar tarjetas
        cards = driver.find_elements(By.CSS_SELECTOR, "article.card-benefit-v2")
        print(f"Tarjetas encontradas: {len(cards)}")
        
        # Verificar títulos
        titles = driver.find_elements(By.CSS_SELECTOR, "p.card__title")
        print(f"Títulos encontrados: {len(titles)}")
        
        if titles:
            for i, title in enumerate(titles[:3]):
                text = title.text.strip()
                print(f"  Título {i+1}: '{text}' (longitud: {len(text)})")
        
        # Verificar si hay elementos con clase carrousel__item
        carrousel_items = driver.find_elements(By.CSS_SELECTOR, "div.carrousel__item")
        print(f"Elementos carrousel__item: {len(carrousel_items)}")
        
        # Verificar paginador
        try:
            paginator = driver.find_element(By.CSS_SELECTOR, "div.paginator")
            print("✓ Paginador encontrado")
            
            page_buttons = paginator.find_elements(By.CSS_SELECTOR, "button.paginator__button")
            print(f"  Botones de página: {len(page_buttons)}")
            
            for button in page_buttons[:5]:
                text = button.text.strip()
                if text:
                    print(f"    Botón: '{text}'")
                    
        except:
            print("✗ Paginador NO encontrado")
        
        print("\nEsperando 30 segundos más para ver si carga contenido...")
        time.sleep(30)
        
        # Verificar de nuevo después de esperar
        cards_after = driver.find_elements(By.CSS_SELECTOR, "article.card-benefit-v2")
        titles_after = driver.find_elements(By.CSS_SELECTOR, "p.card__title")
        
        print(f"Después de esperar:")
        print(f"  Tarjetas: {len(cards_after)}")
        print(f"  Títulos: {len(titles_after)}")
        
        if titles_after:
            for i, title in enumerate(titles_after[:3]):
                text = title.text.strip()
                print(f"    Título {i+1}: '{text}'")
        
        input("Presiona Enter para cerrar el navegador...")
        driver.quit()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    debug_bci_page() 