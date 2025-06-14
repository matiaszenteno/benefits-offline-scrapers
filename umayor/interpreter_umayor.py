import re
from bs4 import BeautifulSoup
import json
import csv
import os

def clean_html_file():
    # Read the input file
    with open('umayor.txt', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Parse HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all benefit cards
    benefits = []
    
    # Look for cards that have a modal target
    benefit_cards = soup.find_all('a', class_='card', attrs={'data-target': re.compile(r'modalBeneficios\d+')})
    
    for card in benefit_cards:
        benefit = {}
        
        # Get the modal target ID
        modal_id = card.get('data-target', '').replace('#', '')
        benefit['id'] = modal_id
        
        # Get title from card
        title_elem = card.find('h4')
        if title_elem:
            benefit['title'] = title_elem.get_text(strip=True)
        
        # Get date from card
        date_elem = card.find('small')
        if date_elem:
            benefit['date'] = date_elem.get_text(strip=True)
        
        # Try to find the modal content
        modal = soup.find('div', id=modal_id)
        if modal:
            # Get category
            cat_elem = modal.find('p', class_='catBeneficios')
            if cat_elem:
                benefit['category'] = cat_elem.get_text(strip=True)
            
            # Get details
            details_elem = modal.find('p', class_='boxCuerpo')
            if details_elem:
                benefit['details'] = details_elem.get_text(strip=True)
            
            # Get image URL
            img_elem = modal.find('img')
            if img_elem and img_elem.get('src'):
                benefit['image_url'] = img_elem['src']
        
        if benefit:  # Only add if we found some data
            benefits.append(benefit)
    
    # Save cleaned data to JSON file
    with open('benefits_clean.json', 'w', encoding='utf-8') as f:
        json.dump(benefits, f, ensure_ascii=False, indent=2)
    
    # Save cleaned data to CSV file
    if benefits:
        keys = ['id', 'title', 'date', 'category', 'details', 'image_url']
        csv_path = os.path.join('data', 'benefits_umayor.csv')
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(benefits)
    
    print(f"Found {len(benefits)} benefits. Data saved to benefits_clean.json and {csv_path}")

if __name__ == "__main__":
    clean_html_file() 