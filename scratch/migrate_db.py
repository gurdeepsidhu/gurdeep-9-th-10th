import json
import os

def migrate_db():
    base_dir = r"c:\Users\HP\Desktop\gurdeep 9 th 10th"
    db_path = os.path.join(base_dir, 'database.json')
    
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    with open(db_path, 'r') as f:
        old_db = json.load(f)

    # New structure: Class -> Subject -> Topic -> [Questions]
    new_db = {}

    for subject, classes in old_db.items():
        for cls, chapters in classes.items():
            if cls not in new_db:
                new_db[cls] = {}
            if subject not in new_db[cls]:
                new_db[cls][subject] = {}
            
            for chapter, topics in chapters.items():
                for topic, years in topics.items():
                    if topic not in new_db[cls][subject]:
                        new_db[cls][subject][topic] = []
                    
                    for year, difficulties in years.items():
                        for difficulty, q_list in difficulties.items():
                            for q in q_list:
                                # Add metadata to the question object
                                q['year'] = year
                                q['difficulty'] = difficulty
                                q['chapter'] = chapter
                                new_db[cls][subject][topic].append(q)

    # Save the new database
    with open(db_path, 'w') as f:
        json.dump(new_db, f, indent=4)
    print("Migration complete!")

if __name__ == "__main__":
    migrate_db()
