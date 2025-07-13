from datasets import load_dataset
from unsloth.chat_templates import standardize_sharegpt
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer

# Load tokenizer from model directory
#tokenizer = AutoTokenizer.from_pretrained("qwen3_lora")

# Load datasets
reasoning_dataset = load_dataset("unsloth/OpenMathReasoning-mini", split="cot")
non_reasoning_dataset = load_dataset("mlabonne/FineTome-100k", split="train")
print(reasoning_dataset[0])

# Convert reasoning dataset
def generate_conversation(examples):
    problems = examples["problem"]
    solutions = examples["generated_solution"]
    conversations = [
        [{"role": "user", "content": p}, {"role": "assistant", "content": s}]
        for p, s in zip(problems, solutions)
    ]
    return {"conversations": conversations}

reasoning_conversations = tokenizer.apply_chat_template(
    reasoning_dataset.map(generate_conversation, batched=True)["conversations"],
    tokenize=False
)

# Convert non-reasoning dataset
dataset = standardize_sharegpt(non_reasoning_dataset)
non_reasoning_conversations = tokenizer.apply_chat_template(
    dataset["conversations"],
    tokenize=False
)

# Mix datasets
chat_percentage = 0.75
non_reasoning_subset = pd.Series(non_reasoning_conversations).sample(
    int(len(reasoning_conversations) * (1.0 - chat_percentage)),
    random_state=2407
)
data = pd.concat([pd.Series(reasoning_conversations), pd.Series(non_reasoning_subset)])
data.name = "text"

combined_dataset = Dataset.from_pandas(pd.DataFrame(data))
combined_dataset = combined_dataset.shuffle(seed=3407)

# Save dataset
combined_dataset.save_to_disk("/app/qwen_llm/training_dataset")
print("Data preparation complete. Saved to training_dataset/")
