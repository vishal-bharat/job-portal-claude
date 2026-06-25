# Fine-tune GISMABert on Google Colab.
#
# How to use:
#   1. Go to https://colab.research.google.com
#   2. Runtime -> Change runtime type -> T4 GPU -> Save
#   3. Upload data/training_pairs.json via the Files panel
#   4. Paste this file into a Colab cell and run it
#   5. Download the 'gismabert' folder from the Files panel
#   6. Place it at: python-backend/gismabert/
#
# Expected time: 20-35 minutes on free Colab T4 GPU.

# Install dependencies
# !pip install sentence-transformers -q

import json
import random
from torch.utils.data import DataLoader
from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses,
    evaluation,
)

# 1. Load training data
print("Loading training pairs...")
with open("training_pairs.json", encoding="utf-8") as f:
    all_pairs = json.load(f)

train_raw = [p for p in all_pairs if p["split"] == "train"]
eval_raw  = [p for p in all_pairs if p["split"] == "eval"]

print(f"   Train: {len(train_raw)} pairs")
print(f"   Eval:  {len(eval_raw)} pairs")

# 2. Build InputExamples
random.shuffle(train_raw)

train_examples = [
    InputExample(
        texts=[p["text_a"], p["text_b"]],
        label=float(p["label"]),
    )
    for p in train_raw
]

# 3. DataLoader
BATCH_SIZE = 16
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)

# 4. Load base model
print("\nLoading base model: all-MiniLM-L6-v2...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 5. Loss function
# Trains the model so cosine(embed_A, embed_B) ≈ label
# Perfect for our 0.0–1.0 relevance scores
train_loss = losses.CosineSimilarityLoss(model)

# 6. Evaluator
# Tracks Spearman correlation between predicted and ground-truth similarity
sentences1 = [p["text_a"] for p in eval_raw]
sentences2 = [p["text_b"] for p in eval_raw]
labels     = [float(p["label"]) for p in eval_raw]

evaluator = evaluation.EmbeddingSimilarityEvaluator(
    sentences1, sentences2, labels,
    name="gisma-eval",
)

# Helper: extract Spearman score
def get_spearman(result) -> float:
    if isinstance(result, dict):
        # Key is 'spearman_cosine' in newer versions
        for key in ("spearman_cosine", "spearman_correlation", "spearman"):
            if key in result:
                return float(result[key])
        # Fallback: take the first numeric value in the dict
        return float(next(v for v in result.values() if isinstance(v, (int, float))))
    return float(result)

# 7. Baseline evaluation
print("\nBaseline (before fine-tuning):")
baseline_raw   = evaluator(model, output_path=None)
baseline_score = get_spearman(baseline_raw)
print(f"   Spearman correlation: {baseline_score:.4f}")

# 8. Training
EPOCHS      = 4
WARMUP_RATE = 0.1
total_steps = len(train_dataloader) * EPOCHS
warmup_steps = int(total_steps * WARMUP_RATE)

print(f"\nStarting GISMABert fine-tuning...")
print(f"   Epochs:       {EPOCHS}")
print(f"   Batch size:   {BATCH_SIZE}")
print(f"   Total steps:  {total_steps}")
print(f"   Warmup steps: {warmup_steps}")
print(f"   Output:       ./gismabert/\n")

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    evaluator=evaluator,
    epochs=EPOCHS,
    warmup_steps=warmup_steps,
    evaluation_steps=max(100, len(train_dataloader) // 2),
    output_path="./gismabert",      # saves best checkpoint automatically
    save_best_model=True,
    show_progress_bar=True,
    checkpoint_save_steps=0,        # no intermediate checkpoints (save space)
)

# 9. Final evaluation
print("\nGISMABert (after fine-tuning):")
final_model = SentenceTransformer("./gismabert")
final_raw   = evaluator(final_model, output_path=None)
final_score = get_spearman(final_raw)
print(f"   Spearman correlation: {final_score:.4f}")
print(f"   Improvement over baseline: +{(final_score - baseline_score):.4f}")

# 10. Sanity check
print("\nSanity check — cosine similarity scores:")

test_cases = [
    (
        "Python SQL Machine Learning Data Analysis Pandas",
        "Junior Data Analyst — Python and SQL required, ML experience a plus",
        "Should be HIGH (Data Science match)",
    ),
    (
        "Python SQL Machine Learning Data Analysis Pandas",
        "HR Manager — recruitment, payroll, employee relations",
        "Should be LOW (HR, not Data Science)",
    ),
    (
        "Marketing SEO Google Analytics Content Marketing",
        "Digital Marketing Manager — SEO, Google Ads, social media campaigns",
        "Should be HIGH (Marketing match)",
    ),
    (
        "Marketing SEO Google Analytics Content Marketing",
        "Backend Developer — Python, Django, REST APIs, Docker",
        "Should be LOW (Dev, not Marketing)",
    ),
]

import numpy as np

for text_a, text_b, note in test_cases:
    emb_a = final_model.encode(text_a)
    emb_b = final_model.encode(text_b)
    score = float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b)))
    print(f"   {note}")
    print(f"     Score: {score:.3f}\n")

print("GISMABert training complete.")
print("Model saved to: ./gismabert/")
print("Download the 'gismabert' folder from the Colab Files panel.")
print("Place it at: python-backend/gismabert/")
