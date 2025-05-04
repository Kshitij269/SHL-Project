import json
import torch
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

with open("recommendationsResponse.txt", "r", encoding="utf-8") as f:
    predictions = json.load(f)

with open("shl_product_descriptions.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

true_descriptions = [entry["description"] for entry in ground_truth]
true_names = [entry["name"] for entry in ground_truth]

predicted_descriptions = [rec["description"] for rec in predictions["recommendations"]["recommended_assessments"]]
predicted_names = [rec["url"].split("/")[-2] for rec in predictions["recommendations"]["recommended_assessments"]]

true_embeddings = model.encode(true_descriptions, convert_to_tensor=True, normalize_embeddings=True)
pred_embeddings = model.encode(predicted_descriptions, convert_to_tensor=True, normalize_embeddings=True)

similarities = util.cos_sim(pred_embeddings, true_embeddings)  # [preds x truths]

name_to_index = {name: i for i, name in enumerate(true_names)}
ground_truth_indices = [name_to_index.get(name, -1) for name in predicted_names]

def recall_at_k(similarities, ground_truth_indices, k=10):
    recalls = []
    for i, true_idx in enumerate(ground_truth_indices):
        if true_idx == -1:
            continue
        top_k = torch.topk(similarities[i], k).indices.tolist()
        recalls.append(1 if true_idx in top_k else 0)
    return sum(recalls) / len(recalls) if recalls else 0.0

def map_at_k(similarities, ground_truth_indices, k=10):
    ap_scores = []
    for i, true_idx in enumerate(ground_truth_indices):
        if true_idx == -1:
            continue
        top_k = torch.topk(similarities[i], k).indices.tolist()
        if true_idx in top_k:
            rank = top_k.index(true_idx) + 1
            ap_scores.append(1.0 / rank)
        else:
            ap_scores.append(0.0)
    return sum(ap_scores) / len(ap_scores) if ap_scores else 0.0

k = 10
for i, pred_name in enumerate(predicted_names):
    top_k_indices = torch.topk(similarities[i], k).indices.tolist()
    print(f"\n🔍 Prediction {i+1}: '{pred_name}'")
    print("Top matches:")
    for rank, idx in enumerate(top_k_indices, 1):
        print(f"{rank}. {true_names[idx]} (Score: {similarities[i][idx]:.4f})")