import csv
import os

def generar_sql_desde_csv(csv_filename):
    dir_script = os.path.dirname(os.path.abspath(__file__))
    ruta_csv = os.path.join(dir_script, csv_filename)
    ruta_sql = os.path.join(dir_script, 'create_and_insert.sql')

    with open(ruta_csv, newline='', encoding='utf-8') as csvfile, open(ruta_sql, 'w', encoding='utf-8') as sqlfile:
        reader = csv.DictReader(csvfile)

        sqlfile.write('DROP TABLE IF EXISTS benefits;\n\n')

        sqlfile.write('''
CREATE TABLE benefits (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    category TEXT,
    provider TEXT,
    location TEXT,
    image_url TEXT
);
'''.strip() + '\n\n')

        for row in reader:
            name = row.get('name', '').replace("'", "''")
            description = row.get('description', '').replace("'", "''")
            category = row.get('category', '').replace("'", "''")
            provider = row.get('provider', '').replace("'", "''")
            location = row.get('location', '').replace("'", "''")
            image_url = row.get('image_url', '').replace("'", "''")

            insert = f"INSERT INTO benefits (name, description, category, provider, location, image_url) VALUES ('{name}', '{description}', '{category}', '{provider}', '{location}', '{image_url}');\n"
            sqlfile.write(insert)

    print(f"Archivo SQL creado en {ruta_sql}")

if __name__ == '__main__':
    generar_sql_desde_csv('benefits.csv')
