import io
import threading
from datetime import datetime
from urllib.request import Request

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from sanic import Sanic
from sanic.response import raw, json, text, HTTPResponse

app = Sanic("STapi")
url = "http://127.0.0.1:8000/"


# 领域降噪
def calculate_noise_count(img_obj, w, h, width, height):
    count = 0
    for _w_ in [w - 1, w, w + 1]:
        for _h_ in [h - 1, h, h + 1]:
            if _w_ > width - 1:
                continue
            if _h_ > height - 1:
                continue
            if _w_ == w and _h_ == h:
                continue
            if img_obj[_w_, _h_] < 230:  # 这里因为是灰度图像，设置小于230为非白色
                count += 1
    return count


# 高斯滤波+锐化+领域降噪的线稿提取方案
def img_ege_get(byte: bytes):
    time = datetime.now()
    byte_stream = io.BytesIO(byte)
    im1 = Image.open(byte_stream).convert('L')  # 灰度图
    im = im1.filter(ImageFilter.GaussianBlur(radius=0.75))  # 高斯模糊 75%

    a = np.asarray(im).astype('float')

    depth = 10.
    grad = np.gradient(a)
    grad_x, grad_y = grad
    grad_x = grad_x * depth / 100.
    grad_y = grad_y * depth / 100.
    # 梯度向量计算
    A = np.sqrt(grad_x ** 2 + grad_y ** 2 + 1.)
    uni_x = grad_x / A
    uni_y = grad_y / A
    uni_z = 1. / A
    vec_el = np.pi / 2.2
    vec_az = np.pi / 4.
    dx = np.cos(vec_el) * np.cos(vec_az)
    dy = np.cos(vec_el) * np.sin(vec_az)
    dz = np.sin(vec_el)

    b = 255 * (dx * uni_x + dy * uni_y + dz * uni_z)
    b = b.clip(0, 255)  # 极值处理
    im2 = Image.fromarray(b.astype('uint8'))
    im2 = im2.filter(ImageFilter.SHARPEN)
    weight, height = im2.size
    # 降噪
    pim = im2.load()
    map(row_noise, [(pim, height, weight, w,) for w in range(weight)])
    imgByteArray = io.BytesIO()
    im2.save(imgByteArray, format='png')
    imgByteArray = imgByteArray.getvalue()
    print(datetime.now() - time)
    return imgByteArray


def row_noise(pim, height, weight, w):
    for h in range(height):
        if calculate_noise_count(pim, w, h, weight, height) < 4:
            pim[w, h] = 255


# 颜色减淡+线性减淡+轮廓滤镜的线稿提取方案
def img_filter(byte: bytes):
    byte_stream = io.BytesIO(byte)
    im1 = Image.open(byte_stream).convert('L')
    img1 = im1.filter(ImageFilter.CONTOUR)
    img2 = img1.copy()
    img2 = ImageOps.invert(img2)

    def loop(x):
        for y in range(height):
            a[x, y] = min(int(a[x, y] * 255 / (256 - b[x, y])), 255)

    for i in range(2):
        img2 = img2.filter(ImageFilter.BLUR)
    width, height = img1.size
    a = img1.load()
    b = img2.load()
    task = [threading.Thread(target=loop, args=(i,)) for i in range(width)]
    for i in task:
        i.start()
    for i in task:
        i.join()
    imgByteArray = io.BytesIO()
    img1.save(imgByteArray, format='png')
    imgByteArray = imgByteArray.getvalue()
    return imgByteArray


@app.middleware("request")
def cors_middle_req(request: Request):
    """路由需要启用OPTIONS方法"""
    if request.method.lower() == 'options':
        allow_headers = [
            'Authorization',
            'content-type'
        ]
        headers = {
            'Access-Control-Allow-Methods':
                ', '.join(request.app.router.get_supported_methods(request.path)),
            'Access-Control-Max-Age': '86400',
            'Access-Control-Allow-Headers': ', '.join(allow_headers),
        }
        return HTTPResponse('', headers=headers)


@app.middleware("response")
def cors_middle_res(request: Request, response: HTTPResponse):
    """跨域处理"""
    allow_origin = '*'
    response.headers.update(
        {
            'Access-Control-Allow-Origin': allow_origin,
        }
    )


'''
下面为一个简易的服务器端，可快速部署图像处理服务
'''

@app.route("/hello", methods=['GET', 'POST'])
async def he(request):
    return text("hello world")



@app.route("/img", methods=['GET', 'POST'])
async def test(request):
    try:
        pic = request.files['file'][0].body
    except:
        pic = request.body
    return raw(
        img_ege_get(pic), content_type='image/png'
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8008, workers=4)
