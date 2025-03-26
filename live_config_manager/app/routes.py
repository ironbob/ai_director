from flask import render_template, request, redirect, url_for, flash, current_app,send_from_directory, abort,send_file
from app.models import SimpleApp
from app import db
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.models import SimpleApp
from app import db
import os
import uuid
import json

bp = Blueprint('main', __name__)
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
