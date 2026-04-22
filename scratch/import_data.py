import json
import os

def generate_summary(topic):
    summaries = {
        "The Human Eye and the Colourful World": "<ul><li><b>The Eye:</b> The human eye works like a camera, focusing light onto the retina.</li><li><b>Defects:</b> Myopia (near-sightedness) is corrected with concave lenses; Hypermetropia with convex lenses.</li><li><b>Prisms:</b> White light splits into 7 colors (VIBGYOR) due to dispersion.</li><li><b>Atmospheric Refraction:</b> Causes the twinkling of stars and advanced sunrise.</li></ul>",
        "Magnetic Effects of Electric Current": "<ul><li><b>Magnetic Field:</b> Field lines emerge from North and merge at South.</li><li><b>Electromagnetism:</b> A current-carrying wire produces a magnetic field. A solenoid acts like a bar magnet.</li><li><b>Fleming's Rules:</b> Left-Hand Rule for Motors (Force), Right-Hand Rule for Generators (Induced current).</li><li><b>Domestic Circuits:</b> Live (Red), Neutral (Black), and Earth (Green) wires protect appliances.</li></ul>",
        "Sources of Energy": "<ul><li><b>Renewable vs Non-Renewable:</b> Renewable sources (Solar, Wind, Hydro) can be replenished. Non-renewable (Coal, Petroleum) will run out.</li><li><b>Fossil Fuels:</b> Formed from ancient biomass. Burning them causes pollution and global warming.</li><li><b>Biogas:</b> A clean fuel produced by anaerobic decomposition. Mainly methane.</li><li><b>Solar Energy:</b> Solar cells convert sunlight directly into electricity using silicon.</li></ul>"
    }
    return summaries.get(topic, "")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    input_file = os.path.join(base_dir, 'user_input.json')
    db_file = os.path.join(project_dir, 'database.json')

    with open(input_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    with open(db_file, 'r', encoding='utf-8') as f:
        db_data = json.load(f)

    # Topic mapping to align with existing database topics if necessary
    topic_mapping = {
        "Light - Reflection and Refraction": "Refraction",
        "Electricity": "Electricity"
    }

    # Create lookup maps to avoid duplicates
    # Use (Class, Subject, Topic) as the key
    existing_summaries = set((item.get('Class'), item.get('Subject'), item.get('Topic')) for item in db_data if item.get('type') == 'Summary')
    existing_questions = set(item.get('question_text') for item in db_data if 'question_text' in item)

    # We will append new items
    items_to_add = []

    for chapter in new_data:
        raw_title = chapter.get('chapter_title')
        topic = topic_mapping.get(raw_title, raw_title)
        
        # Subject Mapping for Class 9 and 10
        math_chapters = [
            "Number Systems", "Polynomials", "Coordinate Geometry", "Linear Equations in Two Variables", 
            "Introduction to Euclid’s Geometry", "Lines and Angles", "Triangles", "Quadrilaterals", 
            "Circles", "Heron’s Formula", "Surface Areas and Volumes", "Statistics", "Probability",
            "Real Numbers", "Pair of Linear Equations in Two Variables", "Arithmetic Progressions", 
            "Quadratic Equations", "Some Applications of Trigonometry", "Introduction to Trigonometry", "Areas Related to Circles"
        ]
        chem_chapters = ["Matter in Our Surroundings", "Is Matter Around Us Pure", "Atoms and Molecules", "Structure of the Atom", "Chemical Reactions and Equations", "Acids, Bases and Salts", "Metals and Non-metals", "Carbon and its Compounds", "Periodic Classification of Elements"]
        bio_chapters = ["The Fundamental Unit of Life", "Tissues", "Diversity in Living Organisms", "Why Do We Fall Ill", "Natural Resources", "Improvement in Food Resources", "Life Processes", "Control and Coordination", "How do Organisms Reproduce?", "Heredity and Evolution", "Our Environment", "Sustainable Management of Natural Resources"]
        hist_chapters = ["The French Revolution", "Socialism in Europe and the Russian Revolution", "Nazism and the Rise of Hitler", "Forest Society and Colonialism", "Pastoralists in the Modern World", "The Rise of Nationalism in Europe", "Nationalism in India", "The Making of a Global World", "The Age of Industrialisation", "Print Culture and the Modern World"]
        geo_chapters = ["India – Size and Location", "Physical Features of India", "Drainage", "Climate", "Natural Vegetation and Wildlife", "Population", "Resources and Development", "Forest and Wildlife Resources", "Water Resources", "Agriculture", "Minerals and Energy Resources", "Manufacturing Industries", "Lifelines of National Economy"]
        civics_chapters = ["What is Democracy? Why Democracy?", "Constitutional Design", "Electoral Politics", "Working of Institutions", "Democratic Rights", "Power Sharing", "Federalism", "Gender, Religion and Caste", "Political Parties", "Outcomes of Democracy"]
        econ_chapters = ["The Story of Village Palampur", "People as Resource", "Poverty as a Challenge", "Food Security in India", "Development", "Sectors of the Indian Economy", "Money and Credit", "Globalisation and the Indian Economy", "Consumer Rights"]
        english_chapters = ["The Fun They Had", "The Sound of Music", "The Little Girl", "A Truly Beautiful Mind", "The Snake and the Mirror", "My Childhood", "Reach for the Top", "Kathmandu", "If I were You", "A Letter to God", "Nelson Mandela: Long Walk to Freedom", "Two Stories about Flying", "From the Diary of Anne Frank", "Glimpses of India", "Mijbil the Otter", "Madam Rides the Bus", "The Sermon at Benares", "The Proposal"]
        hindi_chapters = ["Bade Bhai Sahab", "Diary ka ek Panna", "Tantara-Vamiro Katha", "Ab Kahan Dusre ke Dukh se Dukhi Hone Wale", "Patjhad mein Tooti Pattiyan", "Kartoos", "Harihar Kaka", "Sapnon ke se Din", "Topi Shukla"]

        # Determine Class (Simple mapping for now)
        class_9_keywords = ["Number Systems", "Matter in Our Surroundings", "The French Revolution", "India – Size and Location", "What is Democracy?", "The Story of Village Palampur", "The Fun They Had"]
        cls = "Class 9" if any(k in raw_title for k in class_9_keywords) else "Class 10"
        
        # Override if chapter is strictly Class 9
        class_9_chapters = [
            "Number Systems", "Introduction to Euclid’s Geometry", "Lines and Angles", "Quadrilaterals", "Heron’s Formula",
            "Matter in Our Surroundings", "Is Matter Around Us Pure", "Atoms and Molecules", "Structure of the Atom",
            "The Fundamental Unit of Life", "Tissues", "Diversity in Living Organisms", "Why Do We Fall Ill", "Improvement in Food Resources",
            "The French Revolution", "Socialism in Europe and the Russian Revolution", "Nazism and the Rise of Hitler", "Forest Society and Colonialism", "Pastoralists in the Modern World",
            "India – Size and Location", "Physical Features of India", "Drainage", "Climate", "Natural Vegetation and Wildlife", "Population",
            "What is Democracy? Why Democracy?", "Constitutional Design", "Electoral Politics", "Working of Institutions", "Democratic Rights",
            "The Story of Village Palampur", "People as Resource", "Poverty as a Challenge", "Food Security in India"
        ]
        if raw_title in class_9_chapters:
            cls = "Class 9"

        if raw_title in math_chapters:
            subj = "Mathematics"
        elif raw_title in chem_chapters:
            subj = "Chemistry"
        elif raw_title in bio_chapters:
            subj = "Biology"
        elif raw_title in hist_chapters:
            subj = "History"
        elif raw_title in geo_chapters:
            subj = "Geography"
        elif raw_title in civics_chapters:
            subj = "Civics"
        elif raw_title in econ_chapters:
            subj = "Economics"
        elif raw_title in english_chapters:
            subj = "English"
        elif raw_title in hindi_chapters:
            subj = "Hindi"
        else:
            subj = "Science"
        
        # Final override from JSON if provided
        cls = chapter.get('class', cls)

        # Check if we need to add a summary for this topic
        if (cls, subj, topic) not in existing_summaries:
            summary_content = chapter.get('summary', generate_summary(raw_title))
            if summary_content:
                items_to_add.append({
                    "type": "Summary",
                    "Class": cls,
                    "Subject": subj,
                    "Topic": topic,
                    "title": raw_title + " Summary",
                    "content": summary_content
                })
                existing_summaries.add((cls, subj, topic))

        # Add the practice questions
        for idx, q in enumerate(chapter.get('practice_questions', [])):
            q_text = q.get('question')
            if q_text in existing_questions:
                continue
                
            # Convert options array to dict { "A": "Option text", ... }
            options_dict = {}
            for opt in q.get('options', []):
                if ')' in opt:
                    key = opt.split(')')[0].strip()
                    val = opt.split(')')[-1].strip()
                    options_dict[key] = val
                else:
                    # Fallback for simple strings
                    key = chr(65 + q.get('options').index(opt)) # A, B, C...
                    options_dict[key] = opt
            
            # Extract just the letter for correct answer
            correct_letter = q.get('correct_answer', '').split(')')[0].strip()
            
            # Handle both 'explanation' and 'step_by_step_explanation'
            explanation = q.get('step_by_step_explanation', q.get('explanation', ''))

            items_to_add.append({
                "question_id": f"GEN-{topic[:3].upper()}-{idx+1}-{len(db_data)+len(items_to_add)}",
                "question_text": q_text,
                "options": options_dict,
                "correct_answer": correct_letter,
                "explanations": {
                    "basic": explanation,
                    "advanced": "Excellent job! You have a solid grasp of this concept."
                },
                "year": "Standard",
                "difficulty": "Medium",
                "chapter": raw_title,
                "Class": cls,
                "Subject": subj,
                "Topic": topic
            })
            existing_questions.add(q_text)

    # Append to database
    db_data.extend(items_to_add)

    # Save back
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=4)

    print(f"Successfully imported {len(items_to_add)} items (including summaries and questions)!")

if __name__ == '__main__':
    main()
