
from flask import Blueprint, render_template, redirect, request, jsonify
from flask.views import MethodView
from automation import automation
import sys


# class loginView(MethodView):
#     def get(self):
#         return render_template('login.html')

#     def post(self):
#         print('This is error output', file=sys.stderr)
#         print(request, file=sys.stderr)
#         response = jsonify({'code': 200, 'token': '123',
#                             'data': {'content': "login!"}})
#         # response.status_code = 200
#         return response


# class registerView(MethodView):
#     def get(self):
#         return jsonify({'code': 200, 'message': {'content': "register!"}})
        # return render_template('register.html')


# automation.add_url_rule('/login/', view_func=loginView.as_view('login'))
# automation.add_url_rule('/register/', view_func=registerView.as_view('register'))

