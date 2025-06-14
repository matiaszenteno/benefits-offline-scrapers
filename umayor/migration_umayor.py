import csv

csv_path = r'C:\Users\theon\Desktop\Scrapper\data\benefits_umayor.csv'
sql_path = r'C:\Users\theon\Desktop\Scrapper\data\benefits_umayor.sql'

with open(csv_path, encoding='utf-8') as csvfile, open(sql_path, 'w', encoding='utf-8') as sqlfile:
    reader = csv.DictReader(csvfile)
    sqlfile.write("INSERT INTO benefits (name, description, category, image_url) VALUES\n")
    rows = []
    for row in reader:
        name = row['title'].replace("'", "''")
        description = row['details'].replace("'", "''")
        category = row['category'].replace("'", "''")
        image_url = row['image_url'].replace("'", "''") if row['image_url'] else ''
        rows.append(f"('{name}', '{description}', '{category}', '{image_url}')")
    sqlfile.write(",\n".join(rows) + ";\n")
print("Script SQL generado en:", sql_path)