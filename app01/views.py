import uuid
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from Real_ESRGAN.inference_realesrgan import enhancement
import os
import threading
import tkinter as tk
import tkinter.filedialog as tkf
#import tkinter.font as tf
from pathlib import Path
from tkinter import END
import oss2
import time
import datetime
import pymysql

# 用户账号密码，第三部说明的Access
# 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
# 获取的AccessKey
auth = oss2.Auth('LTAI5tF4xVdSBSNQF3w7oLg3', '1rxXJjS62tKoEwVAtTQstOLjeqEhTv')
# 这个是需要用特定的地址，不同地域的服务器地址不同，不要弄错了
endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'
# 你的项目名称，类似于不同的项目上传的图片前缀url不同
# 因为我用的是ajax传到后端方法接受的是b字节文件，需要如下配置。 阿里云oss支持更多的方式，下面有链接可以自己根据自己的需求去写
bucket = oss2.Bucket(auth, endpoint, 'qy-comyany')  # 项目名称

# 这个是上传图片后阿里云返回的uri需要拼接下面这个url才可以访问，根据自己情况去写这步
base_file_url = 'https://qycompany-bucket.oss-cn-hangzhou.aliyuncs.com/'

max_task = 3

now_task = 0

# 打开数据库连接
db = pymysql.connect(host='112.124.2.120',
                     user='root',
                     password='Ysd@950421',
                     database='photo_ai',
                     )
cursor = db.cursor()
sql = "SELECT * FROM photo_ai_batch WHERE state = 0 AND sever_id = 1 ORDER BY create_date LIMIT 0,1"
sql1 = "UPDATE photo_ai_batch SET state = %s,start_date =%s WHERE id = %s"
# sql2 = "INSERT INTO photoai_info(user_id,picture_id,picture_name,picture_url,preview_url,pictureview_url,width,height,suffix,state,create_date,modified_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
sql2 = "UPDATE photoai_info SET picture_url=%s,state =%s,modified_date = %s WHERE batch_id = %s"
sql3 = "UPDATE photo_ai_batch SET state = %s,end_date =%s WHERE id = %s"
sql4 = "SELECT * FROM photo_ai_batch WHERE id = %s"
sql5 = "UPDATE sever_info SET now_task = %s ,callback_date = %s WHERE id = 1"
second = 10  #延时变量



# Create your views here.
def index(request):
    return render(request,'index.html')


# 进度条
# 当无法确定待上传的数据长度时，total_bytes的值为None。
def percentage(consumed_bytes, total_bytes):
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        print('\r{0}% '.format(rate), end='')


def update_fil_file(filepath,suffix):
    """
    ！ 上传单张图片
    :param file: b字节文件
    :return: 若成功返回图片路径，若不成功返回空
    """
    # 生成文件编号，如果文件名重复的话在oss中会覆盖之前的文件
    number = uuid.uuid4()
    # 生成文件名
    base_fil_name = "photoai/"+str(number) + suffix
    # 生成外网访问的文件路径

    # file_name = base_file_url + base_fil_name
    # 这个是阿里提供的SDK方法 bucket是调用的4.1中配置的变量名
    res = bucket.put_object_from_file(base_fil_name, filepath)

    # 如果上传状态是200 代表成功 返回文件外网访问路径
    # 下面代码根据自己的需求写
    return base_fil_name;
    # if res.status == 200:
    #     return url;
    # else:
    #     return False

def download_file(url,filename):
    local_name = "D:/template/"+filename;
    res = bucket.get_object_to_file(url, local_name)
    if res.status == 200:
        return True
    else:
        return False

@csrf_exempt
def test(request):
    if request.method == 'POST':
        # 获取前端ajax传的文件 使用read()读取b字节文件
        file = request.FILES.get('file').read()
        # 通过上面封装的方法把文件上传
        file_url = update_fil_file(file)
        print(file_url)
        # 这里没有做判断验证只是测试代码 根据自己的需求需要判断
        return HttpResponse('上传成功')

@csrf_exempt
def enhancementStart(oriPath,optPath,suffix,scale,id):
    print("enhancement start")
    # oriPath = "D:/template/2.jpeg";
    # optPath ="D:/template";
    # suffix = ".jpeg";
    # scale =2.2;
    d =".!button2";
    command=enhance(oriPath, optPath, suffix,scale, d,id);
    # button_enhance.place(x=70, y=100)


def openfile(path):
    path.delete(0, END)
    path.insert(0, tkf.askopenfilename(filetypes=[('图片', '.png .jpg .jpeg .tif')]))


def savefiles(path):
    path.delete(0, END)
    path.insert(0, tkf.askdirectory())


def enhance(path1, path2, ext, entry_enhance_scale, button,id):
    print(path1)
    print(path2)
    print(ext)
    print(entry_enhance_scale)
    print(button)
    if not Path(path2).is_dir():
        os.makedirs(path2)
    if not Path(path1).is_file():
        tk.messagebox.showerror('错误', '图片不存在！')
        return
    if path2 == "":
        tk.messagebox.showerror('错误', '生成路径为空！')
        return
    if not str(entry_enhance_scale).replace('.', '', 1).isdigit():
        tk.messagebox.showerror('错误', "参数不是数字！")
        return
    if float(entry_enhance_scale) < 0:
        tk.messagebox.showerror('错误', "倍数不能小于0！")
        return
    if entry_enhance_scale == "":
        tk.messagebox.showerror('错误', "参数不能为空！")
        return

    enhanceThread(path1, path2, ext, entry_enhance_scale, button,id).start()
    InfoThreadEnhance(button).start()

class enhanceThread(threading.Thread):

    def __init__(self, path1, path2, ext, scale, button,id):
        threading.Thread.__init__(self)
        self.path1 = path1
        self.path2 = path2 + '/'
        self.ext = ext
        self.scale = scale
        self.button = button
        self.id = id

    def run(self):
        global now_task;
        print("now_task", now_task)
        message = enhancement(self.path1, self.path2, self.ext, float(self.scale))
        print("message", message)
        a1,a2,a3 = message.split("/",2);
        result = update_fil_file(message,self.ext);
        cursor.execute(sql4, self.id)
        db.commit();
        nowBatchs = cursor.fetchall();
        current_time = datetime.datetime.now();
        print("nowBatchs",nowBatchs)
        for nowBatch in nowBatchs:
            # val2 = (nowBatch[1], nowBatch[3], a3, result,nowBatch[6],nowBatch[7], nowBatch[19],
            #         nowBatch[20], nowBatch[17], 1, current_time, current_time);
            val2 = (result,"1", current_time,self.id);
            cursor.execute(sql2, val2);
            db.commit();
        end_time = datetime.datetime.now();
        val3 = (2,end_time,self.id);
        cursor.execute(sql3,val3)
        db.commit();
        os.remove(self.path1);
        os.remove(message);
        now_task = now_task - 1;
        now_time = datetime.datetime.now();
        callval = (now_task, now_time);
        cursor.execute(sql5, callval);
        print("now_task",now_task)

class InfoThreadEnhance(threading.Thread):
    def __init__(self, button):
        threading.Thread.__init__(self)
        self.button = button

    def run(self):
        # self.button.place(x=70, y=100)
        # self.button['text'] = "图像增强中……"
        print("run",self)

while 60:    #循环输出
    time.sleep(60
               )  #设置延时
    times = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  #设置时间格式
    try:
        cursor.execute(sql);
        db.commit();
        # 提交到数据库执行
        results = cursor.fetchall();
        if len(results)>0:
            for row in results:
                now_task = now_task + 1;
                # 加入回执回报
                now_time = datetime.datetime.now();
                callval = (now_task, now_time);
                cursor.execute(sql5, callval)
                db.commit();

                id = row[0]
                user_id = row[1]
                picture_id = row[3]
                picture_name = row[4]
                picture_url = row[5]
                width = row[10]
                height = row[11]
                suffix = "."+row[17]
                scale = row[18]
                new_width = row[19]
                new_height = row[20]
                # print("id=%s,picture_name=%s,picture_url=%s,width=%s,height=%s,suffix=%s"%(id,picture_name, picture_url, width, height, suffix));
                start_time = datetime.datetime.now();
                val = (1,start_time,id)
                cursor.execute(sql1,val)
                db.commit();
                a,b,c,d = picture_url.split("/",3);
                pictureUrl = d.split("?")[0];
                # print("pictureUrl=",pictureUrl);
                res = download_file(pictureUrl,picture_name);
                if res:
                    oripath = "D:/template/"+picture_name;
                    optpath = "D:/template";
                    enhancementStart(oripath,optpath,suffix,scale,id);
        else:
            # 加入回执回报
            now_time = datetime.datetime.now();
            callval = (now_task, now_time);
            cursor.execute(sql5, callval)
            db.commit();
    except:
        db.rollback()
        db.close()
    print(times)



