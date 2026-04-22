import json
import os

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    db_file = os.path.join(project_dir, 'database.json')

    with open(db_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Subject mapping for Science chapters
    mapping = {
        # Physics
        "Refraction": "Physics",
        "Electricity": "Physics",
        "Magnetic Effects of Electric Current": "Physics",
        "The Human Eye and the Colourful World": "Physics",
        "Sources of Energy": "Physics",
        "Light - Reflection and Refraction": "Physics",
        
        # Chemistry
        "Acids, Bases and Salts": "Chemistry",
        "Chemical Reactions and Equations": "Chemistry",
        "Metals and Non-metals": "Chemistry",
        "Carbon and its Compounds": "Chemistry",
        "Periodic Classification of Elements": "Chemistry",
        
        # Biology
        "Life Processes": "Biology",
        "Control and Coordination": "Biology",
        "How do Organisms Reproduce?": "Biology",
        "Heredity and Evolution": "Biology",
        "Our Environment": "Biology",
        "Management of Natural Resources": "Biology"
    }

    count = 0
    for item in data:
        topic = item.get('Topic')
        if topic in mapping:
            item['Subject'] = mapping[topic]
            count += 1
        # Also check chapter field for questions
        chapter = item.get('chapter')
        if chapter in mapping:
            item['Subject'] = mapping[chapter]

    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    print(f"Successfully updated Subject for {count} items in database.json!")

if __name__ == '__main__':
    main()
