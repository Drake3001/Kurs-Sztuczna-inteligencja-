# Ewaluacja encoder-only na PolEmo2 — skrypt Google Colab
# Uruchomienie:
#   1. Komórka instalacji: !pip install -q transformers datasets torch scikit-learn accelerate pandas
#   2. Uruchom resztę tego pliku

# %% Instalacja (pierwsza komórka Colab)
# !pip install -q transformers datasets torch scikit-learn accelerate pandas

# %% Importy i konfiguracja
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import torch
from datasets import load_dataset
from google.colab import files
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import pipeline

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = Path("results")

MODELS = [
    "Voicelab/herbert-base-cased-sentiment",
    "bardsai/twitter-sentiment-pl-base",
    "tabularisai/multilingual-sentiment-analysis",
]

BATCH_SIZE = 16
PARAM_GRID = [
    {"batch_size": BATCH_SIZE, "truncation": True, "max_length": 64},
    {"batch_size": BATCH_SIZE, "truncation": True, "max_length": 128},
    {"batch_size": BATCH_SIZE, "truncation": True, "max_length": 256},
    {"batch_size": BATCH_SIZE, "truncation": True, "max_length": 512},
    {"batch_size": BATCH_SIZE, "truncation": False, "max_length": 512},
]

_UNKNOWN_LABELS: set[str] = set()

# Znane mapowania etykiet modeli (id -> nazwa z config.id2label)
KNOWN_ID2LABEL = {
    "Voicelab/herbert-base-cased-sentiment": {
        0: "negative",
        1: "neutral",
        2: "positive",
    },
    "bardsai/twitter-sentiment-pl-base": {
        0: "positive",
        1: "neutral",
        2: "negative",
    },
    "tabularisai/multilingual-sentiment-analysis": {
        0: "Very Negative",
        1: "Negative",
        2: "Neutral",
        3: "Positive",
        4: "Very Positive",
    },
}


def setup_results_dirs() -> None:
    for subdir in ("predictions", "metrics", "logs", "reports"):
        (RESULTS_DIR / subdir).mkdir(parents=True, exist_ok=True)


def setup_logging() -> Path:
    log_path = RESULTS_DIR / "logs" / f"ewaluacja_{TIMESTAMP}.log"
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
    )
    return log_path


def safe_name(model_name: str) -> str:
    return model_name.replace("/", "_")


def normalize_id2label(raw_id2label: dict) -> dict[int, str]:
    return {int(k): v for k, v in raw_id2label.items()}


def _to_polemo_label(label_name: str) -> str | None:
    """Mapuje nazwę etykiety modelu na klasę PolEmo2."""
    label = label_name.lower().strip()

    if label == "very negative" or label == "negative":
        return "__label__meta_minus_m"
    if label == "very positive" or label == "positive":
        return "__label__meta_plus_m"
    if label == "neutral":
        return "__label__meta_zero"
    if "negatywn" in label or "minus" in label:
        return "__label__meta_minus_m"
    if "pozytywn" in label or "plus" in label:
        return "__label__meta_plus_m"

    return None


def map_label(
    model_label: str,
    id2label: dict[int, str] | None = None,
    model_name: str | None = None,
) -> str:
    """Przetwarza etykiety z różnych modeli na standard PolEmo2.0."""
    original = str(model_label).strip()
    label_key = original.upper()

    if label_key.startswith("LABEL_"):
        idx = int(label_key.split("_")[1])
        lookup = id2label or (KNOWN_ID2LABEL.get(model_name) if model_name else None)
        if lookup and idx in lookup:
            mapped = _to_polemo_label(lookup[idx])
            if mapped:
                return mapped

    mapped = _to_polemo_label(original)
    if mapped:
        return mapped

    if original not in _UNKNOWN_LABELS:
        _UNKNOWN_LABELS.add(original)
        logging.warning(
            "Nieznana etykieta modelu: %s -> przypisano neutral", original
        )
    return "__label__meta_zero"


def evaluate_model(
    dataset,
    model_name: str,
    param_id: str,
    batch_size: int = 16,
    truncation: bool = True,
    max_length: int = 128,
    save_csv: bool = True,
) -> dict:
    device = 0 if torch.cuda.is_available() else -1
    logging.info(
        "Start ewaluacji: model=%s, param_id=%s, batch_size=%d, max_length=%d",
        model_name,
        param_id,
        batch_size,
        max_length,
    )

    classifier = pipeline("text-classification", model=model_name, device=device)
    id2label = normalize_id2label(classifier.model.config.id2label)

    texts = dataset["sentence"]
    true_labels = dataset["target"]

    raw_predictions = classifier(
        texts,
        batch_size=batch_size,
        truncation=truncation,
        max_length=max_length,
    )
    mapped_predictions = [
        map_label(pred["label"], id2label=id2label, model_name=model_name)
        for pred in raw_predictions
    ]

    accuracy = accuracy_score(true_labels, mapped_predictions)
    f1 = f1_score(true_labels, mapped_predictions, average="macro")
    recall = recall_score(true_labels, mapped_predictions, average="macro")
    precision = precision_score(true_labels, mapped_predictions, average="macro")

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = safe_name(model_name)
    pipeline_kwargs = {
        "batch_size": batch_size,
        "truncation": truncation,
        "max_length": max_length,
    }

    evaluation_summary = {
        "model": model_name,
        "param_id": param_id,
        "batch_size": batch_size,
        "truncation": truncation,
        "max_length": max_length,
        "kwargs": pipeline_kwargs,
        "id2label": {str(k): v for k, v in id2label.items()},
        "timestamp": run_timestamp,
        "ogolne_metryki": {
            "accuracy": accuracy,
            "f1_macro": f1,
            "recall_macro": recall,
            "precision_macro": precision,
        },
        "detailed_report": classification_report(
            true_labels, mapped_predictions, output_dict=True
        ),
    }

    report_text = classification_report(true_labels, mapped_predictions)
    report_path = RESULTS_DIR / "reports" / f"{safe_model}_{param_id}_{run_timestamp}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Model: {model_name}\n")
        f.write(f"Parametry: param_id={param_id}, batch_size={batch_size}, ")
        f.write(f"truncation={truncation}, max_length={max_length}\n")
        f.write(f"Accuracy: {accuracy:.4f}\n")
        f.write(f"F1 macro: {f1:.4f}\n\n")
        f.write("Szczegółowy raport (Quality per class):\n")
        f.write(report_text)

    json_path = RESULTS_DIR / "metrics" / f"{safe_model}_{param_id}_{run_timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_summary, f, indent=4, ensure_ascii=False)

    if save_csv:
        df = dataset.to_pandas()
        df["raw_prediction"] = [pred["label"] for pred in raw_predictions]
        df["mapped_prediction"] = mapped_predictions
        df["prediction_score"] = [pred["score"] for pred in raw_predictions]
        csv_path = RESULTS_DIR / "predictions" / f"wyniki_{safe_model}_{param_id}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")

    logging.info(
        "Zakonczono: model=%s, param_id=%s, accuracy=%.4f, f1_macro=%.4f",
        model_name,
        param_id,
        accuracy,
        f1,
    )

    return {
        "model": model_name,
        "param_id": param_id,
        "batch_size": batch_size,
        "truncation": truncation,
        "max_length": max_length,
        "accuracy": accuracy,
        "f1_macro": f1,
        "recall_macro": recall,
        "precision_macro": precision,
        "timestamp": run_timestamp,
    }


def run_experiments(dataset, models: list[str], param_grid: list[dict]) -> pd.DataFrame:
    summary_rows = []
    total = len(models) * len(param_grid)
    run_num = 0

    for model_name in models:
        for params in param_grid:
            run_num += 1
            trunc_tag = "trunc" if params["truncation"] else "notrunc"
            param_id = f"ml{params['max_length']}_{trunc_tag}"
            logging.info("Eksperyment %d/%d", run_num, total)
            result = evaluate_model(
                dataset,
                model_name,
                param_id=param_id,
                batch_size=params["batch_size"],
                truncation=params["truncation"],
                max_length=params["max_length"],
            )
            summary_rows.append(result)

    summary_df = pd.DataFrame(summary_rows)
    summary_path = RESULTS_DIR / f"porownanie_ewaluacji_{TIMESTAMP}.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8")
    logging.info("Zapisano zbiorcze porownanie: %s", summary_path)
    return summary_df


def zip_and_download(results_dir: Path = RESULTS_DIR) -> str:
    zip_base = f"wyniki_ewaluacji_{TIMESTAMP}"
    zip_path = shutil.make_archive(zip_base, "zip", str(results_dir))
    files.download(zip_path)
    print(f"Zapisano i pobrano: {zip_path}")
    return zip_path


# %% Uruchomienie ewaluacji
setup_results_dirs()
setup_logging()

logging.info("Ladowanie zbioru danych...")
raw_dataset = load_dataset("allegro/klej-polemo2-in", split="test")
dataset = raw_dataset.filter(lambda x: x["target"] != "__label__meta_amb")
logging.info("Zaladowano %d probek testowych", len(dataset))

run_experiments(dataset, MODELS, PARAM_GRID)
zip_and_download()
