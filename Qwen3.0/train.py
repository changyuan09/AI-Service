from unsloth import FastLanguageModel
from datasets import load_from_disk
from trl import SFTTrainer, SFTConfig
from transformers import AutoTokenizer, DataCollatorForLanguageModeling

# Step 1: Load model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/app/qwen_llm/qwen3_lora",  # Replace with your saved LoRA adapter directory if needed
    max_seq_length=2048,
    load_in_4bit=True,
    load_in_8bit=False,
    full_finetuning=False,
)

# Step 2: Set data collator for causal LM
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False  # Causal LM expects full sequences, no masked tokens
)

# Step 3: Load preprocessed dataset
combined_dataset = load_from_disk("/app/qwen_llm/training_dataset")

# Step 4: Configure trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=combined_dataset,
    eval_dataset=None,  # You can add an evaluation dataset if needed
    data_collator=data_collator,
    args=SFTConfig(
        dataset_text_field="text",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=30,  # Adjust based on your dataset and GPU resources
        learning_rate=2e-4,
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        report_to="none",
    ),
)

# Step 5: Start training
trainer.train()
print("Training complete!")

# Step 6: Save LoRA adapters and tokenizer
trainer.model.save_pretrained("/app/qwen_llm/qwen3_lora_trained")
tokenizer.save_pretrained("/app/qwen_llm/qwen3_lora_trained")
print("LoRA adapters and tokenizer saved to qwen3_lora_trained/")

# Step 7: Save merged model (LoRA + base model) in float16 precision
trainer.model.save_pretrained_merged("/app/qwen_llm/qwen3_lora_merged", tokenizer, save_method="merged_16bit")
print("Merged model and tokenizer saved to qwen3_lora_merged/")
