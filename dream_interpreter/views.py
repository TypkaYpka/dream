import uuid
from models import ChatSession, ChatHistory, db
from datetime import datetime, timedelta
import pytz
# новый чат генерит и в бд заливает изменения
def create_chat_session(user_id, title=None):
    session_id = str(uuid.uuid4())
    new_session = ChatSession(session_id=session_id, user_id=user_id, title=title)
    db.session.add(new_session)
    db.session.commit()
    return new_session  # Возвращаем объект сессии

# в бд чат сохраняет, пользователя и нейронки
def save_message(user_id, session_id, message_type, content):
    new_message = ChatHistory(
        user_id=user_id,
        session_id=session_id,
        message_type=message_type,
        content=content
    )
    db.session.add(new_message)
    db.session.commit()

# соритрует историю по датам
def get_chat_sessions_by_time(user_id):
    now = datetime.now(pytz.timezone('Europe/Moscow'))  # Correct timezone string
    today = now.date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
    result = {'today': [], 'yesterday': [], 'last_7_days': [], 'last_30_days': [], 'older': []}

    for session in sessions:
        created = session.created_at.date()
        if created == today:
            result['today'].append(session)
        elif created == yesterday:
            result['yesterday'].append(session)
        elif seven_days_ago < created < yesterday:
            result['last_7_days'].append(session)
        elif thirty_days_ago < created <= seven_days_ago:
            result['last_30_days'].append(session)
        else:
            result['older'].append(session)

    return result
