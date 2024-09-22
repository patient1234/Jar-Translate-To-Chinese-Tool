import json
import os
import zipfile
import shutil
import re
import requests

only_en=1
auto=0
bak="默认"
from_en=0

def find_json_in_zip(z, json_file):
    for name in z.namelist():
        if name.endswith(json_file):
            return name
    return None
    
def combine(z,json1,json2):
    global from_en
    with z.open(json1) as f1:
        if from_en==0:
            d2=json.load(z.open(json2))
        else:
            d2=json.loads('{}')
        d1=json.load(f1)
        d1.update(d2)
        return d1

def process_json(z, json_path):
    global only_en
    global auto
    json_en=find_json_in_zip(z, 'en_us.json')
    if json_en:
        data=combine(z,json_en,json_path)
    else:
        with z.open(json_path) as f:
            data = json.load(f)
    
    # 修改JSON文件内容
    for key in data:
        if data[key]!='' and (only_en==0 or not bool(re.search('[\u4e00-\u9fa5]',data[key]))):
            if auto==1:
                new_value=requests.post("http://127.0.0.1:9911/translate",json={"q":data[key],"source":"en","target":"zh"}).json()['translatedText']
                print(f"\n[{data[key]}]\n'{new_value}'")
            else:
                new_value = input(f"\n[{data[key]}]\n>>")
            if new_value:
                data[key] = new_value
        while ": " in data[key] or ", " in data[key] :
            data[key]=data[key].replace(': ',':').replace(', ',',')
    # 返回修改后的数据
    return data

def process_jar(jar_path):
    global auto
    global from_en
    global bak
    temp_zip_path = jar_path + '.tmp'
    with zipfile.ZipFile(jar_path, 'r') as z, zipfile.ZipFile(temp_zip_path, 'w') as new_zip:
        
        # 查找zh_cn.json或en_us.json
        json_path = find_json_in_zip(z, 'zh_cn.json') or find_json_in_zip(z, 'en_us.json')
        
        if not json_path:
            print(f"在 {jar_path} 中没有找到zh_cn.json或en_us.json")
            new_zip.close()
            os.remove(temp_zip_path)
            return
        if 'en_us.json' in json_path:
            from_en=1
            json_path=json_path.replace("en_us.json","zh_cn.json")
        
        
        #确认开始
        if auto==0:
            comfirm=input("按下[y]开始处理:")
            while comfirm!='y':
                comfirm=input("按下[y]开始处理:")
        
        # 处理JSON文件
        updated_data = process_json(z, json_path)
        
        print("\n保存jar包...")
        
        # 将原始内容和新更新的json文件写入新jar文件
        for item in z.infolist():
            if item.filename != json_path:
                new_zip.writestr(item, z.read(item.filename))
            else:
                new_zip.writestr(item.filename+f'.副[{bak}]本', z.read(item.filename))
                new_zip.writestr(item.filename, json.dumps(updated_data,ensure_ascii=False).replace(', ',',\n\n').replace(': ',':\n').encode('utf-8'))
        
        if from_en==1:
            new_zip.writestr(json_path+f'.副[{bak}]本', z.read(find_json_in_zip(z, 'en_us.json')))
            new_zip.writestr(json_path, json.dumps(updated_data,ensure_ascii=False).replace(', ',',\n\n').replace(': ',':\n').encode('utf-8'))

    # 替换原始jar文件
    os.remove(jar_path)
    shutil.move(temp_zip_path, jar_path)

def scan_and_process_jars(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.jar'):
                jar_path = os.path.join(root, filename)
                print(f"\n开始处理{jar_path}...")
                
                process_jar(jar_path)
                
                print("处理完成")

# 替换以下路径为你的目标目录
print("\n开始寻找jar包...")

directory_to_scan = '.'

from_en_s=input("\n是否从英语文件开始翻译?(默认关闭)\n可配合自动翻译使用，无中文文件自动打开\n(y/n)>")
while from_en_s!='y' and from_en_s!='' and from_en_s!='n':
    from_en_s=input("\n是否从英语文件开始翻译?(默认关闭)\n可配合自动翻译使用，无中文文件自动打开\n(y/n)>")
if from_en_s=='y':
    from_en=1

auto_tips=""

auto_s=input("\n是否自动翻译?(默认关闭)\n(y/n)>")
while auto_s!='y' and auto_s!='' and auto_s!='n':
    auto_s=input("\n是否自动翻译?(默认关闭)\n(y/n)>")
if auto_s=='y':
    auto=1
    auto_tips="\n>>自动翻译已打开，建议设置此选项<<"

only_en_s=input(f"\n是否只翻译没有中文的内容?(默认打开){auto_tips}\n(y/n)>")
while only_en_s!='y' and only_en_s!='' and only_en_s!='n':
    only_en_s=input(f"\n是否只翻译没有中文的内容?(默认打开){auto_tips}\n(y/n)>")
if only_en_s=='n':
    only_en=0

bak=input(f"\n为副本取名，以便出错时替换{auto_tips}\n>")

scan_and_process_jars(directory_to_scan)
print("\n全部jar包处理完成")