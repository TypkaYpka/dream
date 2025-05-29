import re
from typing import List
import torch

import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
from deep_translator import GoogleTranslator

from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

def generate_interpretation(theme: str) -> str:
    theme_to_eng = GoogleTranslator(source='ru', target='en').translate(theme) # перевод запроса на английский
    # Загрузка модели и токенизатора
    model_path = "./model"  # Путь к папке с моделью
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)

    # Создание генератора
    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device="cpu"
    )
    result = generator(
        theme_to_eng,
        max_length=200,
        temperature=0.7,
        truncation=True
    )
    print(result)
    answer = result[0]["generated_text"][result[0]["generated_text"].find('n:') + 2:].strip()
    translated_ru = GoogleTranslator(source='en', target='ru').translate(answer) # перевод ответа на русский

    
    return translated_ru
