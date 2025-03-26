from flask import render_template, request, redirect, url_for, flash, current_app,send_from_directory, abort,send_file
from app.models import SimpleApp,MessageType,UserEnterMessage,UserFollowMessage,UserMessage,UserGiftMessage,UserOrderMessage,BaseMessage
from app import db
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.models import SimpleApp
from app import db
import os
import uuid
import json
from typing import Dict
from app.LiveChatBot import LiveChatBot 
from threading import Lock
from flask_socketio import socketio
import time
from threading import Thread
from flask import jsonify

bp = Blueprint('main', __name__)
# 内存存储
live_bots: Dict[str, LiveChatBot] = {}
bot_lock = Lock()
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/')
def index():
    username = request.args.get('username', '')
    apps = []
    if username:
        apps = SimpleApp.query.filter_by(username=username).order_by(SimpleApp.created_at.desc()).all()
    return render_template('index.html', apps=apps, username=username)

@bp.route('/create', methods=['GET', 'POST'])
def create_app():
    username = request.args.get('username', '')
    if not username:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        app_name = request.form.get('app_name')
        config_file = request.files.get('config_file')
        
        if not app_name:
            flash('应用名称不能为空', 'danger')
            return redirect(url_for('main.create_app', username=username))
        
        new_app = SimpleApp(username=username, app_name=app_name)
        
        if config_file and allowed_file(config_file.filename):
            filename = f"{uuid.uuid4().hex}.json"
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            config_file.save(filepath)
            new_app.config_filename = filename
        
        db.session.add(new_app)
        db.session.commit()
        flash('应用创建成功!', 'success')
        return redirect(url_for('main.index', username=username))
    
    return render_template('create.html', username=username)

@bp.route('/app/<int:app_id>')
def app_detail(app_id):
    app = SimpleApp.query.get_or_404(app_id)
    config_content = app.get_config_content()
    
    # 处理 JSON 数据，确保中文正常显示
    if isinstance(config_content, dict):
        # 如果已经是字典格式，直接使用
        config_json = config_content
    else:
        try:
            # 尝试解析 JSON 字符串
            config_json = json.loads(config_content) if config_content else None
        except (TypeError, json.JSONDecodeError) as e:
            # 如果不是有效的 JSON，作为纯文本传递
            config_json = None
    
    return render_template('detail.html', 
                         app=app,
                         config_content=config_json if config_json else config_content)

@bp.route('/app/<int:app_id>/download')
def download_config(app_id):
    app = SimpleApp.query.get_or_404(app_id)
    
    # 调试信息
    print(f"请求下载应用ID: {app_id}")
    print(f"配置文件名: {app.config_filename}")
    print(f"上传目录: {current_app.config['UPLOAD_FOLDER']}")
    
    if not app.config_filename:
        print("错误: 数据库中没有记录文件名")
        abort(404)
    
    # 构建完整路径
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], app.config_filename)
    print(f"完整文件路径: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在于路径 {file_path}")
        abort(404)
    
    try:
        return send_file(
            path_or_file=file_path,
            as_attachment=True
        )
    except Exception as e:
        print(f"下载时发生错误: {str(e)}")
        abort(500)

@bp.route('/api/app/<int:app_id>')
def get_app_config(app_id):
    app = SimpleApp.query.get_or_404(app_id)
    config_content = app.get_config_content()
    if config_content is None:
        return {'error': 'Config not found'}, 404
    return config_content

def get_or_create_bot(app_id: str) -> LiveChatBot:
    with bot_lock:
        if app_id not in live_bots:
            live_bots[app_id] = LiveChatBot(app_id)
        return live_bots[app_id]

# 启动消息处理器线程
def start_message_processor():
    def processor():
        while True:
            with bot_lock:
                for bot in live_bots.values():
                    responses = bot.process_messages()
                    if responses:
                        socketio.emit('bot_response', {
                            'app_id': bot.app_id,
                            'messages': responses
                        }, room=f'app_{bot.app_id}')
            
            time.sleep(1)  # 每秒检查一次
    
    thread = Thread(target=processor)
    thread.daemon = True
    thread.start()

def handle_live_message_common(app_id: str, message_type: MessageType, data: dict):
    bot = get_or_create_bot(app_id)
    
    # 创建对应的消息对象
    if message_type == MessageType.USER_ENTER:
        message = UserEnterMessage(data['username'])
    elif message_type == MessageType.USER_FOLLOW:
        message = UserFollowMessage(data['username'])
    elif message_type == MessageType.USER_MESSAGE:
        message = UserMessage(data['username'], data['content'])
    elif message_type == MessageType.USER_GIFT:
        message = UserGiftMessage(
            username=data['username'],
            gift_name=data['gift_name'],
            gift_value=data.get('gift_value', 0)  # 默认值
        )
    elif message_type == MessageType.USER_ORDER:
        message = UserOrderMessage(
            username=data['username'],
            product_name=data['product_name'],
            amount=data.get('amount', 0)  # 默认值
        )
    else:
        return False
        
    bot.add_message(message)
    return True

# WebSocket消息处理 (保持原有)
@socketio.on('live_message')
def handle_live_message(data):
    try:
        message_type = MessageType(data['type'])
        if handle_live_message_common(data['app_id'], message_type, data):
            return {'status': 'success'}
        return {'status': 'error', 'message': 'Invalid message type'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 新增HTTP消息接口
@bp.route('/api/message', methods=['POST'])
def http_handle_message():
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        # 验证必要字段
        required_fields = ['app_id', 'type', 'username']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing field: {field}'}), 400
        
        message_type = MessageType(data['type'])
        if handle_live_message_common(data['app_id'], message_type, data):
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Invalid message type'}), 400
    except ValueError as e:
        return jsonify({'status': 'error', 'message': f'Invalid message type: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取历史消息
@bp.route('/api/bot/<app_id>/history', methods=['GET'])
def get_history(app_id):
    bot = get_or_create_bot(app_id)
    return jsonify({
        'history': [msg.to_dict() for msg in bot.message_history[-20:]]
    })