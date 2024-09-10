import json

def load_knowledge_base(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_knowledge_base(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)
    print("Knowledge base updated and saved.")

def add_to_knowledge_base(file_path):
    knowledge_base = load_knowledge_base(file_path)
    
    while True:
        question = input("Enter the question (or press Enter to finish): ")
        if not question:
            break
        
        answer = input("Enter the answer: ")
        
        new_entry = {
            "question": question,
            "answer": answer
        }
        
        knowledge_base.append(new_entry)
        print("Entry added successfully!")
        
        save_now = input("Do you want to save the changes now? (y/n): ").lower()
        if save_now == 'y':
            save_knowledge_base(file_path, knowledge_base)
    
    if input("Do you want to save any unsaved changes? (y/n): ").lower() == 'y':
        save_knowledge_base(file_path, knowledge_base)
    else:
        print("Changes not saved.")

# Usage
file_path = 'knowledge_base.json'  # Replace with your actual file path
add_to_knowledge_base(file_path)