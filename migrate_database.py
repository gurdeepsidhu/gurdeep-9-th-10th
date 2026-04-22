import json
import os

def flatten_database():
    db_path = 'database.json'
    backup_path = 'database_backup.json'
    
    if not os.path.exists(db_path):
        print("Error: database.json not found.")
        return

    # Create a backup just in case
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4)
    print(f"Backup created at {backup_path}")

    flat_questions = []

    def recursive_flatten(data, path_dict):
        if isinstance(data, list):
            for q in data:
                flat_q = q.copy()
                # Ensure path tags are present
                flat_q.update(path_dict)
                # Ensure 'Topic' is a clean string if it's nested
                if 'Topic' not in flat_q:
                    flat_q['Topic'] = path_dict.get('Topic', 'General')
                flat_questions.append(flat_q)
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = path_dict.copy()
                depth = len(path_dict)
                if depth == 0: new_path['Class'] = key
                elif depth == 1: new_path['Subject'] = key
                elif depth == 2: new_path['Topic'] = key
                else: new_path['Topic'] = f"{path_dict['Topic']} > {key}"
                recursive_flatten(value, new_path)

    recursive_flatten(db, {})
    
    # Save the new flat database
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(flat_questions, f, indent=4)
    
    print(f"Successfully flattened {len(flat_questions)} questions into database.json")

if __name__ == "__main__":
    flatten_database()
