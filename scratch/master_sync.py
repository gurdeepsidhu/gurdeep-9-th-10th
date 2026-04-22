import json
import os

def master_sync():
    db_file = 'database.json'
    with open(db_file, 'r', encoding='utf-8') as f:
        db_data = json.load(f)

    # Dictionary of ALL chapters we want to ensure are in the database
    # Subject -> Chapter Name -> { summary: str, questions: list }
    all_content = {
        "Mathematics": {
            "Real Numbers": {
                "summary": "Real Numbers include rational and irrational numbers. <ul><li><b>HCF/LCM:</b> $HCF(a, b) \\times LCM(a, b) = a \\times b$.</li><li><b>Fundamental Theorem of Arithmetic:</b> Every composite number is a product of primes.</li></ul>",
                "questions": [
                    {"q": "HCF of 95 and 152 is:", "opts": ["A) 1", "B) 19", "C) 38", "D) 57"], "ans": "B", "exp": "Factorize: $95=5 \\times 19$, $152=2^3 \\times 19$. Common factor is 19."}
                ]
            },
            "Polynomials": {
                "summary": "Study of zeroes and coefficients. <ul><li><b>Sum of zeroes:</b> $-b/a$.</li><li><b>Product of zeroes:</b> $c/a$.</li></ul>",
                "questions": [
                    {"q": "Zeroes of $x^2-2x-8$ are:", "opts": ["A) 2,-4", "B) 4,-2", "C) -2,-2", "D) 4,4"], "ans": "B", "exp": "Factor: $(x-4)(x+2)=0 \\implies x=4, -2$."}
                ]
            },
            "Pair of Linear Equations in Two Variables": {
                "summary": "Systems of two equations. <ul><li><b>Unique:</b> $a_1/a_2 \\neq b_1/b_2$.</li><li><b>Infinite:</b> $a_1/a_2 = b_1/b_2 = c_1/c_2$.</li><li><b>None:</b> $a_1/a_2 = b_1/b_2 \\neq c_1/c_2$.</li></ul>",
                "questions": [
                    {"q": "If lines are parallel, the system has:", "opts": ["A) 1 solution", "B) 2 solutions", "C) Infinite", "D) No solution"], "ans": "D", "exp": "Parallel lines never intersect."}
                ]
            },
            "Arithmetic Progressions": {
                "summary": "Sequences with constant difference. <ul><li><b>$n^{th}$ term:</b> $a + (n-1)d$.</li><li><b>Sum:</b> $\\frac{n}{2}(2a + (n-1)d)$.</li></ul>",
                "questions": [
                    {"q": "In AP: 10, 7, 4... the $30^{th}$ term is:", "opts": ["A) 97", "B) 77", "C) -77", "D) -87"], "ans": "C", "exp": "$a=10, d=-3$. $a_{30}=10+29(-3)=10-87=-77$."}
                ]
            },
            "Triangles": {
                "summary": "Similarity and Pythagoras. <ul><li><b>BPT:</b> Ratio of sides is equal for parallel line.</li><li><b>Similarity:</b> AA, SSS, SAS.</li></ul>",
                "questions": [
                    {"q": "Ratio of areas of similar triangles is:", "opts": ["A) Ratio of sides", "B) Square of ratio of sides", "C) Cube of ratio", "D) None"], "ans": "B", "exp": "Theorem: Area ratio = $(\\text{side ratio})^2$."}
                ]
            },
            "Introduction to Trigonometry": {
                "summary": "Ratios and identities. <ul><li>$\\sin^2 \\theta + \\cos^2 \\theta = 1$.</li><li>$\\tan \\theta = \\sin / \\cos$.</li></ul>",
                "questions": [
                    {"q": "Value of $\\cos 0^\\circ$ is:", "opts": ["A) 0", "B) 1", "C) 1/2", "D) Not defined"], "ans": "B", "exp": "From trig table, $\\cos 0 = 1$."}
                ]
            },
            "Coordinate Geometry": {
                "summary": "Points on a plane. <ul><li><b>Distance:</b> $\\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$.</li><li><b>Midpoint:</b> $(x_1+x_2)/2, (y_1+y_2)/2$.</li></ul>",
                "questions": [
                    {"q": "Distance of (3,4) from origin is:", "opts": ["A) 3", "B) 4", "C) 5", "D) 7"], "ans": "C", "exp": "$\\sqrt{3^2+4^2}=5$."}
                ]
            },
            "Quadratic Equations": {
                "summary": "Standard form $ax^2+bx+c=0$. <ul><li><b>Roots:</b> $\\frac{-b \\pm \\sqrt{D}}{2a}$.</li><li><b>D:</b> $b^2-4ac$.</li></ul>",
                "questions": [
                    {"q": "If $D=0$, roots are:", "opts": ["A) Real & Equal", "B) Real & Distinct", "C) Imaginary", "D) None"], "ans": "A", "exp": "When discriminant is zero, roots are identical."}
                ]
            },
            "Some Applications of Trigonometry": {
                "summary": "Heights and distances using angles of elevation and depression.",
                "questions": [
                    {"q": "If tower height = shadow length, sun's angle is:", "opts": ["A) $30^\\circ$", "B) $45^\\circ$", "C) $60^\\circ$", "D) $90^\\circ$"], "ans": "B", "exp": "$\\tan \\theta = h/h = 1 \\implies \\theta = 45^\\circ$."}
                ]
            },
            "Circles": {
                "summary": "Tangents and radii properties. Tangent is perpendicular to radius.",
                "questions": [
                    {"q": "Max tangents from external point is:", "opts": ["A) 1", "B) 2", "C) 3", "D) Infinite"], "ans": "B", "exp": "Only two tangents can be drawn from a single point outside."}
                ]
            },
            "Areas Related to Circles": {
                "summary": "Sector and segment areas. <ul><li><b>Sector:</b> $(\\theta/360) \\pi r^2$.</li></ul>",
                "questions": [
                    {"q": "Area of circle with radius 7 is:", "opts": ["A) 44", "B) 154", "C) 49", "D) 98"], "ans": "B", "exp": "$\\pi r^2 = (22/7) \\times 49 = 154$."}
                ]
            },
            "Surface Areas and Volumes": {
                "summary": "3D shapes formulas for Cube, Cone, Sphere, etc.",
                "questions": [
                    {"q": "Volume of sphere with radius $r$ is:", "opts": ["A) $\\pi r^2$", "B) $4\\pi r^2$", "C) $\\frac{4}{3}\\pi r^3$", "D) $2\\pi r$"], "ans": "C", "exp": "Standard volume formula for a sphere."}
                ]
            },
            "Statistics": {
                "summary": "Mean, Median, Mode. <ul><li>$3 \\text{ Median} = \\text{Mode} + 2 \\text{ Mean}$.</li></ul>",
                "questions": [
                    {"q": "Midpoint of class 10-20 is:", "opts": ["A) 10", "B) 15", "C) 20", "D) 5"], "ans": "B", "exp": "$(10+20)/2 = 15$."}
                ]
            },
            "Probability": {
                "summary": "Likelihood of events. $0 \\le P(E) \\le 1$.",
                "questions": [
                    {"q": "Prob of sure event is:", "opts": ["A) 0", "B) 1", "C) 0.5", "D) -1"], "ans": "B", "exp": "A certain event has probability 1."}
                ]
            }
        },
        "Chemistry": {
            "Chemical Reactions and Equations": {
                "summary": "Balancing equations and reaction types.",
                "questions": [
                    {"q": "Which is a decomposition reaction?", "opts": ["A) $A+B \\to AB$", "B) $AB \\to A+B$", "C) $A+BC \\to AC+B$", "D) None"], "ans": "B", "exp": "One reactant breaking into many."}
                ]
            },
            "Acids, Bases and Salts": {
                "summary": "pH, litmus, and salt properties.",
                "questions": [
                    {"q": "pH of neutral solution is:", "opts": ["A) 0", "B) 7", "C) 14", "D) 1"], "ans": "B", "exp": "Neutral water has pH 7."}
                ]
            },
            "Metals and Non-metals": {
                "summary": "Reactivity and extraction of metals.",
                "questions": [
                    {"q": "Only liquid metal at room temp:", "opts": ["A) Na", "B) Hg", "C) Al", "D) Fe"], "ans": "B", "exp": "Mercury is liquid."}
                ]
            },
            "Carbon and its Compounds": {
                "summary": "Covalent bonding and hydrocarbons.",
                "questions": [
                    {"q": "Functional group of alcohol is:", "opts": ["A) -CHO", "B) -OH", "C) -COOH", "D) -Cl"], "ans": "B", "exp": "-OH represents alcohols."}
                ]
            },
            "Periodic Classification of Elements": {
                "summary": "Modern periodic table trends.",
                "questions": [
                    {"q": "Atomic size across a period:", "opts": ["A) Increases", "B) Decreases", "C) Constant", "D) Random"], "ans": "B", "exp": "Nuclear charge pulls electrons closer."}
                ]
            }
        },
        "Biology": {
            "Life Processes": {
                "summary": "Nutrition, Respiration, Circulation, Excretion.",
                "questions": [
                    {"q": "Photosynthesis occurs in:", "opts": ["A) Mitochondria", "B) Chloroplast", "C) Nucleus", "D) Ribosome"], "ans": "B", "exp": "Chloroplasts contain chlorophyll for light trapping."}
                ]
            },
            "Control and Coordination": {
                "summary": "Nervous and Hormonal systems.",
                "questions": [
                    {"q": "Gap between neurons is:", "opts": ["A) Axon", "B) Synapse", "C) Dendrite", "D) Cell body"], "ans": "B", "exp": "Synapse is the chemical junction."}
                ]
            }
        }
    }

    # Track existing topics to avoid duplicates
    existing_summaries = set(item.get('Topic') for item in db_data if item.get('type') == 'Summary')
    existing_questions = set(item.get('Topic') for item in db_data if 'question_text' in item)

    items_to_add = []

    for subj, chapters in all_content.items():
        for topic, content in chapters.items():
            # Add Summary if missing
            if topic not in existing_summaries:
                items_to_add.append({
                    "type": "Summary",
                    "Class": "Class 10",
                    "Subject": subj,
                    "Topic": topic,
                    "title": topic + " Summary",
                    "content": content["summary"]
                })
                existing_summaries.add(topic)
                print(f"Adding Summary: {subj} -> {topic}")

            # Add Questions if missing
            if topic not in existing_questions:
                for idx, q in enumerate(content["questions"]):
                    # Parse options
                    opts_dict = {}
                    for o in q["opts"]:
                        key = o.split(')')[0].strip()
                        val = o.split(')')[-1].strip()
                        opts_dict[key] = val
                    
                    items_to_add.append({
                        "question_id": f"SYNC-{topic[:3].upper()}-{idx+1}",
                        "question_text": q["q"],
                        "options": opts_dict,
                        "correct_answer": q["ans"],
                        "explanations": {
                            "basic": q["exp"],
                            "advanced": "Excellent job! You are mastering this topic."
                        },
                        "year": "Standard",
                        "difficulty": "Medium",
                        "chapter": topic,
                        "Class": "Class 10",
                        "Subject": subj,
                        "Topic": topic
                    })
                existing_questions.add(topic)
                print(f"Adding Questions: {subj} -> {topic}")

    if items_to_add:
        db_data.extend(items_to_add)
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=4)
        print(f"Master Sync Complete! Added {len(items_to_add)} items.")
    else:
        print("Everything is already in sync!")

if __name__ == '__main__':
    master_sync()
