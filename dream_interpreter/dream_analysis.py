import re
from typing import List
import torch

import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib  # для сохранения модели, если нужно
from deep_translator import GoogleTranslator

# Загрузка необходимых данных NLTK
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('omw-1.4')

# =========================
# Шаг 1. Очистка и лемматизация
# =========================
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^а-яА-Яa-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize_and_lemmatize(text: str) -> List[str]:
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text)
    lemmas = [lemmatizer.lemmatize(tok) for tok in tokens]
    return lemmas

def preprocess_for_tfidf(text: str) -> str:
    cleaned = clean_text(text)
    lemmas = tokenize_and_lemmatize(cleaned)
    return " ".join(lemmas)

# =========================
# Шаг 2. Векторизация TF-IDF
# =========================
def build_tfidf_vectorizer(docs: List[str]) -> TfidfVectorizer:
    processed_docs = [preprocess_for_tfidf(doc) for doc in docs]
    vectorizer = TfidfVectorizer()
    vectorizer.fit(processed_docs)
    return vectorizer

def vectorize_dream(dream: str, vectorizer: TfidfVectorizer):
    processed = preprocess_for_tfidf(dream)
    return vectorizer.transform([processed])

# =========================
# Шаг 3. Классификация сна
# =========================
# def train_classifier(docs: List[str], labels: List[str]):
#     processed_docs = [preprocess_for_tfidf(doc) for doc in docs]
#     model = make_pipeline(TfidfVectorizer(), MultinomialNB())
#     model.fit(processed_docs, labels)
#     return model

# def analyze_dream(dream: str):
#     # processed = '[p(*"&^:%Lr.dfil;j,mn )]'(dream)
#     prediction = model.predict([dream])[0]
#     return prediction

# from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# def generate_interpretation(theme: str) -> str:
#     theme_to_eng = GoogleTranslator(source='ru', target='en').translate(theme)
#     # Загрузка модели и токенизатора
#     model_path = "./model"  # Путь к папке с моделью
#     tokenizer = AutoTokenizer.from_pretrained(model_path)
#     model = AutoModelForCausalLM.from_pretrained(model_path)

#     # Создание генератора
#     generator = pipeline(
#         "text-generation",
#         model=model,
#         tokenizer=tokenizer,
#         device="cpu"
#     )
#     result = generator(
#         theme_to_eng,
#         max_length=200,
#         temperature=0.7,
#         truncation=True
#     )
#     print(result)
#     answer = result[0]["generated_text"][result[0]["generated_text"].find('n:') + 2:].strip()
#     translated_ru = GoogleTranslator(source='en', target='ru').translate(answer)

    
#     return translated_ru



'''--------------------------------------------------------------
-----------------------------------------------------------------
-----------------------------------------------------------------'''

# def generate_interpretation_phi3(symbols_list, model, tokenizer):
#     symbols_str = ", ".join(symbols_list)
#     prompt = f"<|user|>\nAnalyze the dream symbols: '{symbols_str}'. Provide a detailed interpretation.<|end|>\n<|assistant|>"

#     inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)

#     # Исправление для новых версий Transformers
#     generation_config = {
#         "max_new_tokens": 300,
#         "do_sample": True,
#         "temperature": 0.7,
#         "top_p": 0.9,
#         "top_k": 50,
#         "pad_token_id": tokenizer.eos_token_id,
#         "eos_token_id": tokenizer.eos_token_id
#     }

#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             **generation_config
#         )

#     # Обработка ответа
#     response = tokenizer.decode(outputs[0], skip_special_tokens=False)
#     assistant_part = response.split("<|assistant|>")[-1]
#     interpretation = assistant_part.replace("<|end|>", "").strip()

#     return interpretation

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

adapter_path = "./dream_interpreter_phi3_lora"
base_model_name = "microsoft/Phi-3-mini-4k-instruct"

# --- Конфигурация QLoRA ---
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=False,
)

# --- Загрузка базовой модели ---
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
)

# --- Загрузка токенизатора ---
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': tokenizer.eos_token})

# --- Загрузка и применение LoRA адаптера ---
model = PeftModel.from_pretrained(base_model, adapter_path)
model = model.merge_and_unload()  # Важно объединить адаптер с моделью!
model = model.eval()

# --- Функция для генерации (обновленная версия) ---
def generate_interpretation_phi3(symbols_list):
    symbols_list = GoogleTranslator(source='ru', target='en').translate(symbols_list)
    symbols_str = ", ".join(symbols_list)
    prompt = f"<|user|>\nAnalyze the dream symbols: '{symbols_str}'. Provide a detailed interpretation.<|end|>\n<|assistant|>"

    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)

    generation_kwargs = {
        "max_new_tokens": 300,
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "pad_token_id": tokenizer.eos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        # Добавляем параметры для новых версий Transformers
        "use_cache": False  # Отключаем кэширование для обхода ошибки
    }

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            **generation_kwargs
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    assistant_part = response.split("<|assistant|>")[-1]
    interpretation = assistant_part.replace("<|end|>", "").strip()
    interpretation = GoogleTranslator(source='en', target='ru').translate(interpretation)
    return interpretation