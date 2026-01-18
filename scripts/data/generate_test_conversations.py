"""Generate test conversations for self-learning system"""

import json
from datetime import datetime
from pathlib import Path

# Create logs directory
logs_dir = Path(__file__).resolve().parents[1] / "talk-to-ai" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Test conversation pairs - expanded set for cycle #2
conversations = [
    # AI/ML Fundamentals
    ("What is quantum computing?", "Quantum computing is a type of computation that harnesses quantum mechanical phenomena like superposition and entanglement to process information in ways that classical computers cannot."),
    ("Explain machine learning", "Machine learning is a branch of artificial intelligence where systems learn from data to improve their performance on tasks without being explicitly programmed."),
    ("How do neural networks work?", "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers that process and transform input data to produce outputs."),
    ("What is reinforcement learning?", "Reinforcement learning is a machine learning paradigm where an agent learns to make decisions by interacting with an environment and receiving rewards or penalties for its actions."),
    ("Tell me about transformers", "Transformers are a neural network architecture that uses self-attention mechanisms to process sequential data. They're the foundation of modern language models like GPT and BERT."),
    ("What is deep learning?", "Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to learn hierarchical representations of data."),
    ("Explain gradient descent", "Gradient descent is an optimization algorithm used to minimize a loss function by iteratively moving in the direction of steepest decrease, determined by the negative gradient."),
    ("What are LSTMs?", "LSTMs (Long Short-Term Memory networks) are a type of recurrent neural network designed to learn long-term dependencies by using gates to control information flow."),
    ("What is overfitting?", "Overfitting occurs when a model learns the training data too well, including noise and outliers, resulting in poor generalization to new data."),
    ("Explain backpropagation", "Backpropagation is an algorithm for training neural networks that computes gradients of the loss function with respect to network parameters by applying the chain rule backwards through the network."),
    
    # Advanced ML Concepts
    ("What is transfer learning?", "Transfer learning is a technique where a model trained on one task is reused as the starting point for a different but related task, leveraging previously learned features."),
    ("Explain attention mechanisms", "Attention mechanisms allow models to focus on relevant parts of the input when processing information, dynamically weighting different elements based on their importance."),
    ("What is batch normalization?", "Batch normalization is a technique that normalizes layer inputs across mini-batches to stabilize and accelerate training by reducing internal covariate shift."),
    ("What are GANs?", "GANs (Generative Adversarial Networks) consist of two neural networks—a generator and discriminator—that compete to create realistic synthetic data."),
    ("Explain dropout regularization", "Dropout is a regularization technique that randomly disables neurons during training to prevent overfitting and improve generalization."),
    
    # Quantum Computing
    ("What is superposition?", "Superposition is a quantum property where a qubit can exist in multiple states simultaneously until measured, unlike classical bits that are either 0 or 1."),
    ("Explain quantum entanglement", "Quantum entanglement is a phenomenon where quantum particles become correlated such that the state of one instantaneously affects the state of another, regardless of distance."),
    ("What are quantum gates?", "Quantum gates are the building blocks of quantum circuits that perform operations on qubits, similar to logic gates in classical computing but operating on quantum states."),
    ("What is a qubit?", "A qubit (quantum bit) is the basic unit of quantum information that can exist in superposition of 0 and 1 states, enabling quantum parallelism."),
    ("Explain quantum decoherence", "Quantum decoherence is the loss of quantum properties when a quantum system interacts with its environment, causing it to behave more classically."),
    
    # Python Programming
    ("What are Python decorators?", "Decorators are functions that modify the behavior of other functions or classes, using the @decorator syntax to wrap functionality around existing code."),
    ("Explain list comprehensions", "List comprehensions provide a concise way to create lists in Python using the syntax [expression for item in iterable if condition]."),
    ("What is the GIL?", "The GIL (Global Interpreter Lock) is a mutex in CPython that allows only one thread to execute Python bytecode at a time, affecting multi-threaded performance."),
    ("What are Python generators?", "Generators are functions that use yield to produce a sequence of values lazily, one at a time, without storing the entire sequence in memory."),
    ("Explain async/await in Python", "async/await are keywords for writing asynchronous code in Python, allowing concurrent execution of I/O-bound operations without blocking."),
    
    # Data Structures
    ("What is a hash table?", "A hash table is a data structure that maps keys to values using a hash function, providing average O(1) time complexity for lookups, insertions, and deletions."),
    ("Explain binary search trees", "A binary search tree is a tree data structure where each node has at most two children, and the left subtree contains smaller values while the right contains larger values."),
    ("What are linked lists?", "Linked lists are linear data structures where elements are stored in nodes containing data and a reference to the next node, allowing efficient insertion and deletion."),
    ("What is a heap?", "A heap is a specialized tree-based data structure that satisfies the heap property: parent nodes are either greater than or equal to (max heap) or less than or equal to (min heap) their children."),
    ("Explain graph traversal", "Graph traversal algorithms like BFS (breadth-first search) and DFS (depth-first search) systematically visit all nodes in a graph following different exploration strategies."),
    
    # Software Engineering
    ("What is CI/CD?", "CI/CD (Continuous Integration/Continuous Deployment) is a practice of automating code integration, testing, and deployment to deliver software changes rapidly and reliably."),
    ("Explain microservices architecture", "Microservices architecture structures an application as a collection of loosely coupled, independently deployable services that communicate via APIs."),
    ("What is Docker?", "Docker is a containerization platform that packages applications and their dependencies into isolated containers, ensuring consistency across different environments."),
    ("What is REST API?", "REST (Representational State Transfer) is an architectural style for designing networked applications using HTTP methods and stateless client-server communication."),
    ("Explain version control", "Version control systems like Git track changes to code over time, enabling collaboration, branching, merging, and reverting to previous states."),
    
    # Azure & Cloud
    ("What is Azure Functions?", "Azure Functions is a serverless compute service that runs event-driven code without managing infrastructure, scaling automatically based on demand."),
    ("Explain Azure Quantum", "Azure Quantum is Microsoft's cloud quantum computing platform providing access to quantum hardware, simulators, and development tools."),
    ("What is Cosmos DB?", "Cosmos DB is a globally distributed, multi-model database service offering low-latency access, automatic scaling, and multiple consistency models."),
    ("What are Azure App Services?", "Azure App Services is a PaaS offering for hosting web applications, REST APIs, and mobile backends with built-in scaling and management."),
    ("Explain Azure Storage", "Azure Storage provides scalable cloud storage services including Blob storage (objects), Queue storage (messages), Table storage (NoSQL), and File storage (SMB shares)."),
    
    # LoRA & Fine-Tuning
    ("What is LoRA?", "LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning technique that adds trainable low-rank matrices to frozen pre-trained model weights."),
    ("Explain fine-tuning", "Fine-tuning involves training a pre-trained model on a specific dataset to adapt it to a particular task while leveraging learned general knowledge."),
    ("What is PEFT?", "PEFT (Parameter-Efficient Fine-Tuning) refers to techniques like LoRA that fine-tune models by updating only a small subset of parameters, reducing computational costs."),
    ("What are adapters?", "Adapters are small trainable modules inserted into pre-trained models that enable task-specific adaptation without modifying the original model weights."),
    ("Explain quantization", "Quantization reduces model precision from float32 to lower bit representations (int8, int4) to decrease memory usage and increase inference speed with minimal accuracy loss."),
    
    # General Knowledge
    ("How does encryption work?", "Encryption transforms readable data into encoded format using algorithms and keys, ensuring only authorized parties can decrypt and access the original information."),
    ("What is algorithmic complexity?", "Algorithmic complexity measures the efficiency of algorithms using Big O notation to describe how runtime or space requirements grow with input size."),
    ("Explain caching strategies", "Caching stores frequently accessed data in fast storage layers to reduce latency and computational load, using strategies like LRU, LFU, or time-based expiration."),
    ("What is serverless computing?", "Serverless computing is a cloud model where providers manage infrastructure automatically, executing code in response to events and charging only for actual compute time."),
    ("What are design patterns?", "Design patterns are reusable solutions to common software design problems, categorized into creational, structural, and behavioral patterns."),
]

# Generate log files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"chat_{timestamp}_training_data.jsonl"

print(f"Generating {len(conversations)} conversation pairs...")
print(f"Output: {log_file}")

with open(log_file, "w", encoding="utf-8") as f:
    for user_msg, assistant_msg in conversations:
        # Write user message
        f.write(json.dumps({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now().isoformat(),
            "provider": "lmstudio",
            "model": "local-model"
        }) + "\n")
        
        # Write assistant response
        f.write(json.dumps({
            "role": "assistant",
            "content": assistant_msg,
            "timestamp": datetime.now().isoformat(),
            "provider": "lmstudio",
            "model": "local-model"
        }) + "\n")

print(f"\n✅ Generated {len(conversations)} conversation pairs")
print(f"📁 Saved to: {log_file}")
print("\nNow run the self-learning system to train on these conversations:")
print("  python .\\scripts\\self_learning_chat.py --min-conversations 5")
