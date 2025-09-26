"""
Fine-tuning approach for Bookgium AI Assistant

This approach involves training a model specifically on your application data.
"""

import json
from typing import List, Dict

class BookgiumTrainingDataGenerator:
    """Generate training data for fine-tuning"""
    
    def generate_training_examples(self) -> List[Dict]:
        """Generate training examples for accounting Q&A"""
        
        training_data = [
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful accounting assistant for Bookgium."},
                    {"role": "user", "content": "How do I create a journal entry?"},
                    {"role": "assistant", "content": "To create a journal entry in Bookgium: 1. Go to Accounts > Journal Entries, 2. Click 'New Journal Entry', 3. Enter date and description, 4. Add debit and credit lines ensuring they balance, 5. Save the entry. Remember, total debits must equal total credits."}
                ]
            },
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful accounting assistant for Bookgium."},
                    {"role": "user", "content": "What's the difference between assets and liabilities?"},
                    {"role": "assistant", "content": "Assets are resources your business owns (cash, inventory, equipment) that have economic value. Liabilities are debts or obligations your business owes to others (loans, accounts payable). In Bookgium, assets have normal debit balances while liabilities have normal credit balances."}
                ]
            },
            # Add more training examples...
        ]
        
        return training_data
    
    def export_training_data(self, filename: str):
        """Export training data to JSONL format for OpenAI fine-tuning"""
        training_data = self.generate_training_examples()
        
        with open(filename, 'w') as f:
            for example in training_data:
                f.write(json.dumps(example) + '\n')

# Usage:
# generator = BookgiumTrainingDataGenerator()
# generator.export_training_data('bookgium_training.jsonl')
