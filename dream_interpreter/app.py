# import logging
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import ChatHistory, ChatSession, db
from dream_analysis import generate_interpretation
from views import create_chat_session, save_message, get_chat_sessions_by_time
from auth import app

# главная страница
@app.route("/")
def index():
    if current_user.is_authenticated:
        categorized_sessions = get_chat_sessions_by_time(current_user.id)
        session_data = {}
        for category, sessions in categorized_sessions.items():
            session_data[category] = []
            for session in sessions:
                last_message = ChatHistory.query.filter_by(session_id=session.session_id).order_by(ChatHistory.timestamp.desc()).first()
                session_data[category].append({
                    "session_id": session.session_id,
                    "last_message": last_message.content[:60] + "..." if last_message else "(пустой чат)"
                })
    else:
        session_data = {}

    return render_template("index.html", session_data=session_data)

# новый диалог
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    dream_text = request.form.get("dream")

    # logger.debug(f"Received dream text: {dream_text}")

    if not dream_text:
        flash("Введите текст сна.")
        return redirect(url_for("index"))


    dream_text = request.form.get("dream")
    interpretation = generate_interpretation(dream_text)

    # Создаем новую сессию для нового сна
    session = create_chat_session(current_user.id)

    # logger.debug(f"Using session: {session.session_id}")

    # Сохраняем вопрос и ответ
    save_message(user_id=current_user.id, session_id=session.session_id, message_type='user', content=dream_text)
    save_message(user_id=current_user.id, session_id=session.session_id, message_type='assistant', content=interpretation)

    return redirect(url_for('chat', session_id=session.session_id))

# продолжение текущего диалога
@app.route("/analyze_cont", methods=["POST"])
@login_required
def analyze_cont():
    dream_text = request.form.get("dream")
    session_id = request.form.get("session_id")

    # logger.debug(f"Received dream text: {dream_text}")
    # logger.debug(f"Received session_id: {session_id}")

    if not dream_text:
        flash("Введите текст сна.")
        return redirect(url_for("index"))

    # Анализируем сон
    interpretation = generate_interpretation(dream_text)

    # ищем сессию и если находим продолжаем чат
    if session_id:
        session = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.id).first()
        if not session:
            session = create_chat_session(current_user.id)
    else:
        session = create_chat_session(current_user.id)

    # logger.debug(f"Using session: {session.session_id}")

    # Сохраняем вопрос и ответ
    save_message(user_id=current_user.id, session_id=session.session_id, message_type='user', content=dream_text)
    save_message(user_id=current_user.id, session_id=session.session_id, message_type='assistant', content=interpretation)

    return redirect(url_for('chat', session_id=session.session_id))

# новый чат
@app.route("/new_chat")
@login_required
def new_chat():
    session = create_chat_session(current_user.id)
    # logger.debug(f"Created new session: {session.session_id}")
    return redirect(url_for("chat", session_id=session.session_id))

# добавление сообщений в существующий чат
@app.route("/chat/<session_id>")
@login_required
def chat(session_id):
    session = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.id).first_or_404()
    messages = ChatHistory.query.filter_by(session_id=session_id).order_by(ChatHistory.timestamp).all()
    # logger.debug(f"Loaded messages for session {session_id}: {messages}")

    # Получаем данные о сессиях для боковой панели (категоризировано)
    categorized_sessions = get_chat_sessions_by_time(current_user.id)
    session_data = {}
    for category, sessions in categorized_sessions.items():
        session_data[category] = []
        for s in sessions:
            last_message = ChatHistory.query.filter_by(session_id=s.session_id).order_by(ChatHistory.timestamp.desc()).first()
            session_data[category].append({
                "session_id": s.session_id,
                "last_message": last_message.content[:60] + "..." if last_message else "(пустой чат)"
            })

    return render_template("chat.html", session=session, messages=messages, session_data=session_data)

# удаление чата
@app.route("/delete_chat/<session_id>", methods=["DELETE"])
@login_required
def delete_chat(session_id):
    session = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.id).first()
    if session:
        # Удаляем все сообщения, связанные с этой сессией
        ChatHistory.query.filter_by(session_id=session_id).delete()
        # Удаляем саму сессию
        db.session.delete(session)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Session not found"}), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
