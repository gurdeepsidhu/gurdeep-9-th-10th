import json

# 1. Reasoning Map Schema
# Organized by: Subject -> Chapter -> Topic -> Year of Exam -> Difficulty Level
reasoning_map = {
    "Mathematics": {
        "Algebra": {
            "Linear Equations in Two Variables": {
                "2023": {
                    "Medium": [
                        {
                            "question_id": "MATH-ALG-LIN-2023-M-001",
                            "question_text": "If 2x + 3y = 12 and x - y = 1, what is the value of x + y?",
                            "options": {
                                "A": "3",
                                "B": "4",
                                "C": "5",
                                "D": "6"
                            },
                            "correct_answer": "C",
                            "explanations": {
                                "basic": "First, find x and y. From the second equation, x = y + 1. Substitute this into the first equation: 2(y + 1) + 3y = 12. This gives 2y + 2 + 3y = 12, so 5y = 10, meaning y = 2. If y = 2, then x = 2 + 1 = 3. Finally, x + y = 3 + 2 = 5.",
                                "advanced": "While substitution works, you can also solve this by noticing patterns or using elimination. Multiply the second equation by 3 to get 3x - 3y = 3. Add this to the first equation (2x + 3y = 12) to immediately eliminate y: (2x+3x) = 15 => 5x = 15 => x = 3. Substitute x=3 into x-y=1 to get y=2. Thus x+y = 5. Mastering elimination saves time on standard tests."
                            }
                        }
                    ]
                }
            }
        }
    },
    "Science": {
        "Physics": {
            "Light - Reflection and Refraction": {
                "2022": {
                    "Hard": [
                        {
                            "question_id": "SCI-PHY-LIG-2022-H-001",
                            "question_text": "An object is placed at a distance of 10 cm from a convex mirror of focal length 15 cm. Find the position and nature of the image.",
                            "options": {
                                "A": "6 cm behind the mirror, virtual and erect",
                                "B": "6 cm in front of the mirror, real and inverted",
                                "C": "30 cm behind the mirror, virtual and erect",
                                "D": "30 cm in front of the mirror, real and inverted"
                            },
                            "correct_answer": "A",
                            "explanations": {
                                "basic": "Use the mirror formula: 1/f = 1/v + 1/u. For a convex mirror, f is positive (+15 cm) and u is always negative (-10 cm). So, 1/v = 1/f - 1/u = 1/15 - (1/-10) = 1/15 + 1/10 = (2+3)/30 = 5/30 = 1/6. Therefore, v = +6 cm. Since v is positive, the image is formed behind the mirror, so it's virtual and erect.",
                                "advanced": "Beyond the formula 1/v + 1/u = 1/f, conceptually, a convex mirror always forms a virtual, erect, and diminished image regardless of object position (unless the object is at infinity, where it forms at the focus). The magnification m = -v/u = -(6)/(-10) = 0.6, confirming it is diminished and erect. Recognizing this property can often allow you to eliminate options B and D immediately without calculation."
                            }
                        }
                    ]
                }
            }
        }
    }
}

# 2. Evaluation Logic
def provide_reasoning_feedback(question_data, student_answer):
    """
    Evaluates the student's answer and provides the appropriate explanation tier.
    
    Logic:
    - Wrong Answer -> Basic explanation to help them understand the fundamental steps.
    - Right Answer -> Advanced insight to deepen their understanding or offer shortcuts.
    """
    is_correct = (student_answer == question_data["correct_answer"])
    
    if is_correct:
        return {
            "status": "Correct",
            "message": "Great job! That's the right answer.",
            "insight_type": "Advanced",
            "feedback": question_data["explanations"]["advanced"]
        }
    else:
        return {
            "status": "Incorrect",
            "message": f"Not quite. The correct answer was {question_data['correct_answer']}.",
            "insight_type": "Basic",
            "feedback": question_data["explanations"]["basic"]
        }

# --- Example Usage ---
if __name__ == "__main__":
    # Fetch a sample question from the map
    sample_question = reasoning_map["Science"]["Physics"]["Light - Reflection and Refraction"]["2022"]["Hard"][0]
    
    print("--- Question ---")
    print(sample_question["question_text"])
    for key, val in sample_question["options"].items():
        print(f"{key}: {val}")
        
    print("\n--- Scenario 1: Student gets it wrong (Answers 'C') ---")
    wrong_feedback = provide_reasoning_feedback(sample_question, "C")
    print(json.dumps(wrong_feedback, indent=2))
    
    print("\n--- Scenario 2: Student gets it right (Answers 'A') ---")
    right_feedback = provide_reasoning_feedback(sample_question, "A")
    print(json.dumps(right_feedback, indent=2))
