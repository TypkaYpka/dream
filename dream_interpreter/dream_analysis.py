
import requests
from deep_translator import GoogleTranslator
import os
from litellm import completion

os.environ["HF_TOKEN"] = "TOKEN"  

def generate_interpretation(text):
    response = completion(
        system_prompt = """
            Ты профессиональный толкователь снов с 20-летним опытом в области психоанализа и символизма. 
            Каждый запрос пользователя — это описание сна. Анализируй сновидение по следующим аспектам:
            1. Основные символы и их психологическая интерпретация
            2. Связь с текущей жизненной ситуацией
            3. Возможные скрытые тревоги/желания
            4. Практические рекомендации
            5. Альтернативные трактовки

            Форматируй ответ:
            - Заголовки разделов выделяй через **
            - Списки оформляй через дефисы
            - Ключевые термины выделяй курсивом
            - Добавляй эмодзи для визуального разделения
            - Между разделами оставляй пустую строку
            """,
        model="huggingface/together/deepseek-ai/DeepSeek-R1",  # Используем Together AI как провайдер
        messages=[{"role": "user", "content": text}]
    )
    return format_dream_response(response.choices[0].message.content)

def format_dream_response(response):
    # Разделяем на разделы и добавляем оформление
    sections = response.split('###')
    formatted = []
    
    for section in sections:
        if not section.strip():
            continue
            
        # Обработка заголовков
        if section.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
            header, _, content = section.partition('**')
            header = header.strip().replace('\n', '')
            formatted.append(f"\n**{header}**")
            
            # Обработка списков
            if '—' in content:
                list_items = [item.strip() for item in content.split('—') if item.strip()]
                for item in list_items:
                    formatted.append(f"- {item}")
            else:
                formatted.append(content)
        else:
            formatted.append(section)
    
    # Добавляем эмодзи-разделители
    return "\n".join(formatted).replace('**', '\n**').replace(' - ', '\n- ')
