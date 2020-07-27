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

# 400:未填写用户名或密码；401:用户名或密码错误；402：用户名已存在；405:非法的user_token; 406:学号/编号和姓名输入错误;  407:Token 过期了;410:非法的device_token;411:非法的设备注册信息;412:设备注册信息填写错误;416:用户权限不足;417:设备不在线
@automation.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    print(username, password, file=sys.stderr)
    if username is None or password is None:
        # abort(400)    # missing arguments
        abort(400)
    success = verify_password(username, password)
    if not success:
        abort(401)
    token = g.user.generate_auth_token()
    resp = jsonify(
        {'data': {'token': token.decode('ascii'), 'content': "login!"}})
    resp.status_code = 200
    return resp

# 需修改：注册请求permission进行permission定制化
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


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(id=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@auth.login_required
@automation.route('/info', methods=['POST'])
def information():
    token = request.json.get('token')
    # print(token, file=sys.stderr)
    user = User.verify_auth_token(token)
    # print('token-------------',file=sys.stderr)
    # print(token,file=sys.stderr)
    # print('id-------------',file=sys.stderr)
    # print(user.id,file=sys.stderr)
    # print('role-------------',file=sys.stderr)
    # print([user.role],file=sys.stderr)
    # print('birthday-------------', file=sys.stderr)
    # print(user.birthday, file=sys.stderr)
    # print('phone-------------', file=sys.stderr)
    # print(user.phone, file=sys.stderr)
    # print('end-------------', file=sys.stderr)

    if user is None:
        abort(405)
    else:
        birthday = str(user.birthday)
        resp = jsonify(
            {'data': {'roles': [user.role], 'name': user.name, 'id': user.id, 'birthday': birthday, 'phone': user.phone}})
        return resp


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


@auth.login_required
@automation.route('/logout', methods=['POST'])
def logout():
    resp = jsonify()
    resp.status_code = 202
    return resp


# 查询在线设备
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
        if now-device_alive.heartbeat_timestamp < 10000:
            devices_json['data'].update({device_alive.serial: {}})

            devices_json['data'][device_alive.serial]['device_set'] = device_alive.device.device_set
            devices_json['data'][device_alive.serial]['device_type'] = device_alive.device.device_type

            # user_read_permission=user.permission%3
            # device_read_permission=device_alive.device.permission%3
            # user_write_permission=user.permission>>2
            # device_write_permission = device_alive.device.permission >> 2

            # if user_read_permission < device_read_permission:
            #     devices_json['data'][device_alive.serial]['read_permission'] = False
            # elif user_read_permission >= device_read_permission:
            #     devices_json['data'][device_alive.serial]['read_permission'] = True
            #     devices_json['data'][device_alive.serial]['history'] = []
            #     for history in device_alive.device.query_historys:
            #         devices_json['data'][device_alive.serial]['history'].append(
            #             {'content': history.command_content, 'timestamp': history.query_timestamp, 'response': history.response})

            if user.permission < device_alive.device.permission:
                devices_json['data'][device_alive.serial]['write_permission'] = False
            elif device_alive.device.permission <= user.permission:
                latest_response = QueryHistory.query.with_parent(device_alive.device).filter(
                    QueryHistory.response != None).order_by(desc(QueryHistory.query_timestamp)).first()
                if latest_response:
                    devices_json['data'][device_alive.serial]['latest_response'] = latest_response.response
                    devices_json['data'][device_alive.serial]['latest_response_id'] = latest_response.id
                    devices_json['data'][device_alive.serial]['latest_response_command'] = latest_response.command_content
                    # print('latest_response_command-------------', file=sys.stderr)
                    # print(latest_response.command_content, file=sys.stderr)
                    # print('end-------------', file=sys.stderr)
                devices_json['data'][device_alive.serial]['write_permission'] = True

        else:
            db.session.delete(device_alive)
            db.session.commit()

    return jsonify(devices_json)

# 查询设备历史信息
@auth.login_required
@automation.route('/device_history', methods=['POST'])
def queryDeviceHistory():
    token = request.json.get('token')
    user = User.verify_auth_token(token)
    if not user:
        abort(405)
    devices_json = {'data': {}}
    for device in DeviceRegister.query.all():
        devices_json['data'].update({device.serial: {}})
        devices_json['data'][device.serial]['device_set'] = device.device_set
        devices_json['data'][device.serial]['device_type'] = device.device_type

        user_read_permission = user.permission % 4
        device_read_permission = device.permission % 4

        if user_read_permission < device_read_permission:
            devices_json['data'][device.serial]['read_permission'] = False
        elif user_read_permission >= device_read_permission:
            devices_json['data'][device.serial]['read_permission'] = True
            devices_json['data'][device.serial]['history'] = []
            for history in device.query_historys.order_by(desc(QueryHistory.query_timestamp)):
                # devices_json['data'][device.serial]['history'].append(
                #     {'command': history.command_content, 'timestamp': history.query_timestamp, 'response': history.response})
                if history.response:
                    devices_json['data'][device.serial]['history'].append(
                        {'id': history.id, 'command': history.command_content, 'timestamp': history.query_timestamp})

    return jsonify(devices_json)


@automation.route('/history_detail', methods=['POST'])
def deviceHistoryDetail():
    token = request.json.get('token')
    id = request.json.get('id')
    user = User.verify_auth_token(token)
    if(user is None):
        abort(405)
    if(id is None):
        abort(406)
    device_history = QueryHistory.query.filter_by(id=id).first()
    if not device_history:
        abort(412)
    resp = {'data': {'response': device_history.response,
                     'command': device_history.command_content}}
    # print('response-------------',file=sys.stderr)
    # print(device_history.response,file=sys.stderr)
    # print('-------------', file=sys.stderr)
    return jsonify(resp)


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
    # print('response-------------',file=sys.stderr)
    # print(response,file=sys.stderr)
    # print('-------------', file=sys.stderr)
    # historys = device.query_historys
    # 接收回应
    # if respone:
    #     for key, value in respone.items():
    #         history = historys.filter(id=key).first()
    #         if history:
    #             history.response = value
    #     db.session.commit()
    # # 发送请求
    # commands_json = {'data': {'command': []}}
    # for id, content in historys.filter_by(response == None).order_by(
    #         desc(query_timestamp)).with_entities(id,command_content):
    #     command_json = {'id': id, 'content': content}
    #     commands_json['data']['command'].append(command_json)
    # return jsonify(commands_json)

    # 接收回应
    # if respone:

    #     for key, value in respone.items():
    #         history = QueryHistory.query.with_parent(
    #             device).filter_by(id=key).first()
    #         if history and not history.response:
    #             history.response = value
    #     db.session.commit()
    if response:
        for item in response:
            history = QueryHistory.query.with_parent(
                device).filter_by(id=item['id']).first()
            if history and not history.response:
                history.response = item['response']
        db.session.commit()
    # 发送请求
    commands_json = {'data': {'commands': []}}
    for id, content in QueryHistory.query.with_parent(device).filter_by(response=None).order_by(
            desc(QueryHistory.query_timestamp)).with_entities(QueryHistory.id, QueryHistory.command_content):
        command_json = {'id': id, 'content': content}
        commands_json['data']['commands'].append(command_json)
    return jsonify(commands_json)


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
        # from app import db
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
            # print('auth.device_set-------------', file=sys.stderr)
            # print(auth_device.device_set, file=sys.stderr)
            auth_device.device_set = device_set
            # print('device_set-------------', file=sys.stderr)
            # print(device_set, file=sys.stderr)
            # print('-------------', file=sys.stderr)
            auth_device.permission = permission
            db.session.commit()
            token = auth_device.generate_auth_token()
            resp = jsonify(
                {'data': {'device_token': token.decode('ascii')}})
            return resp
        else:
            # 验证失败
            abort(412)
