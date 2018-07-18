#encoding=utf-8

from PIL import Image
import datetime,time
import pytesseract
import requests
import re
from io import BytesIO
from bs4 import BeautifulSoup
import sys

start=time.clock()
reload(sys)
sys.setdefaultencoding('utf-8') 

#对图片进行二值化处理,threshold表示阈值
def binarizing(im,threshold):
    pixdata=im.load()
    w,h=im.size
    for j in range(h):
        for i in range(w):
            if pixdata[i,j]<threshold:
                pixdata[i,j]=0
            else:
                pixdata[i,j]=255
    im.save('binarizing.png')
    return im

#图片去噪
#######对于像素值>245的邻域像素，判别为属于背景色
#######如果一个像素上下左右4各像素值有超过两个
#######像素属于背景色，那么该像素就是目标点，否则就是噪声
def denoising(im):
    pixdata=im.load()
    w,h=im.size
    for j in range(1,(h-1)):
        for i in range(1,(w-1)):
            count=0
            if pixdata[i,j-1]>245:
                count=count+1
            if pixdata[i,j+1]>245:
                count=count+1
            if pixdata[i+1,j]>245:
                count=count+1
            if pixdata[i-1,j]>245:
                count=count+1
            if count>2:
                pixdata[i,j]=255
    im.save('noising.png')
    return im

#对图片进行预处理
def imgdeal(im):
    im=im.convert('L')#图片灰度图转换
    im.save('gray.png')
    im=denoising(im)#图片去噪
    im=binarizing(im,128)#图片二值化
    im.save('final.png')
    return im

#对图片进行验证码识别
def recognition(im):
    code = pytesseract.image_to_string(im)
    return code



#实现自动打码登录并爬取信息    
def login():
    n=10 #  n表示尝试登录校园网的次数
    fail=0 #  fail表示识别验证码失败的次数
    success=0 #  success表示识别验证码成功的次数
    while(n>0):
        post_url = 'http://jwxt.bupt.edu.cn/jwLoginAction.do'
        yzm_url = "http://jwxt.bupt.edu.cn/validateCodeAction.do?random="
        chengji_url = 'http://jwxt.bupt.edu.cn/gradeLnAllAction.do?type=ln&oper=qbinfo&lnxndm=2017-2018å­¦å¹´ç¬¬ä¸å­¦æ(ç§)(ä¸å­¦æ)'
        session = requests.session()  # 建立会话，保持会话信息，cookies
        r = session.get(post_url)
        cookies = r.headers['Set-Cookie']  # 获取cookies
        cookies = cookies.strip('; path=/')
        yam_headers={
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'Cookie': cookies,
        'Host': 'jwxt.bupt.edu.cn',
        'Referer':'http://jwxt.bupt.edu.cn/jwLoginAction.do',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
        }
        login_headers= {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '37',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': cookies,
        'Host': 'jwxt.bupt.edu.cn',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
        }
        chengji_headers = {
        'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN',
        'Connection': 'Keep-Alive',
        'Cookie': cookies,
        'Host': 'jwxt.bupt.edu.cn',
        'Refer': 'http://jwxt.bupt.edu.cn/gradeLnAllAction.do?type=ln&oper=fa',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
        }
        yamdata = session.get(yzm_url, headers=yam_headers)
        tempIm = BytesIO(yamdata.content)  # 将数据流放入tempIm以字节的形式       
        im = Image.open(tempIm)  # 转换为图片的形式
        im = im.resize((150,40))

        a=str(n)
        im.save(a+'yzm.png')
        #im_new=segment(im)
        im=imgdeal(Image.open(a+'yzm.png'))

        '''
        im1=im_new[0]
        a=str(n)
        im1.save(a+'im1.png')
        im1=imgdeal(Image.open('im1.png'))
        code1=recognition(im1)
        code1=code1.replace(' ','')
        print(code1)
        '''
        code = recognition(im)
        v_yzm = code.replace(' ','')#去掉空格
        login_data = {
        "zjh":'2016211594',
        "mm":'xu549761',
        "v_yzm":v_yzm,
        'type': 'sso'
        }
        login_headers['Cookie']=cookies
        d = session.post(post_url,data = login_data,headers = login_headers)
        e = session.get(chengji_url,headers = chengji_headers)
        info = r'<td align="center">\s*?(\S.*?)\s*?</td>\s*?'*6
        pattern = re.compile(info)
        info_result = pattern.findall(e.text)
        if(len(info_result)<1):#根据爬取信息的长度来判断是否成功登录校园网  
            fail=fail+1;       #fail用来记录失败的次数
            session.close()
        else:
            filename = r"grades.txt"
            gradesfile = open(filename, "w+")
            gradesfile.write(e.content)
            gradesfile.close()
            alist = list()
            success=success+1; #success用来记录成功的次数
            soup = BeautifulSoup(open(filename))
            filename2 = "result.txt"
            resfile = open(filename2,"w+")
            p = re.compile('<[^>]+>')
            for tag in soup.find_all("tr", "odd"):
                blist = list()
                for astring in tag.contents:
                    s = p.sub("", str(astring))
                    s = ' '.join(s.split())
                    blist.append(s) 
                    print(s)
                    resfile.write(s)
#                    print("----------------------------")
                print("*****************************************")
#                print(blist)
                alist.append(blist)
    #   result = tag.contents
           # print(blist)
#           resfile.write(result)
#           alist.append(str1.split())
            credit = 0
            summary = 0
            for a in alist:
#              print(a[9],a[13])
                if a[11] != '\xe4\xbb\xbb\xe9\x80\x89':
                    temp1 = float(re.match("[0-9]+.[0-9]",a[13]).group())
                    credit+=float(a[9])
                    summary+=float(a[9])*temp1
                else:
                    print(a[11])
            print("加权平均分")
            print(summary/credit)
            resfile.close()     
            break
        n=n-1;           
#        print('成功次数为%d'%success)
#        print('fail次数为%d'%fail)

if __name__ == "__main__": 
    login()
    end=time.clock()
#    print('耗费时间为%d'%(end-start))


#对图片进行切割处理
def segment(im):
    im_new=[]
    im0=im.crop((5,0,5+37,40))
    im_new.append(im0)
    im1=im.crop((40,0,40+37,40))
    im_new.append(im1)
    im2=im.crop((77,0,77+37.5,40))
    im_new.append(im2)
    im3=im.crop((114,0,114+37,40))
    im_new.append(im3)
    return im_new


