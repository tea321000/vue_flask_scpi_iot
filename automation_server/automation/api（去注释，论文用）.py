from flask import Flask, abort, request, jsonify, g, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_httpauth import HTTPBasicAuth

import sys
from automation import automation
from .sql import db
from .models import User, UserList, DeviceRegister, DeviceAlive, QueryHistory, Feedback
import time
auth = HTTPBasicAuth()

# 错误码：400:未填写用户名或密码；401:用户名或密码错误；402：用户名已存在；405:非法的user_token; 406:学号/编号和姓名输入错误;  407:Token 过期了;410:非法的device_token;411:非法的设备注册信息;412:设备注册信息填写错误;416:用户权限不足;417:设备不在线
#用户登录
@automation.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    print(username, password, file=sys.stderr)
    if username is None or password is None:
        abort(400)
    success = verify_password(username, password)
    if not success:
        abort(401)
    token = g.user.generate_auth_token()
    resp = jsonify(
        {'data': {'token': token.decode('ascii'), 'content': "login!"}})
    resp.status_code = 200
    return resp

#用户注册
@automation.route('/register', methods=['POST'])
def new_user():
    username = request.json.get('username')
    name = request.json.get('name')
    password = request.json.get('password')
    birthday = request.json.get('birthday')
    phone = request.json.get('phone')
    role = request.json.get('role')
    # permission = 1 if role == 'student' else 2
    if role == 'visitor':
        permission = 1
    elif role == 'observer':
        permission = 3
    elif role == 'manager':
        permission = 7
    elif role == 'administrator':
        permission = 15
    if username is None or password is None:
        # return jsonify({'code': 400})    # missing arguments
        abort(400)
    if User.query.filter_by(id=username).first() is not None:
        # return jsonify({'code': 402})    # existing user
        abort(402)
    if UserList.query.filter_by(id=username, name=name, role=role).first() is None:
        # try to authenticate with username/password
        abort(406)
        # return jsonify({'code': 406})
    else:
        user = User(id=username, name=name,
                    birthday=birthday, phone=phone, role=role, permission=permission)
        user.hash_password(password)
        from app import db
        db.session.add(user)
        db.session.commit()
        resp = jsonify({'username': user.id})
        resp.status_code = 201
        return resp

#比对密码
@auth.verify_password
def verify_password(username_or_token, password):
    #尝试使用token登录
    user = User.verify_auth_token(username_or_token)
    if not user:
        # 尝试使用用户名/密码登录
        user = User.query.filter_by(id=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

#前端向后端请求用户信息时使用
@auth.login_required
@automation.route('/info', methods=['POST'])
def information():
    token = request.json.get('token')
    user = User.verify_auth_token(token)
    if user is None:
        abort(405)
    else:
        resp = jsonify(
            {'data': {'roles': [user.role], 'name': user.name, 'id': user.id, 'birthday': user.birthday+'', 'phone': user.phone}})
        return resp

#更改个人信息
@auth.login_required
@automation.route('/personal', methods=['POST'])
def personalChange():
    token = request.json.get('token')
    user = User.verify_auth_token(token)
    if(user is None):
        abort(405)
    password = request.json.get('password')
    birthday = request.json.get('birthday')
    phone = request.json.get('phone')
    if(password is not None):
        user.hash_password(password)
    user.birthday = birthday
    user.phone = phone
    db.session.commit()
    resp = jsonify()
    resp.status_code = 200
    return resp

#用户登出
@auth.login_required
@automation.route('/logout', methods=['POST'])
def logout():
    resp = jsonify()
    resp.status_code = 202
    return resp


# 前端查询在线设备
@auth.login_required
@automation.route('/query_device', methods=['POST'])
def queryDevice():
    token = request.json.get('token')
    user = User.verify_auth_token(token)
    if not user:
        abort(405)
    devices_json = {'data': {}}
    for device_alive in DeviceAlive.query.all():
        now = int(round(time.time() * 1000))
        if now-device_alive.heartbeat_timestamp < 60000:
            devices_json['data'].update({device_alive.serial: {}})

            devices_json['data'][device_alive.serial]['device_set'] = device_alive.device.device_set
            devices_json['data'][device_alive.serial]['device_type'] = device_alive.device.device_type

            if user.permission < device_alive.device.permission:
                devices_json['data'][device_alive.serial]['write_permission'] = False
            elif device_alive.device.permission <= user.permission:
                devices_json['data'][device_alive.serial]['write_permission'] = True

        else:
            db.session.delete(device_alive)
            db.session.commit()

    return jsonify(devices_json)

# 前端查询设备历史信息
@auth.login_required
@automation.route('/device_history', methods=['POST'])
def queryDeviceHistory():
    token = request.json.get('token')
    user = User.verify_auth_token(token)
    devices_json = {'data': {}}
    for device in DeviceRegister.query.all():
        devices_json['data'].update({device.serial: {}})
        devices_json['data'][device.serial]['device_set'] = device.device_set
        devices_json['data'][device.serial]['device_type'] = device.device_type

        user_read_permission = user.permission % 3
        device_read_permission = device.permission % 3

        if user_read_permission < device_read_permission:
            devices_json['data'][device.serial]['read_permission'] = False
        elif user_read_permission >= device_read_permission:
            devices_json['data'][device.serial]['read_permission'] = True
            devices_json['data'][device.serial]['history'] = []
            for history in device.query_historys:
                devices_json['data'][device.serial]['history'].append(
                    {'content': history.command_content, 'timestamp': history.query_timestamp, 'response': history.response})

    return jsonify(devices_json)

# 前端发送用户指令
@automation.route('/command', methods=['POST'])
def deviceCommand():
    token = request.json.get('token')
    user = User.verify_auth_token(token)
    if(user is None):
        abort(405)
    device_serial = request.json.get('serial')
    device = DeviceRegister.query.filter_by(serial=device_serial).first()
    if device is None:
        abort(411)
    if device.permission > user.permission:
        abort(416)
    if not device.alive:
        abort(417)
    command = request.json.get('command')
    query_history = QueryHistory(
        device_serial=device_serial, user_id=user.id, query_timestamp=int(round(time.time() * 1000)), command_content=command)
    db.session.add(query_history)
    db.session.commit()
    resp = jsonify(success=True)
    return resp

#设备心跳包交互
@automation.route('/device', methods=['POST'])
def device():
    token = request.json.get('device_token')
    device = DeviceRegister.verify_auth_token(token)
    if not device:
        abort(410)
    # 心跳
    if not device.alive:
        device_alive = DeviceAlive(
            serial=device.serial, heartbeat_timestamp=int(round(time.time() * 1000)))
        db.session.add(device_alive)
        db.session.commit()
    else:
        device_alive = DeviceAlive.query.filter_by(
            serial=device.serial).first()
        if not device_alive:
            abort(411)
        device_alive.heartbeat_timestamp = int(round(time.time() * 1000))
        db.session.commit()

    response = request.json.get('response')
    #接收回应
    if response:
        for item in response:
            history = QueryHistory.query.with_parent(device).filter_by(id=item['id']).first()
            if history and not history.response:
                history.response = item.response
        db.session.commit()
    # 发送请求
    commands_json = {'data': {'commands': []}}
    for id, content in QueryHistory.query.with_parent(device).filter_by(response=None).order_by(
            desc(QueryHistory.query_timestamp)).with_entities(QueryHistory.id, QueryHistory.command_content):
        command_json = {'id': id, 'content': content}
        commands_json['data']['commands'].append(command_json)
    return jsonify(commands_json)

#设备端注册
@automation.route('/device_register', methods=['POST'])
def device_register():
    serial = request.json.get('serial')
    mac = request.json.get('mac')
    user_agent = request.headers.get('User-Agent')
    device_type = request.json.get('device_type')
    device_set = request.json.get('device_set')
    permission = request.json.get('permission')
    if not serial or not mac or not user_agent or not device_type or not device_set or not permission:
        abort(411)
    if DeviceRegister.query.filter_by(serial=serial).first() is None:
        # 设备注册流程
        device = DeviceRegister(
            serial=serial, user_agent=user_agent, device_type=device_type, device_set=device_set, permission=permission)
        device.hash_mac(mac)
        db.session.add(device)
        db.session.commit()
        token = device.generate_auth_token()
        resp = jsonify(
            {'data': {'device_token': token.decode('ascii')}})
        return resp
    else:
        # 设备验证流程
        auth_device = DeviceRegister.query.filter_by(
            serial=serial, user_agent=request.headers.get('User-Agent')).first()
        if auth_device and auth_device.verify_mac(mac):
            # 验证成功
            auth_device.device_type = device_type
            auth_device.device_set = device_set
            auth_device.permission = permission
            db.session.commit()
            token = auth_device.generate_auth_token()
            resp = jsonify(
                {'data': {'device_token': token.decode('ascii')}})
            return resp
        else:
            # 验证失败
            abort(412)
