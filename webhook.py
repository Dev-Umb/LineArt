# webhook.py
import os


def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    os.system('git add .')
    os.system('git commit -m "merge"')
    os.system('git pull origin master')
    print('git pull finish')
    return [b'Hello, webhook!']


# start_webkook.py
#!/usr/bin/env python
# coding=utf-8
from wsgiref.simple_server import make_server
# 导入我们自己编写的application函数:
# 创建一个服务器，IP地址为空，端口是8000，处理函数是application:
httpd = make_server('', 8000, application)
print('Serving HTTP on port 8000...')
# 开始监听HTTP请求:
httpd.serve_forever()