__author__ = 'wwxiang'

import sys
import logging
import os
import tkinter
import tkinter.messagebox
import urllib.parse
import urllib.request
import xml.etree.ElementTree
import xml.dom.minidom
import shutil
import zipfile
import time
import suds.client
import threading
import traceback


# 临时解决依赖模块问题，加入系统模块路径
# sys.path.append("./suds-jurko-0.4.1.jurko.3")
# import suds



#日志信息
handler = logging.StreamHandler(sys.stderr)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logger = logging.getLogger('suds.transport.http')
logger.setLevel(logging.DEBUG), handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
class OutgoingFilter(logging.Filter):
    def filter(self, record):
        return record.msg.startswith('sending:')
handler.addFilter(OutgoingFilter())

#全局信息
G_LOG = []

#工作目录
workPath = os.getcwd()
downloadPath = workPath + os.path.sep + 'download'
webappmkdir = downloadPath + os.path.sep + 'webapp'
errorLog = downloadPath + os.path.sep + 'errorLog'
error_log = errorLog + os.path.sep + 'error.txt'
if os.path.isdir(downloadPath):
    shutil.rmtree(downloadPath)
os.mkdir(downloadPath)
os.mkdir(webappmkdir)
os.mkdir(errorLog)
G_LOG.append('mkdir:'+downloadPath + '\n')
G_LOG.append('mkdir:'+webappmkdir + '\n')
G_LOG.append('mkdir:'+errorLog + '\n')

#获取当前系统时间
theTime = time.strftime('%Y-%m-%d-%H-%M',time.localtime(time.time()))
G_LOG.append('当前系统时间：'+theTime + '\n')

#SOAP 源
#SOAP http://wb.mobile.sh.ctripcorp.com/hybridpublish/service.asmx?wsdl
#SOAP SEND
bodyXML = '''
  <?xml version="1.0"?>
  <Request>
    <Header UserID="CtripTest" SessionID="0d21swty1o22qatzzrke4vip" RequestID="1c34b903-e1f5-4c6d-bbb4-d1bcd0a664e3" RequestType="Operation.HybridPublishService.HybridPackageQueryRQ" ClientIP="172.16.150.76" AsyncRequest="false" Timeout="0" MessagePriority="3" AssemblyVersion="1.0.2.5" RequestBodySize="0" SerializeMode="Xml" RouteStep="1" />
    <HybridPackageQueryRQ>
      <EnvCode>1</EnvCode>
      <ClientVersion>{0}</ClientVersion>
    </HybridPackageQueryRQ>
  </Request>'''

#格式化 XML
def formatXML(SOAPXML):
    return ' '.join(SOAPXML.split())
    pass
# 获取TEXT 节点
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
    pass
#在后台处理下载
class StageDownloadHandler(threading.Thread):
    def __init__(self,address,zip_all):
        threading.Thread.__init__(self)
        self.__add = address
        self.__zip = zip_all
        pass
    def run(self):
        #显示下载进度
        def downSize(count, blockSize, totalSize):
            if not count:
                print('connection opened')
            if totalSize <0:
                print('远程主机，返回的下载总量为负数')
                print('read %d blocks' % count)
            else:
                print ('download '+self.__add+' %d KB, totalsize: %d KB' % (count*blockSize/1024.0,totalSize/1024.0))
            pass
        #远程主机，返回的头信息是否与此匹配，来判断是否是zip文件 application/x-zip-compressed
        remoteHostTest = urllib.request.urlopen(self.__add)
        if not remoteHostTest.headers['Content-Type'] == 'application/x-zip-compressed':
            return
        print('request '+ self.__add +' wait ....')
        G_LOG.append('DOWNLOAD '+ self.__add +'\n')
        try:
            zip_add = downloadPath+os.path.sep+self.__add+'.zip'
            self.__zip.append(zip_add)
            urllib.request.urlretrieve(self.__add,zip_add,reporthook=downSize)
        except ValueError:
            print(self.__add)
            raise ValueError('Error: download url bad'+self.__add)
            G_LOG.append('Error: download url bad'+self.__add+'\n')
        pass
    pass
#主类
class ClientApp:
    def __init__(self,width=600,height=150,stage=None):
        self.root = tkinter.Tk()
        self.root.geometry('{0}x{1}'.format(width,height))
        self.root.title('downloadZIP')
        label = tkinter.Label(self.root,text='download zip the current directory mkdir webapp and download')
        label.pack(padx=5,pady=5,anchor='w')
        self.stage = stage
        pass
    #渲染UI界面
    def renderui(self):
        messURL = tkinter.Label(self.root,text='SOAP URL: http://wb.mobile.sh.ctripcorp.com/hybridpublish/service.asmx?wsdl')
        messURL.pack(padx=5,anchor='w')
        parmas = tkinter.Label(self.root,text='send SOAP version:')
        parmas.pack(padx=5,anchor='w')
        self.getVersion = tkinter.Entry(self.root,width=500)
        self.getVersion.pack(padx=5,pady=5)
        # getSendDate = tkinter.Text(self.root,width=400,height=10)
        # getSendDate.pack(padx=5,pady=5,anchor='w')
        # getSendDate.focus_set()
        # Tscrollbar = tkinter.Scrollbar(self.root)
        # Tscrollbar.pack(side='right',fill='y')
        # Tscrollbar.config(command=getSendDate.yview)
        # getSendDate.config(yscrollcommand=Tscrollbar.set)
        openSOAP = tkinter.Button(self.root,text='exec',width=30,height=1)
        openSOAP.bind('<Button-1>',self.sendRquest)
        openSOAP.pack(padx=5,pady=5,anchor='w')
        pass
    #打包webpp
    def unpackwebapp(self):
        print('unpack webapp path :'+ webappmkdir)
        G_LOG.append('unpack webapp path :'+ webappmkdir+'\n')
        unpack_zip = zipfile.ZipFile('webapp.zip','w')
        for dirpath, dirnames, filenames in os.walk(webappmkdir):
            for filename in filenames:
                unpack_zip_path = os.path.join('webapp'+os.path.sep+ dirpath.split('webapp')[1],filename)
                print('wait :' + filename)
                unpack_zip.write(os.path.join(dirpath,filename),unpack_zip_path)
                print('success :' + filename)
                G_LOG.append('SUCCESS ' + unpack_zip_path + '\n')
        print('done')
        unpack_zip.close()
        webLogFile = open(errorLog+os.path.sep+'web-log-'+theTime+'.txt','w',encoding='utf-8')
        webLogFile.write(' '.join(G_LOG))
        webLogFile.close()
        tkinter.messagebox.showinfo('SUCCESS MESSAGE','DONE')
        pass
    #检校md5
    def calibrationMD5(self):

        pass
    #解析 XML
    def handlerparseXML(self,xmlData):
        SOAP_ZIP_XML_PATH = downloadPath + os.path.sep +'SOAP_zip.xml'
        with open(SOAP_ZIP_XML_PATH,'w',encoding='utf-8') as xml_f:
            xml_f.write(xmlData)
            xml_f.close()
        SOAP_DIC = {}
        SOAP_XML_DOM = xml.dom.minidom.parseString(xmlData)
        SOAP_XMl_HEAD = SOAP_XML_DOM.getElementsByTagName('Header')
        SOAP_DIC['ServerIP'] = SOAP_XMl_HEAD[0].getAttribute('ServerIP')
        SOAP_DIC['ResultCode'] = SOAP_XMl_HEAD[0].getAttribute('ResultCode')
        SOAP_DIC['ResultMsg'] = SOAP_XMl_HEAD[0].getAttribute('ResultMsg')
        SOAP_DIC['ResultNo'] = SOAP_XMl_HEAD[0].getAttribute('ResultNo')
        if not len(SOAP_DIC['ServerIP']):
            print('ERROR: SOAP REQUEST BAD')
            print(SOAP_DIC['ResultNo'])
            print(SOAP_DIC['ResultMsg'])
            G_LOG.append('ERROR: SOAP REQUEST BAD \n')
            G_LOG.append('THE ERRPR MESSAGE '+SOAP_DIC['ResultMsg']+'\n')
            return
        SOAP_XML_Result = SOAP_XML_DOM.getElementsByTagName('Result')
        SOAP_XML_HybridPackage = SOAP_XML_DOM.getElementsByTagName('HybridPackage')
        downloadALL = []
        for node in SOAP_XML_HybridPackage:
            for node_value in node.childNodes:
                node_text = getText(node_value.childNodes)
                if len(node_text):
                    downloadALL.append(node_text)
        count = 0
        zip_all = []
        for zip_down in downloadALL:
            count += 1
            down = StageDownloadHandler(zip_down,zip_all)
            down.start()
            if len(downloadALL) == count:
                down.join()
        for zip_app in zip_all:
            zip_file = zipfile.ZipFile(zip_app,'r')
            zip_name_file = zip_file.namelist()
            zip_info_file = zip_file.infolist()
            for name in zip_name_file:
                G_LOG.append('UN ZIP '+name + '\n')
            zip_file.extractall(path = webappmkdir)
            zip_file.close()
        self.unpackwebapp()
        pass
    #向远程SOAP webservice 发起请求
    def sendRquest(self,event):
        SOAPURL = 'http://wb.mobile.sh.ctripcorp.com/hybridpublish/service.asmx?wsdl'
        SOAPSENDDATA = self.getVersion.get()
        SOAPSENDDATA = bodyXML.format(SOAPSENDDATA)
        SOAPSENDDATA = formatXML(SOAPSENDDATA)
        try:
            webservice = suds.client.Client(SOAPURL)
            SOAPRESPONSE = webservice.service.Request(SOAPSENDDATA)
            print('SOAP SUCCESS:'+SOAPURL)
            G_LOG.append('SOAP URL :' +SOAPURL + '\n')
            G_LOG.append('SOAP SEND DATA :' +SOAPSENDDATA + '\n' )
            self.handlerparseXML(SOAPRESPONSE)
            print(SOAPRESPONSE)
        except urllib.error.URLError:
            self.error_outinput()
            print('SOAP REQUEST BAD')
        pass
    #循环UI
    def loop(self):
        self.root.resizable(False,False)
        self.renderui()
        self.root.mainloop()
        pass
    #错误信息输出
    def error_outinput(self):
        error_f = open(error_log,'a')
        traceback.print_exc(file=error_f)
        error_f.close()
        pass
    pass

app = ClientApp()
app.loop()