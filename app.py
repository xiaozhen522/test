# -*- coding:utf-8
import os
import json
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from fake_useragent import UserAgent
from xpinyin import Pinyin
import requests

import sys
import importlib
import jieba
importlib.reload(sys)
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal, LAParams

app = Flask(__name__)
basepath = os.path.dirname(__file__)  # 当前文件所在路径
upload_path = os.path.join(basepath, 'data')

def parse(read_path,save_path):
    fp = open(read_path, 'rb')  # 以二进制读模式打开
    # 用文件对象来创建一个pdf文档分析器
    praser = PDFParser(fp)
    # 创建一个PDF文档
    doc = PDFDocument()
    # 连接分析器 与文档对象
    praser.set_document(doc)
    doc.set_parser(praser)

    # 提供初始化密码
    # 如果没有密码 就创建一个空的字符串
    doc.initialize()

    # 检测文档是否提供txt转换，不提供就忽略
    if not doc.is_extractable:
        # raise PDFTextExtractionNotAllowed
        return '你提供的PDF文档不支持转换为txt文档'
    else:
        # 创建PDf 资源管理器 来管理共享资源
        rsrcmgr = PDFResourceManager()
        # 创建一个PDF设备对象
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        # 创建一个PDF解释器对象
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # 循环遍历列表，每次处理一个page的内容
        for page in doc.get_pages():  # doc.get_pages() 获取page列表
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout = device.get_result()
            # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等 想要获取文本就获得对象的text属性，
            for x in layout:
                if (isinstance(x, LTTextBoxHorizontal)):
                    with open(save_path, 'a', encoding='utf-8') as f:
                        results = x.get_text()
                        f.write(results + '\n')


def solve(save_path):
    # e10.3CalThreeKingdoms.py
    excludes = {}  # {"将军","却说","丞相"}
    txt = open(save_path, "r", encoding='utf-8').read()
    words = jieba.lcut(txt)
    counts = {}
    for word in words:
        if len(word) == 1:  # 排除单个字符的分词结果
            continue
        else:
            counts[word] = counts.get(word, 0) + 1
    for word in excludes:
        del (counts[word])
    items = list(counts.items())
    items.sort(key=lambda x: x[1], reverse=True)
    data=[]
    for i in range(len(items)):
        word, count = items[i]
        data.append("{:*<10}{:->5}".format(word, count))
    return data

def is_Chinese(word):
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def getdata():
    data = list(os.walk(upload_path))
    file_names = data[0][2]
    datas = {
        'file_names': file_names,
    }
    return datas


@app.route('/pdf/',methods=['GET','POST'])
def pdf():
    if request.method=='GET':
        return render_template('pdf.html')
    elif request.method=='POST':
        f=request.files['file_name']
        pdf_path_save=os.path.join(basepath,'static/pdf',secure_filename(f.filename))
        pdf_path_read=os.path.join(basepath,'static/pdf',secure_filename(f.filename[:-4]+'.txt'))
        pdf_path_read=os.path.abspath(pdf_path_read)
        pdf_path_save=os.path.abspath(pdf_path_save)
        f.save(pdf_path_save)
        parse(pdf_path_save,pdf_path_read)
        msg=solve(pdf_path_read)
        os.remove(pdf_path_read)
        os.remove(pdf_path_save)
        return render_template('pdf.html',msg=msg)


@app.route('/')
def home_page():
    return render_template('home_page.html')


@app.route('/Yso/')
def search():
    return render_template('Yso.html')


@app.route('/Yso/search/', methods=['GET'])
def search_get():
    try:
        if request.method == 'GET':
            keyword = request.args.get('keyword')
            data_path = os.path.join(basepath,'static','data.csv')
            data_path = os.path.abspath(data_path)
            with open(data_path, 'r', encoding='utf-8')as f:
                readlines = f.readlines()
            for i in readlines:
                data = i.split(',')
                if keyword in data[0]:
                    print(data[1])
                    context = {
                        'message': data[1]
                    }
                    return render_template('Yso.html', **context)

    except:
        return render_template('404.html')

@app.route('/upload/', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files['file_name']
        upload_path1 = os.path.join(basepath, 'data', secure_filename(f.filename))
        # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
        upload_path2 = os.path.abspath(upload_path1)  # 将路径转换为绝对路径
        f.save(upload_path2)
        return redirect(url_for('index'))


@app.route('/download/', methods=['GET'])
def download():
    try:
        if request.method == 'GET':
            down = request.args.get('down')
            delete = request.args.get('delete')
            file = request.args.get('file')
            if delete == '删除':
                upload_path1 = os.path.join(basepath, 'data', file)
                upload_path2 = os.path.abspath(upload_path1)  # 将路径转换为绝对路径
                os.remove(upload_path2)
                return redirect(url_for('index'))
            if down == '下载':
                directory = os.path.join(basepath, 'data')
                directory = os.path.abspath(directory)
                return send_from_directory(directory, file, as_attachment=True)
    except:
        return render_template('404.html')


@app.route('/weather/')
def weather_serch():
    return render_template('weather.html')


@app.route('/weather/city/', methods=['POST'])
def weather():
    if request.method == 'POST':
        city = request.form['city']
        if is_Chinese(city):
            city = Pinyin().get_pinyin(city, '')
        header = {
            'user_agent': UserAgent().random
        }
        url = 'http://api.openweathermap.org/data/2.5/weather?q=%s&mode=json&units=metric&lang=zh_cn&APPID=6a67ed641c0fda8b69715c43518b6996' % city
        reponse = requests.get(url, headers=header).text
        context = json.loads(reponse)
        context['city'] = city
    return render_template('city.html', **context)


@app.route('/index/')
def index():
    context = getdata()
    return render_template('index.html', **context)


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'mima0000':
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='密码错误，请重试')
    elif request.method == 'GET':
        return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
