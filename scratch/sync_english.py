import json
import os

def sync_english():
    db_file = 'database.json'
    with open(db_file, 'r', encoding='utf-8') as f:
        db_data = json.load(f)

    english_content = [
        # POEMS
        {
            "chapter_title": "Dust of Snow",
            "summary": "A short poem by Robert Frost that illustrates how a small natural event can change one's mood. <ul><li><b>The Incident:</b> A crow shakes down dust of snow from a hemlock tree on the poet.</li><li><b>The Impact:</b> This simple act saves the rest of the poet's day from being wasted in regret.</li><li><b>Symbolism:</b> Hemlock (poisonous) and Crow (bad omen) are used to bring positivity.</li></ul>",
            "questions": [{"q": "Who is the poet of 'Dust of Snow'?", "opts": ["A) Robert Frost", "B) John Berryman", "C) Leslie Norris", "D) Walt Whitman"], "ans": "A", "exp": "Robert Frost is the famous American poet known for this poem."}]
        },
        {
            "chapter_title": "Fire and Ice",
            "summary": "A poem about the end of the world. <ul><li><b>Fire:</b> Represents desire and passion.</li><li><b>Ice:</b> Represents hatred and coldness.</li><li><b>Conclusion:</b> Both are equally powerful and capable of destroying the world.</li></ul>",
            "questions": [{"q": "What does 'Ice' symbolize in the poem?", "opts": ["A) Love", "B) Hatred", "C) Desire", "D) Peace"], "ans": "B", "exp": "Ice represents the cold, calculating nature of hatred."}]
        },
        # FOOTPRINTS WITHOUT FEET
        {
            "chapter_title": "A Triumph of Surgery",
            "summary": "Tricky, a small dog, is pampered by his rich mistress Mrs. Pumphrey. <ul><li><b>The Problem:</b> Tricky becomes hugely fat and listless due to overeating.</li><li><b>The Cure:</b> Mr. Herriot (the vet) takes him to the surgery and gives him no food, only water and exercise.</li><li><b>Outcome:</b> Tricky recovers completely, which Mrs. Pumphrey calls a 'triumph of surgery'.</li></ul>",
            "questions": [{"q": "Who was Tricky?", "opts": ["A) A cat", "B) A dog", "C) A vet", "D) A servant"], "ans": "B", "exp": "Tricky was the pampered pet dog of Mrs. Pumphrey."}]
        },
        {
            "chapter_title": "The Thief's Story",
            "summary": "A 15-year-old thief (Hari Singh) befriends a kind writer named Anil. <ul><li><b>The Trust:</b> Anil teaches Hari to read, write, and cook.</li><li><b>The Theft:</b> Hari steals Anil's money but returns it because he realizes the value of education and Anil's trust.</li><li><b>Transformation:</b> Hari decides to leave his criminal life for a better future.</li></ul>",
            "questions": [{"q": "What was Anil's profession?", "opts": ["A) Doctor", "B) Lawyer", "C) Writer", "D) Teacher"], "ans": "C", "exp": "Anil wrote for magazines to make a living."}]
        },
        {
            "chapter_title": "The Necklace",
            "summary": "Matilda Loisel, a pretty but dissatisfied woman, borrows a diamond necklace for a ball. <ul><li><b>The Loss:</b> She loses the necklace and spends 10 years in poverty to replace it.</li><li><b>The Irony:</b> She later discovers that the original necklace was fake (cost only 500 francs).</li></ul>",
            "questions": [{"q": "How many years did the Loisels spend repaying the debt?", "opts": ["A) 5 years", "B) 10 years", "C) 20 years", "D) 1 year"], "ans": "B", "exp": "They spent 10 long years of hard labor and poverty to pay off the 36,000 francs."}]
        },
        {
            "chapter_title": "Bholi",
            "summary": "The story of Sulekha (Bholi), who is neglected due to her looks and stammering. <ul><li><b>The Teacher:</b> Her school teacher encourages her and gives her confidence.</li><li><b>The Decision:</b> Bholi refuses to marry Bishamber (a greedy lame man) and decides to serve her parents and teach in the school.</li></ul>",
            "questions": [{"q": "What was Bholi's real name?", "opts": ["A) Sulekha", "B) Sunaina", "C) Sukanya", "D) Surekha"], "ans": "A", "exp": "Bholi was called so because she was considered a simpleton, but her real name was Sulekha."}]
        }
    ]

    existing_topics = set(item.get('Topic') for item in db_data if item.get('Subject') == 'English')
    items_to_add = []

    for entry in english_content:
        topic = entry["chapter_title"]
        if topic not in existing_topics:
            # Add Summary
            items_to_add.append({
                "type": "Summary",
                "Class": "Class 10",
                "Subject": "English",
                "Topic": topic,
                "title": topic + " Summary",
                "content": entry["summary"]
            })
            # Add Questions
            for idx, q in enumerate(entry["questions"]):
                opts_dict = {}
                for o in q["opts"]:
                    key = o.split(')')[0].strip()
                    val = o.split(')')[-1].strip()
                    opts_dict[key] = val
                
                items_to_add.append({
                    "question_id": f"ENG-{topic[:3].upper()}-{idx+1}",
                    "question_text": q["q"],
                    "options": opts_dict,
                    "correct_answer": q["ans"],
                    "explanations": {"basic": q["exp"]},
                    "Class": "Class 10",
                    "Subject": "English",
                    "Topic": topic
                })
            print(f"Adding English: {topic}")

    if items_to_add:
        db_data.extend(items_to_add)
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=4)
        print(f"English Sync Complete! Added {len(items_to_add)} items.")
    else:
        print("English is already in sync!")

if __name__ == '__main__':
    sync_english()
