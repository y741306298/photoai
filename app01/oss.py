from django.shortcuts import render,HttpResponse
import io

import oss2
from PIL import Image


# Create your views here.
def upload_file(oss_file_name, image, local_file_path):
    """
    上传文件
    :param oss_file_name: oss 上传文件名
    :param image: 图片文件
    :param local_file_path: 本地图片路径
    :return: oss文件访问路径
    """

    # oss 配置信息
    access_key_id = "access-key-id"
    access_key_secret = "access-key-secret"
    bucket_name = "bucket-name"
    region = "oss-cn-beijing"
    cdn_host = "http://img-dev"

    # oss 授权
    auth = oss2.Auth(access_key_id, access_key_secret)
    # oss bucket
    endpoint = "https://" + region + ".aliyuncs.com"
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    # 将本地文件转为二进制流
    if local_file_path != "":
        blob = read2byte(local_file_path)
    else:
        blob = image2byte(image)
    # oss 开始上传
    bucket.put_object(oss_file_name, blob)

    oss_url = cdn_host + "/" + oss_file_name
    return oss_url


def read2byte(path):
    """
    文件转为二进制
    :param path: 图片路径
    :return: 二进制数据
    """
    with open(path, "rb") as f:
        byte_data = f.read()
    return byte_data


def image2byte(image):
    """
    图片转byte
    :param image: 必须是PIL格式
    :return: 二进制
    """
    # 创建一个字节流管道
    img_bytes = io.BytesIO()
    # 把PNG格式转换成的四通道转成RGB的三通道，然后再保存成jpg格式
    image = image.convert("RGB")
    # 将图片数据存入字节流管道， format可以按照具体文件的格式填写
    image.save(img_bytes, format="JPEG")
    # 从字节流管道中获取二进制
    image_bytes = img_bytes.getvalue()
    return image_bytes


def byte2image(byte_data):
    """
    byte 转为图片
    :param byte_data: 二进制
    :return:  图片
    """
    image = Image.open(io.BytesIO(byte_data))
    return image