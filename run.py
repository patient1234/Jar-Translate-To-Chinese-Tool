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
        
        # 将原始内容和新更新的json文件写入新jar文件
        for item in z.infolist():
            if item.filename != json_path:
                new_zip.writestr(item, z.read(item.filename))
            else:
                new_zip.writestr(item.filename+f'.{bak}.副本', z.read(item.filename))
                new_zip.writestr(item.filename, json.dumps(updated_data,ensure_ascii=False).replace(', ',',\n\n').replace(': ',':\n').encode('utf-8'))
        
        if not find_json_in_zip(new_zip, 'zh_cn.json'):
            new_zip.writestr(json_path+f'.{bak}.副本', z.read(find_json_in_zip(z, 'en_us.json')))
            new_zip.writestr(json_path, json.dumps(updated_data,ensure_ascii=False).replace(', ',',\n\n').replace(': ',':\n').encode('utf-8'))

    print("\n保存jar包...")
    # 替换原始jar文件
    os.remove(jar_path)
    shutil.move(temp_zip_path, jar_path)

def scan_and_process_jars(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.jar'):
                jar_path = os.path.join(root, filename)
                print(f"\n开始处理{jar_path}...")
                if select==1:
                    process_jar(jar_path)
                elif select==2:
                    0
                elif select==3:
                
                    temp_zip_path = jar_path + '.tmp'
                    with zipfile.ZipFile(jar_path, 'r') as z, zipfile.ZipFile(temp_zip_path, 'w') as new_zip:
                        for f in z.infolist():
                            if not f.filename.endswith(f".{bak}.副本"):
                                new_zip.writestr(f, z.read(f.filename))
                    
                    # 替换原始jar文件
                    print("\n保存jar包...")
                    os.remove(jar_path)
                    shutil.move(temp_zip_path, jar_path)
                    
                elif select==4:
                
                    temp_zip_path = jar_path + '.tmp'
                    with zipfile.ZipFile(jar_path, 'r') as z, zipfile.ZipFile(temp_zip_path, 'w') as new_zip:
                        for f in z.infolist():
                            if not f.filename.endswith("zh_cn.json"):
                                new_zip.writestr(f, z.read(f.filename))
                    
                    # 替换原始jar文件
                    print("\n保存jar包...")
                    os.remove(jar_path)
                    shutil.move(temp_zip_path, jar_path)
                    
                print("处理完成")

# 替换以下路径为你的目标目录
directory_to_scan = '.'

while True:

    select_t="\n1.开始翻译\n2.回退副本\n3.删除副本\n4.删除汉化\n5.退出\n>>"
    
    select=eval(input(select_t))
    while select<1 or select>5 or select%1!=0:
        select=eval(input(select_t))
    
    if select==1:
        
        from_en_t="\n是否从英语文件开始翻译?(默认关闭)\n可配合自动翻译使用，无中文文件自动打开\n(y/n)>"
        
        from_en_s=input(from_en_t)
        while from_en_s!='y' and from_en_s!='' and from_en_s!='n':
            from_en_s=input(from_en_t)
        if from_en_s=='y':
            from_en=1
        
        auto_tips=""
        
        auto_t="\n是否自动翻译?(默认关闭)\n(y/n)>"
        
        auto_s=input(auto_t)
        while auto_s!='y' and auto_s!='' and auto_s!='n':
            auto_s=input(auto_t)
        if auto_s=='y':
            auto=1
            auto_tips="\n>>自动翻译已打开，建议设置此选项<<"
        
        only_en_t=f"\n是否只翻译没有中文的内容?(默认打开){auto_tips}\n(y/n)>"
        
        only_en_s=input(only_en_t)
        while only_en_s!='y' and only_en_s!='' and only_en_s!='n':
            only_en_s=input(only_en_t)
        if only_en_s=='n':
            only_en=0
        
        bak=input(f"\n为副本取名，以便出错时替换{auto_tips}\n>")
        
        scan_and_process_jars(directory_to_scan)
    elif select==2:
        print("暂时没做，紧急修改了BUG")
    elif select==3:
        
        bak=input("\n输入要删除的副本名\n>")
        scan_and_process_jars(directory_to_scan)
        
    elif select==4:
        
        from_en_t="\n确认删除汉化文件?\n(y/n)>"
        
        delete_s=input(from_en_t)
        while delete_s!='y' and delete_s!='n':
            delete_s=input(delete_t)
        if delete_s=='y':
            scan_and_process_jars(directory_to_scan)
            
    elif select==5:
        break
