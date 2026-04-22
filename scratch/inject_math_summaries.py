import json
import os

def inject_math_summaries():
    db_file = 'database.json'
    with open(db_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    new_summaries = [
        {
            "type": "Summary",
            "Class": "Class 10",
            "Subject": "Mathematics",
            "Topic": "Introduction to Trigonometry",
            "title": "Introduction to Trigonometry Summary",
            "content": "Trigonometry is the study of relationships between sides and angles of triangles. In Class 10, we focus on right-angled triangles. <ul><li><b>Trigonometric Ratios:</b> $\\sin \\theta = \\frac{O}{H}$, $\\cos \\theta = \\frac{A}{H}$, $\\tan \\theta = \\frac{O}{A}$.</li><li><b>Values:</b> Memorize the table for $0^\\circ, 30^\\circ, 45^\\circ, 60^\\circ, 90^\\circ$.</li><li><b>Identities:</b> The most important one is $\\sin^2 \\theta + \\cos^2 \\theta = 1$.</li></ul>"
        },
        {
            "type": "Summary",
            "Class": "Class 10",
            "Subject": "Mathematics",
            "Topic": "Coordinate Geometry",
            "title": "Coordinate Geometry Summary",
            "content": "Coordinate Geometry allows us to represent points and shapes on a Cartesian plane using $(x, y)$ coordinates. <ul><li><b>Distance Formula:</b> $d = \\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$.</li><li><b>Midpoint:</b> $M = (\\frac{x_1+x_2}{2}, \\frac{y_1+y_2}{2})$.</li><li><b>Section Formula:</b> $P = (\\frac{m_1x_2+m_2x_1}{m_1+m_2}, \\frac{m_1y_2+m_2y_1}{m_1+m_2})$.</li></ul>"
        }
    ]

    # Add only if not already present
    existing_topics = [item.get('Topic') for item in data if item.get('type') == 'Summary']
    for s in new_summaries:
        if s['Topic'] not in existing_topics:
            data.append(s)
            print(f"Added summary for {s['Topic']}")

    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    inject_math_summaries()
