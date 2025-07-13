# inference_out.py
from unsloth import FastLanguageModel
from transformers import TextStreamer
import torch
import yaml

print("[DEBUG] Loading model once at module level...")

# Load config from YAML once
with open("/app/Configs/Config_qwen.yaml", "r") as f:
    config = yaml.safe_load(f)


print("[DEBUG] Loaded config:", config)

_model = None
_tokenizer = None
_model_device = None

def load_model_once():
    global _model, _tokenizer, _model_device
    if _model is None:
        model_dir = "/app/qwen_llm/qwen3_lora_merged"
        _model, _tokenizer = FastLanguageModel.from_pretrained(
            model_dir,
            max_seq_length=config["max_seq_length"],
            load_in_4bit=config["load_in_4bit"],
            load_in_8bit=config["load_in_8bit"],
            full_finetuning=False,
        )
        _model_device = next(_model.parameters()).device
        print(f"[DEBUG] Model loaded to device: {_model_device}")
        
def run_inference(question):
    load_model_once()

    messages = [{"role": "user", "content": question}]
    text = _tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=config["enable_thinking"],
    )

    inputs = _tokenizer(text, return_tensors="pt").to(_model_device)

    output = _model.generate(
        **inputs,
        max_new_tokens=config["max_new_tokens"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        top_k=config["top_k"],
        pad_token_id=_tokenizer.eos_token_id
    )

    response_text = _tokenizer.decode(output[0], skip_special_tokens=True)
    print("[DEBUG] response_test generated successfully")
    
    return response_text.strip()
