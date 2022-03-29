import hmac
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
# github中webhooks的secret
github_secret = 'imfFTJq4'


def encryption(data):
    key = github_secret.encode('utf-8')
    obj = hmac.new(key, msg=data, digestmod='sha1')
    return obj.hexdigest()


# webhook.py
import os


@app.route('/hook', methods=['POST'])
def post_data():
    """
    github加密是将post提交的data和WebHooks的secret通过hmac的sha1加密，放到HTTP headers的
    X-Hub-Signature参数中
    """
    post_data = request.data
    token = encryption(post_data)
    # 认证签名是否有效
    signature = request.headers.get('X-Hub-Signature', '').split('=')[-1]
    if signature != token:
        return "token认证无效", 401
    # 运行shell脚本，更新代码
    os.system('sh ../deploy.sh')
    return jsonify({"status": 200})


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000)
