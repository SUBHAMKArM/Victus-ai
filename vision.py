"""Victus AI - Vision
Requires: pip install torch torchvision pillow transformers
"""
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"

HAS_VISION = False
image_ai = None


def init_vision():
    """Load vision model. Safe — won't crash if torch missing."""
    global HAS_VISION, image_ai

    try:
        import torch
        print(f"[*] PyTorch {torch.__version__} found.")
    except Exception as e:
        print(f"[!] Vision disabled — PyTorch error: {e}")
        print("[!] Run: pip install torch torchvision torchaudio")
        return

    try:
        from transformers import pipeline as tf_pipeline
        print("[*] Loading vision model (downloads ~1GB first time)...")
        image_ai = tf_pipeline(
            task="image-text-to-text",
            model="Salesforce/blip-image-captioning-base"
        )
        HAS_VISION = True
        print("[+] Vision ready.")
    except Exception as e:
        print(f"[!] Vision failed: {e}")
        print("[!] Try: pip install torch torchvision pillow transformers")


def analyze_image(path):
    if not HAS_VISION or not image_ai:
        return "Vision not available."
    if not os.path.exists(path):
        return f"Image not found: {path}"
    try:
        result = image_ai(images=path, text="Describe this image.")
        return result[0]['generated_text']
    except Exception as e:
        return f"Could not analyze: {e}"


def handle_vision(text):
    if not any(w in text for w in ["analyze image", "scan image", "describe image"]):
        return False, ""
    if not HAS_VISION:
        return True, "Vision not loaded. Install torch and transformers."
    parts = text.replace("analyze image", "").replace("scan image", "").replace("describe image", "").strip()
    if parts and os.path.exists(parts):
        return True, analyze_image(parts)
    return True, "Tell me the image path."
