from database import connect, init_db

init_db()
conn = connect()
cursor = conn.cursor()

topics_data = {
    "DEFINITION OF ARTIFICIAL INTELLIGENCE": [
        "What is Artificial Intelligence?", "Why AI is needed", "Human vs. machine intelligence", "Goals of AI", "Real-life applications of AI"
    ],
    "ARTIFICIAL INTELLIGENCE - A PART OF COMPUTER SCIENCE": [
        "Relationship between AI and computer science", "AI as an interdisciplinary field", "Areas of CS used in AI", "Challenges in defining AI as a CS subfield"
    ],
    "A STATE SPACE GRAPH - A FORMAL REPRESENTATION OF PROBLEM-SOLVING PROCESS": [
        "What is a state space?", "State, initial state, goal state", "Operators and state transitions", "Graphical structure", "Example-based illustration"
    ],
    "A GAME TREE - AN APPLICATION OF A STATE SPACE GRAPH": [
        "What is a game tree?", "Two-player perfect information games", "Game tree vs state space", "Turn-taking and node levels", "Subtraction game example"
    ],
    "STATE SPACE SEARCH": [
        "Search as problem-solving", "Start, goal, path", "Open vs closed nodes", "Forward vs backward search", "Backtracking and loop avoidance"
    ],
    "UNINFORMED SEARCH ALGORITHMS": [
        "Breadth-First Search", "Depth-First Search", "Depth-Limited Search", "Bidirectional Search"
    ],
    "HEURISTIC SEARCH AND COMPLEXITY OF A STATE SPACE GRAPH": [
        "What is a heuristic function?", "Complexity of state spaces", "Heuristic vs uninformed search", "When heuristics help", "Design implications"
    ],
    "HEURISTIC SEARCH ALGORITHMS": [
        "Hill Climbing", "Best-First Search", "Beam Search", "A* Algorithm", "Comparison and limitations"
    ],
    "HEURISTIC SEARCH ALGORITHMS FOR TWO-PERSON GAMES WITH PERFECT INFORMATION": [
        "What are two-person games?", "Game strategies", "Minimax Algorithm", "Alpha-Beta Pruning", "Game tree optimization"
    ],
    "THE CONCEPT OF MACHINE LEARNING": [
        "What is Machine Learning?", "ML vs traditional programming", "Types of learning", "Robot learning example", "Data and learning environment"
    ],
    "ALGORITHMS OF SUPERVISED MACHINE LEARNING": [
        "Linear Regression", "Decision Trees", "Support Vector Machines", "k-NN", "Logistic Regression", "Naive Bayes"
    ],
    "ALGORITHMS OF UNSUPERVISED MACHINE LEARNING": [
        "What is clustering?", "K-Means", "Hierarchical clustering", "Association rule mining", "PCA"
    ],
    "MACHINE LEARNING PERFORMANCE EVALUATION METRICS": [
        "Accuracy", "Precision", "Recall", "F1 Score", "Confusion Matrix", "ROC Curve and AUC"
    ],
    "BASICS OF ARTIFICIAL NEURAL NETWORKS": [
        "What is ANN?", "Biological inspiration", "Perceptron", "Multilayer Perceptron", "Forward/Backward propagation", "Activation functions"
    ],
    "KNOWLEDGE REPRESENTATION AND NETWORKED REPRESENTATION": [
        "Importance of knowledge", "Declarative vs procedural", "Semantic networks", "Networked representation", "Linked data"
    ],
    "STRUCTURED KNOWLEDGE REPRESENTATION SCHEMES": [
        "Frame-based systems", "Slot-filler structures", "Ontologies", "Taxonomies", "Object-based representation"
    ],
    "PROCEDURAL KNOWLEDGE REPRESENTATION SCHEMES": [
        "What is procedural knowledge?", "Production rules", "Scripts", "Rule chaining", "Rule-based systems"
    ]
}

cursor.execute("DELETE FROM topics")
cursor.execute("DELETE FROM subtopics")

for topic_title, subtopics in topics_data.items():
    cursor.execute("INSERT INTO topics (title) VALUES (%s) RETURNING id", (topic_title,))
    topic_id = cursor.fetchone()[0]
    for sub in subtopics:
        cursor.execute("INSERT INTO subtopics (topic_id, title) VALUES (%s, %s)", (topic_id, sub))


conn.commit()
conn.close()
print("PostgreSQL populated with AI course topics and subtopics.")
