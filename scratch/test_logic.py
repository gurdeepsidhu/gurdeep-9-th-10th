import json

def test_logic():
    with open('database.json', 'r', encoding='utf-8') as f:
        all_qs = json.load(f)
    
    # Simulate user selecting Subject: Physics
    filtered = [q for q in all_qs if q.get('Subject') == "Physics"]
    print(f"Items in Physics: {len(filtered)}")
    
    # Simulate user selecting Topic: Refraction
    topic_filtered = [q for q in filtered if q.get('Topic') == "Refraction"]
    print(f"Items in Refraction: {len(topic_filtered)}")
    
    # Check for summaries in Refraction
    summaries = [i for i in topic_filtered if str(i.get('type', '')).lower() == 'summary']
    print(f"Summaries in Refraction: {len(summaries)}")
    
    # Trace Topic names
    topics = set(i.get('Topic') for i in all_qs)
    print(f"Unique Topics: {topics}")
    
    subjects = set(i.get('Subject') for i in all_qs)
    print(f"Unique Subjects: {subjects}")

if __name__ == '__main__':
    test_logic()
