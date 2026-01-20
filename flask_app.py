#!/usr/bin/env python
# coding: utf-8

import flask
from datetime import datetime

app = flask.Flask(__name__)

# 首页
@app.route("/")
def index():
    return """
    <!doctype html>
    <html>
      <body>
        <h1>Python学习平台</h1>
        <p>欢迎使用Python学习平台！</p>
        <ul>
          <li><a href="/hello/World">打招呼</a></li>
          <li><a href="/calculate/10/5">计算器</a></li>
          <li><a href="/form">提交表单</a></li>
        </ul>
        <p>当前时间: {}</p>
      </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M"))

# 问候页面
@app.route("/hello/<name>")
def hello(name):
    return flask.render_template_string("""
    <!doctype html>
    <html>
      <body>
        <p>你好，<b>{{name}}</b>！</p>
        <p>今天是 {{date}}。</p>
        <a href="/">返回首页</a>
      </body>
    </html>
    """, name=name, date=datetime.now().strftime("%Y年%m月%d日"))

# 计算器
@app.route("/calculate/<int:a>/<int:b>")
def calculate(a, b):
    results = {
        "a": a,
        "b": b,
        "sum": a + b,
        "product": a * b,
        "difference": a - b,
        "quotient": a / b if b != 0 else "未定义"
    }
    
    html = """
    <!doctype html>
    <html>
      <body>
        <h1>计算结果</h1>
        <p>{} + {} = {}</p>
        <p>{} × {} = {}</p>
        <p>{} - {} = {}</p>
        <p>{} ÷ {} = {}</p>
        <a href="/">返回首页</a>
      </body>
    </html>
    """.format(a, b, results["sum"], a, b, results["product"], 
               a, b, results["difference"], a, b, results["quotient"])
    
    return html

# 表单页面
@app.route("/form")
def show_form():
    return """
    <!doctype html>
    <html>
      <body>
        <h1>提交信息</h1>
        <form action="/submit" method="post">
          姓名: <input name="name"/><br/>
          邮箱: <input name="email"/><br/>
          <input type="submit" value="提交"/>
        </form>
        <a href="/">返回首页</a>
      </body>
    </html>
    """

# 表单处理
@app.route("/submit", methods=["POST"])
def submit_form():
    name = flask.request.form.get("name", "")
    email = flask.request.form.get("email", "")
    
    return flask.render_template_string("""
    <!doctype html>
    <html>
      <body>
        <h1>提交成功！</h1>
        <p>姓名: {{name}}</p>
        <p>邮箱: {{email}}</p>
        <p>提交时间: {{time}}</p>
        <a href="/">返回首页</a>
      </body>
    </html>
    """, name=name, email=email, time=datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    print("Flask应用启动中...")
    print("访问 http://127.0.0.1:5000/")
    app.run(debug=True)