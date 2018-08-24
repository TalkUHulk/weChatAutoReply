# weChatAutoReply
Python+itchat+PyQt5实现的个人版微信--自动回复、防撤回、红包提醒等

一直在学习python，无意中看到了itchat这个包，感觉很有意思，简单实现了一个LowB版微信，给女朋友捉弄朋友用。其实没有什么难度，做的很简陋，这里做下记录。

[博客地址](https://blog.csdn.net/hyqwmxsh/article/details/82019571)

环境：
* python3.6

* PyQt5 5.11.2

* itchat 1.3.10

* wordcloud 1.5.0

* matplotlib 2.1.2

代码主要包括四个部分:

* [itchat_thread.py](https://github.com/Mister5ive/weChatAutoReply/blob/master/itchat_thread.py)负责itchat的相关处理

* [LogWindow.py](https://github.com/Mister5ive/weChatAutoReply/blob/master/LogWindow.py)是登陆窗口的代码

* [MainWindow.py](https://github.com/Mister5ive/weChatAutoReply/blob/master/MainWindow.py)是主界面的代码

* [AutoReplyWechat.py](https://github.com/Mister5ive/weChatAutoReply/blob/master/AutoReplyWechat.py)相当于一个调度中心，包括main函数


# 登录

这部分代码功能很简单，就是获取itchat的登陆二维码


## 代码：


from PyQt5.QtWidgets import QDialog,QLabel,QPushButton,QVBoxLayout,QApplication
from PyQt5 import QtGui
import math


LogDialogWidth = 300
LogDialogHeight = 500


class LogWindow(QDialog):

    def __init__(self):
        super(LogWindow, self).__init__()
        self.setStyle('qrc/dark.qss') # 设置样式
        self.initUI()

    def setStyle(self,_qssPath):
        with open(_qssPath,encoding='UTF-8') as file:
            str = file.read()
            qss = ''.join(str)
            self.setStyleSheet(qss)

    def initUI(self):

        self.mainButton = QPushButton(u'获取登录二维码',self)
        self.mainButton.setGeometry(int(math.ceil(LogDialogWidth / 2 - LogDialogWidth / 3 / 2)), int(math.ceil(LogDialogHeight / 10 * 8)),
            int(math.ceil(LogDialogWidth/3)), int(math.ceil(LogDialogHeight / 25)))

        self.labelQR = QLabel(self)
        self.labelQR.setFixedSize(280,280)
        self.labelQR.setAutoFillBackground(True)
        self.png = QtGui.QPixmap('qrc/welcome.png')
        self.labelQR.setPixmap(self.png)
        self.labelQR.setScaledContents(True)

        loginLayout = QVBoxLayout()
        loginLayout.addWidget(self.labelQR)
        loginLayout.addWidget(self.mainButton)
        self.setLayout(loginLayout)
        self.setWindowTitle(u'微信(by MisterGunner)')
        cx = (QApplication.desktop().width() - LogDialogWidth) / 2
        cy = (QApplication.desktop().height() - LogDialogHeight) / 2
        self.setGeometry(cx,cy,LogDialogWidth,LogDialogHeight)

    def setLabelPic(self,img):
        self.png = QtGui.QPixmap()
        self.png.loadFromData(img)
        self.labelQR.setPixmap(self.png)
        self.mainButton.setText('请扫码登录')



# itchat消息处理

这部分代码主要是微信消息的获取和后续处理，全部基于itchat来实现，后面别的有趣的功能也应该在这里增加。

from PyQt5.QtCore import QThread, pyqtSignal
import itchat
from itchat.content import NOTE,SHARING,TEXT,ATTACHMENT,RECORDING,VIDEO,VOICE,MAP,PICTURE,CARD
import time
import os
import re
import requests
import json


gFriendsInfo = None  # 朋友信息
gChatroomInfo = None  # 朋友信息

class ItchatThread(QThread):
    #signal
    LoginQR = pyqtSignal(list,name='LoginQR')
    Login = pyqtSignal(name='Login')
    LogExit = pyqtSignal(name='LogExit')
    recMessage = pyqtSignal(dict,bool,str ,name='recMessage')#{},isgroup,type
    noteMsg = pyqtSignal(str, int,name='noteMsg')  # 收到0红包,1撤回 name , isGroup

    FriendsInfo = pyqtSignal(list,name='FriendsInfo') # full friend contact get
    ChatroomInfo = pyqtSignal(list,name='ChatroomInfo') # full chatroom contact get
    autoReplyGroupList = [] # 自动回复的群名

    def __init__(self):
        super().__init__()
        self.msgHistory = []
        self.autoReply = False
        self.selfName = None
        self.contactInit = False # 通讯录读取，只需一次


    def msgClear(self):

        tm = time.time()
        ln = len(self.msgHistory)
        start = 0
        if ln:
            # delete msg that received 2 min ago. find last time satified condition
            for i in range(ln):
                if tm - self.msgHistory[i]['time'] >= 120:
                    start = i
                else:
                    break
            self.msgHistory = self.msgHistory[start:]




    def run(self):

        @itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING, PICTURE, RECORDING, ATTACHMENT, VIDEO, VOICE],
                             isGroupChat=False)
        def friend_rec_msg(msg):
            # save head img
            headImgPath = 'cache/'+msg['User']['NickName']+'.png'
            if os.path.exists(headImgPath) is False:
                itchat.get_head_img(userName=msg['User']['UserName'], picDir=headImgPath)

            if msg['Type'] == TEXT:  # TEXT
                #rMsg = {'time':time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg['CreateTime'])),'nickname':msg['User']['NickName'],'remarkname':msg['User']['RemarkName'], 'content': msg['Text']}
                rMsg = {'time': msg['CreateTime'], 'nickname': msg['User']['NickName'], 'remarkname': msg['User']['RemarkName'],
                        'content': msg['Text'],'fromusr':msg['FromUserName'],'selfusr':self.selfName}

                file_dir = 'cache/log/' + msg['User']['NickName'] + '/' + 'rec.log'

                if not os.path.isdir(os.path.split(file_dir )[0]):
                    os.makedirs(os.path.split(file_dir )[0])
                # save to log
                with open(file_dir, 'a+',encoding='utf-8' ) as file:
                    file.write(str(rMsg)+'\n')
                    file.flush()
                # record msg
                self.msgHistory.append(rMsg)
                # clear msg that received 2 min ago
                self.msgClear()
                # emit signal
                self.recMessage.emit(rMsg,False,'Text')

                # auto reply

                if self.autoReply:
                    itchat.send_msg(u'%s' % self.tuling(msg['Text']), msg['FromUserName'])


            elif msg['Type'] == NOTE:
                content =msg['Content']
                if re.search('红包',content):
                    #print('@@@@@@@@收到红包，请在手机端查收')
                    self.noteMsg.emit(msg['User']['RemarkName'],0)

                elif re.search('撤回',content):

                    n_nickname = msg['User']['NickName']
                    n_remarkname = msg['User']['RemarkName']
                    length = len(self.msgHistory)
                    index = 0
                    for i in reversed(self.msgHistory):
                        if self.msgHistory[length - index - 1]['nickname'] == n_nickname or self.msgHistory[length - index - 1]['remarkname'] == n_remarkname:
                            # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.msgHistory[length - index - 1]['time'])))
                            msg_recall = n_remarkname + '，撤回内容为：' + self.msgHistory[length - index - 1]['content']
                            # 撤回内容发给文件助手
                            itchat.send_msg(u"[%s]%s\n" %
                                            (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.msgHistory[length - index - 1]['time'])),msg_recall), 'filehelper')
                            #print(msg_recall)
                            break
                        index += 1

            elif msg['Type'] == PICTURE or  RECORDING or  ATTACHMENT or VIDEO:
                msg.download('recPic/'+msg.fileName)



        # file.write(u"[%s]收到群：%s 好友%s 的信息：%s\n" % (
        # time.strftime("%Y-%m-%d %H:%M:%S", time.local  time(msg['CreateTime'])), msg['User']['NickName'],
        # msg['ActualNickName'], msg['Text']))

        @itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING, PICTURE, RECORDING, ATTACHMENT, VIDEO, VOICE], isGroupChat=True)
        def group_rec_text(msg):
            file_dir = None
            if msg['Type'] == TEXT:  # TEXT

                # 自动回复
                if msg['User']['NickName'] in self.autoReplyGroupList:
                    itchat.send_msg(u'%s' % self.tuling(msg['Text']), msg['FromUserName'])


                rMsg = {'time': msg['CreateTime'], 'nickname': msg['User']['NickName'],
                        'remarkname': msg['User']['RemarkName'],
                        'content': msg['Text'], 'fromusr': msg['FromUserName'], 'selfusr': self.selfName}
                # 保存记录
                file_dir = 'cache/log/' + msg['User']['NickName'] + '/' + 'rec.log'

                if not os.path.isdir(os.path.split(file_dir)[0]):
                    os.makedirs(os.path.split(file_dir)[0])
                # save to log
                with open(file_dir, 'a+', encoding='utf-8') as file:
                    file.write(str(rMsg) + '\n')
                    file.flush()
                # emit signal
                self.recMessage.emit(rMsg, True, 'Text')

            elif msg['Type'] == NOTE:
                content = msg['Content']
                if re.search('红包', content):
                    #print('@@@@@@@@收到红包，请在手机端查收')
                    self.noteMsg.emit(msg['User']['NickName',0])
                elif re.search('撤回', content):
                    str2 = '{}{}'.format('群%s有人撤回消息\n'%msg['User']['NickName'],'聊天记录位置%s'%file_dir)
                    self.noteMsg.emit(str2,1)

            elif msg['Type'] == PICTURE or  RECORDING or  ATTACHMENT or VIDEO:
                msg.download('recPic/'+msg.fileName)




        # 启动itchat()
        itchat.auto_login(picDir= '',qrCallback=self.qrCallBack,loginCallback=self.loginCallback,exitCallback=None)
        itchat.dump_login_status(fileDir='cache/login/login_state.jw')
        self.selfName = itchat.get_friends(update=True)[0]['UserName']
        itchat.get_head_img(userName=itchat.get_friends(update=True)[0]['UserName'],picDir='cache/head/self.png')

        if self.contactInit == False:
            global gFriendsInfo
            global gChatroomInfo

            self.contactInit = True
            gFriendsInfo = itchat.get_friends(update=True)
            gChatroomInfo = itchat.get_chatrooms(update=True)
            self.FriendsInfo.emit(gFriendsInfo)
            self.ChatroomInfo.emit(gChatroomInfo)

        itchat.run()

    def qrCallBack(self,uuid, status, qrcode):
        self.LoginQR.emit([qrcode])

    def loginCallback(self):
        self.Login.emit()

    def exitCallback(self):
        pass

    def tuling(self, info):
        appkey = "e5ccc9c7c8834ec3b08940e290ff1559"
        url = "http://www.tuling123.com/openapi/api?key=%s&info=%s" % (appkey, info)
        req = requests.get(url)
        content = req.text
        data = json.loads(content)
        answer = data['text']
        return answer

    def group_id(self, name):
        df = itchat.search_chatrooms(name=name)
        return df[0]['UserName']

    # tuling auto reply
    def setAutoReply(self,on_off):
        self.autoReply = on_off

    # input send
    def sendMsg(self,sMsg):
        itchat.send_msg(u'%s' % sMsg[0], sMsg[1])

    def setAutoGroupList(self,_list):
        self.autoReplyGroupList = _list

    def get_head(self,_usrname):
        return itchat.get_head_img(userName = _usrname)

 ItchatThread继承QThread类，这里必须注意，itchat一定不能写在主线程里，会堵塞Qt部分，所以要单独开一个子线程，重写run函数。

run函数中，分别处理群和个人消息，关于itchat的api，具体可以参考官网说明。


### 个人消息部分：


调用get_head_img获取对方头像，并保存到本地。
如果是文本信息，聊天记录保存到本地文件log，然后存进一个list--msgHistory。上述list用来保存2min以内的聊天记录（2min以上无法撤回），用来实现防撤回功能。这里保存的信息主要包括创建时间，消息人昵称、备注、ID和内容。msgHistory因为只保存了最近2min的消息，所以要一直清理，否则会堆积太多内容。msgClear函数用来清理msgHistory，原理也很简单，当前时间跟最早的时间作差，大于120s即删除。
autoReply用来开启自动回复，通过Qt界面设置。自动回复调用了图灵机器人的API。
如果是NOTE类型的消息，检测其中的关键字，如果包含“红包”，发出一个信号，给Qt做相应处理；如果包含“撤回”字眼，则发送msgHistory的最近一条消息给自己的文件助手（这里只实现了发送撤回的最近一条消息）。
如果是图片消息，就下载到相应路径。
其他类型消息未做处理。
群消息处理类似。

最后调用auto_login，就可以获取二维码登录自己的微信了。这里注意，默认是调用电脑的看图软件打开二维码，或者可以在控制台利用字符显示。这里我想在qt界面显示，所以重写了qrCallBack，把图片数据发送给界面显示，loginCallBack负责通知界面登录状态。get_friends获取通讯录朋友信息，供界面使用。


# 主界面

这部分代码写的有点乱，其实没什么难度，主要是自己想实现的逻辑理清就ok了。


 ## 代码：
 

from PyQt5.QtWidgets import QApplication ,QWidget, QTabWidget,QTextBrowser,QTextEdit,QListWidgetItem,QCheckBox,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,QGridLayout,QListWidget,QMenu,QSystemTrayIcon,QAction
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtGui,Qt,QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
import matplotlib.pyplot as plt
import time
import numpy as np
import wordcloud
from PIL import Image
import re
import os



curTmpImg = None

class mainWindow(QTabWidget):

    sendMessage = pyqtSignal(list,name='sendMessage')
    selectFriend = pyqtSignal(list,name='selectFriend')
    selectAutoGroup = pyqtSignal(list, name='selectAutoGroup')
    imgHeadRequest = pyqtSignal(str,name='imgHeadRequest')
    friendAutoReply = pyqtSignal(int, name='friendAutoReply') # 朋友自动回复

    chatroom_num = 0 # 群个数
    selectGroupAutoReply = [] # 自动回复的群

    '''
    通讯录信息
    | NickName ,Sex,Province,City,signature,FromUserName|
    '''
    AllFriendsInfo = {}

    def __init__(self):
        super().__init__()

        self.focusID = 0
        self.setStyle('qrc/black.qss')
        self.createActions()
        self.createTrayIcon()
        self.init()

    def setStyle(self,_qssPath):
        with open(_qssPath,encoding='UTF-8') as file:
            str = file.read()
            qss = ''.join(str)
            self.setStyleSheet(qss)

    def init(self):
        self.tabChat = QWidget()
        self.tabContact = QWidget()
        self.tabSet = QWidget()

        self.addTab(self.tabChat, '微信')
        self.addTab(self.tabContact, '通讯录')
        self.addTab(self.tabSet, '设置')

        self.tabChatInit()
        self.setInit()
        self.contactInit()
        # self.leftLayout = QVBoxLayout()
        # self.rightLayout = QVBoxLayout()
        # mainLayout = QGridLayout()
        #
        # self.contact = QListWidget()
        # self.leftLayout.addWidget(self.contact)
        #
        # self.chatroom = QLineEdit()
        # self.chatroom.setText('This is ChatRoom')
        # self.chatlog = QLabel()
        # self.chatlog.setText('This is ChatLog')
        #
        # self.rightLayout.addWidget(self.chatlog)
        # self.rightLayout.addWidget(self.chatroom)
        #
        # mainLayout.addLayout(self.leftLayout, 0, 0, 1, 1)
        # mainLayout.addLayout(self.rightLayout, 0, 1, 1, 3)
        #
        # self.setLayout(mainLayout)
        self.setWindowTitle(self.tr('Wechat_alpha'))

    def addChatFriend(self,_NickName, _RemarkName):

        item = QListWidgetItem()
        str = _NickName
        if _RemarkName is not '':
            str+='['+_RemarkName+']'

        item.setText(str)

        self.listChatting.addItem(item)

    # 通讯录写入名单
    def fillContact(self, _fullContact):

        # self.AllFriendsInfo = _fullContact
        for each in  _fullContact:
            item = QListWidgetItem()
            str = each['RemarkName']
            if str is '':
                str = each['NickName']
            item.setText(str)
            self.contactList.addItem(item)
           # | NickName, Sex, Province, City, signature, FromUserName |
            self.AllFriendsInfo[str] = [each['NickName'],each['Sex'],each['Province'],each['City'],each['Signature'],each['UserName']]

    # 群自动回复----获得群名
    def setChatroomFill(self,_chatroom):

        self.chatroom_num = 0
        for each in _chatroom:
            self.chatroom_num += 1
            #self.chatroomInfo[each['NickName']] = each['UserName']
            item = QListWidgetItem()
            str = each['NickName']
            item.setText(str)
            self.allGroupList.addItem(item)
        #print(self.chatroomInfo)

    def contactInit(self):

        size  = self.size()

        self.contactList = QListWidget()
        self.contactList.setFixedSize(size.width() / 3,size.height())
        self.contactList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.contactList.itemClicked.connect(self.contactListClick)

        infoWidget = QWidget()
        infoWidget.setFixedSize(size.width() * 2 / 3,size.height())

        topLayout = QGridLayout()
        midLayout = QVBoxLayout()
        bottomLayout = QHBoxLayout()

        # top
        self.headLabel = QLabel()  # 头像
        self.headLabel.setFixedSize(150,150)
        self.headLabel.setScaledContents(True)

        self.signatureLabel = QLabel()  # 签名
        self.signatureLabel.setAlignment(QtCore.Qt.AlignVCenter)
        self.nickNameLabel = QLabel()  # 微信名
        self.nickNameLabel.setAlignment(QtCore.Qt.AlignVCenter)

        topLayout.addWidget(self.nickNameLabel,1,0,1,3)
        topLayout.addWidget(self.signatureLabel,2,0,1,3)
        topLayout.addWidget(self.headLabel,0,1,1,1)


        # mid
        self.remarkNameLabel = QLabel() # 备注
        self.cityLabel = QLabel()   # 城市

        midLayout.addWidget(self.remarkNameLabel)
        midLayout.addWidget(self.cityLabel)

        # bottom
        self.sendMsgBtn = QPushButton('发消息')

        bottomLayout.addWidget(self.sendMsgBtn)

        layout = QGridLayout()

        infoLayout = QVBoxLayout()
        infoLayout.addLayout(topLayout)
        infoLayout.addLayout(midLayout)
        infoLayout.addLayout(bottomLayout)
        infoLayout.addSpacing(10)

        infoWidget.setLayout(infoLayout)
        layout.addWidget(self.contactList,0,0,1,1)
        layout.addWidget(infoWidget,0,1,1,2)

        self.tabContact.setLayout(layout)


    def setInit(self):


        setTab = QTabWidget(self.tabSet)
        setTab.setTabPosition(QTabWidget.West) # 方向

        size = self.size()


        #############################自动回复################################
        btnAutoSet = QPushButton('应用')
        btnAutoCancel = QPushButton('取消')
        btnAutoCancel.clicked.connect(self.clearSelectList)
        btnAutoSet.clicked.connect(self.setSelectList)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(btnAutoSet)
        btnLayout.addSpacing(5)
        btnLayout.addWidget(btnAutoCancel)

        self.allGroupList = QListWidget()
        self.selectGroupList = QListWidget() # 选定自动回复的

        self.allGroupList.setFixedSize(size.width() * 3 / 7,size.height() * 2 / 3)
        self.selectGroupList.setFixedSize(size.width() * 3 / 7, size.height() * 2 / 3)

        self.allGroupList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.selectGroupList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.allGroupList.itemDoubleClicked.connect(self.aGroupDoubleClick)
        self.selectGroupList.itemDoubleClicked.connect(self.sGroupDoubleClick)


        self.setAutoLayout = QGridLayout()
        self.autoReplyFriend = QCheckBox('自动回复')
        self.autoReplyFriend.stateChanged.connect(self.setFriendAutoReply)

        self.setAutoLayout.setSpacing(10)

        self.setAutoLayout.addWidget(self.autoReplyFriend,0,0,1,1)
        self.setAutoLayout.addWidget(self.allGroupList, 1, 0, 10, 1)
        self.setAutoLayout.addWidget(self.selectGroupList, 1, 1, 10, 1)
        self.setAutoLayout.addLayout(btnLayout, 12, 1, 1, 1)

        # for each in self.ChatroomCheckBoxList:
        #     self.setAutoLayout.addWidget(each)
        tabAuto = QWidget()
        tabAuto.setLayout(self.setAutoLayout)
        #####################################################################
        # 其他
        self.showLabel = QLabel()
        self.showLabel.setScaledContents(True)
        self.showLabel.setFixedSize(size.width() * 2 / 3, size.width() * 2 / 3)
        sexDisttibutionBtn = QPushButton('性别分布')
        wordCouldBtn = QPushButton('签名词图')

        sexDisttibutionBtn.clicked.connect(self.calSex)
        wordCouldBtn.clicked.connect(self.generateWordCloud )

        layout = QGridLayout()

        layout.addWidget(self.showLabel,0,0,2,2)
        layout.addWidget(sexDisttibutionBtn, 2, 0, 1, 1)
        layout.addWidget(wordCouldBtn, 2, 1, 1, 1)
        tabFun = QWidget()
        tabFun.setLayout(layout)
        #####################################################################
        setTab.addTab(tabAuto,'自动回复')
        setTab.addTab(tabFun, '特色功能')
        # setTab.addTab('其他')


    def tabChatInit(self):

        size = self.size()

        layout = QGridLayout()
        self.listChatting = QListWidget()
        self.listChatting.setFixedSize(size.width() / 3, size.height())

        self.chatLog =QTextBrowser()
        self.chatLog.document().setMaximumBlockCount(1000)# 限制1000行
        self.chatLog.setFixedSize(size.width() * 2 / 3, size.height() * 2 / 3)

        self.textInput= QTextEdit()
        self.textInput.setFixedSize(size.width() * 2 / 3, size.height()  / 4)

        self.btnSend = QPushButton()
        self.btnSend.setText('发送')

        # 显示正在聊天的朋友
        self.chattingFri = QLabel('当前聊天朋友：_____')


        self.btnSend.clicked.connect(self.sendMsg)
        self.listChatting.itemClicked.connect(self.listClick)

        self.chatLog.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.chatLog.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        layout.addWidget(self.listChatting, 0, 0, 6, 1)
        layout.addWidget(self.chatLog, 0, 1, 3, 3)
        layout.addWidget(self.textInput, 3, 1, 2, 3)
        layout.addWidget(self.chattingFri, 5, 1, 1, 1)
        layout.addWidget(self.btnSend, 5, 3, 1, 1)

        self.tabChat.setLayout(layout)

    def showChatLog(self,_Msg):
        msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_Msg['time']))
        content = _Msg['content']

        if _Msg['fromusr'] == _Msg['selfusr']:
            self.chatLog.append(msg_time + '\n' + '我' + ':' + content + '\n')
        else:
            fromFriend = _Msg['remarkname']
            self.chatLog.append(msg_time + '\n' + fromFriend + ':'+ content+ '\n')

    def showSendChatLog(self,_Msg):
        msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        content = _Msg[0]
        self.chatLog.append(msg_time + '\n' + '我' + ':' + content + '\n')

    @pyqtSlot()
    def sendMsg(self):

        sMsg = self.textInput.toPlainText()
        if sMsg != '':
            self.textInput.clear()
            self.sendMessage.emit([sMsg])

    @pyqtSlot(QListWidgetItem)
    def listClick(self,item):
        self.selectFriend.emit([item.text()])

    @pyqtSlot(QListWidgetItem)
    def contactListClick(self,item):
        global curTmpImg
        # | NickName, Sex, Province, City, signature, FromUserName |
        cur = self.AllFriendsInfo[item.text()]
        self.imgHeadRequest.emit(cur[5])

        if curTmpImg:
            png = QtGui.QPixmap()
            png.loadFromData(curTmpImg)
            #png.scaled((50,50))
            self.headLabel.setPixmap(png)
            curTmpImg = None


        self.signatureLabel.setText('签名      '+''.join(cur[4]))  # 签名
        str = ''.join(cur[0])
        if cur[1] == 1:
            str +=' ♂'
        else:
            str+='  ♀'
        self.nickNameLabel.setText('微信      '+str)  # 微信名
        self.remarkNameLabel.setText('备注        '+item.text())  # 备注
        self.cityLabel.setText('地区      '+''.join(cur[2]+' '+cur[3]))  # 城市

    # add to select list
    @pyqtSlot(QListWidgetItem)
    def aGroupDoubleClick(self, item):
        select = item.text()
        item = QListWidgetItem()
        item.setText(select)
        self.selectGroupList.addItem(item)
        self.selectGroupAutoReply.append(select)

    # remove select item from list
    @pyqtSlot(QListWidgetItem)
    def sGroupDoubleClick(self, item):

        select = item.text()
        self.selectGroupList.removeItemWidget(self.selectGroupList.takeItem(self.selectGroupList.row(item)))
        self.selectGroupAutoReply.remove(select)

    @pyqtSlot(int)
    def setFriendAutoReply(self,_state):
        self.friendAutoReply.emit(_state)

    # 清空选定
    def clearSelectList(self):
        self.selectGroupList.clear()
        self.selectGroupAutoReply.clear()

    # 应用群自动回复
    def setSelectList(self):
        self.selectAutoGroup.emit(self.selectGroupAutoReply)



    # 获取头像
    def postUserHead(self,_img):
        global curTmpImg
        curTmpImg = _img
        #print(_img)

    # 更改当前聊天朋友名字显示
    def changeChattingFri(self,_str):
        self.chattingFri.setText('当前发送:'+_str[0])

    #  计算性别
    def calSex(self):

        # 设置全局字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        # 解决‘-’表现为方块的问题
        plt.rcParams['axes.unicode_minus'] = False

        female = 0
        total = len(self.AllFriendsInfo)
        for each in self.AllFriendsInfo.values():

            if each[1] is 2:
                female +=1
        male =  total - female

        data = {
              '男性(人)':(male,'#7199cf'),
              '女性(人)':(female,'#ffff10')
        }

        # 设置绘图对象的大小
        fig = plt.figure(figsize=(8, 8))

        sex = data.keys()
        values = [x[0] for x in data.values()]
        colors = [x[1] for x in data.values()]

        ax1 = fig.add_subplot(111)
        ax1.set_title('性别比例')

        labels = ['{}:{}'.format(city, value) for city, value in zip(sex, values)]

        # 设置饼图的凸出显示
        explode = [0, 0.1]

        # 画饼状图， 并且指定标签和对应的颜色
        # 指定阴影效果
        ax1.pie(values, labels=labels, colors=colors, explode=explode, shadow=True)

        pngPath ='cache/_sd/sd.jpg'
        plt.savefig(pngPath)
        # plt.show()
        if os.path.exists(pngPath):
            png = QtGui.QPixmap(pngPath)
            self.showLabel.setPixmap(png)

    # 生成词云
    def generateWordCloud(self):

        signature = [each[4] for each in self.AllFriendsInfo.values()]

        text = ','.join(signature)
        pattern = re.compile('<span.*?</span>')  # 匹配表情
        text = re.sub(repl='',string=text,pattern=pattern) # 删除表情

        coloring = np.array(Image.open("qrc/back.jpg"))
        my_wordcloud = wordcloud .WordCloud(background_color="white", max_words=2000,
                                 mask=coloring, max_font_size=60, random_state=42, scale=2,
                                 font_path="qrc/FZSTK.ttf").generate(text  )  # 生成词云。font_path="C:\Windows\Fonts\msyhl.ttc"指定字体，有些字不能解析中文，这种情况下会出现乱码。

        file_name_p = 'cache/word/wc.jpg'
        my_wordcloud.to_file(file_name_p)  # 保存图片

        if os.path.exists(file_name_p):
            png = QtGui.QPixmap(file_name_p)
            self.showLabel.setPixmap(png)

    def createTrayIcon(self):
        '''
        创建托盘图标，可以让程序最小化到windows托盘中运行
        :return:
        '''
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon('qrc/icon.png'))
        self.setWindowIcon(QIcon('qrc/icon.png'))
        self.trayIcon.show()

    def createActions(self):
        '''
        为托盘图标添加功能
        :return:
        '''
        self.restoreAction = QAction("来喽", self, triggered=self.showNormal)
        self.quitAction = QAction("告辞", self, triggered=QApplication.instance().quit)

    def iconActivated(self, reason):
        '''
        激活托盘功能
        :param reason:
        :return:
        '''
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showNormal()

    # 弹窗提醒
    def msgWarning(self,_message,_type):

        if _type == 0:
            QMessageBox.information(self,
                                "红包提醒",
                                _message,
                                QMessageBox.Yes )
        else:
            QMessageBox.information(self,
                                    "撤回提醒",
                                    _message,
                                    QMessageBox.Yes)

QTabWidget建了三个页，基本是模仿的微信PC端。

信息都是从itchatThread类获取的，然后就是几个类之间的互相通信。

聊天界面收到消息就会在左侧add朋友的消息，点击左侧的朋友，然后相应发给不同的人（未实现群聊天，只能收）。

通讯录基本跟原生微信一样，展示朋友，点击展示相应的information。没实现发送消息功能。

设置界面就是自动回复的开关了，checkbox是个人微信自动回复，下面是群消息自动回复，双击左侧选择，右侧是选定的，确认生效。

两个趣功能是在网上看到的，感觉很有意思，云词功能调用了wordcloud包，很好玩。我做了下简单改进在界面展示出来。



# 调度部分

这部分代码就算是指挥中心了，继承QThread，负责其他三个累的通信，很容易理解。

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSlot,QThread
from PyQt5.QtGui import QIcon
import sys
import LogWindow
import MainWindow
from itchat_thread import ItchatThread

LogDialogWidth = 300
LogDialogHeight = 500

class WeChat(QThread):

    def __init__(self):
        super(WeChat, self).__init__()
        self.initWechat()
        self.chattingFriends = [] # 左侧朋友
        self.isGroup = False
        self.mType = 0
        self.chattingNum = 0 # 左侧显示的个数
        self.chattingFriendsInfo = {}  # 左侧显示的朋友相关信息 名字+fromID
        self.curChatFriID = None  # 当前聊天朋友ID


    def initWechat(self):

        self.LogWin = LogWindow.LogWindow()
        self.MainWin = MainWindow.mainWindow()
        self.MainWin.sendMessage.connect(self.sendMsg)  # 发送输入消息
        self.MainWin.selectFriend.connect(self.changeChattingFriend) # 鼠标点击左侧朋友
        self.MainWin.imgHeadRequest.connect(self.userHeadRespond) # 相应头像请求
        self.MainWin.friendAutoReply.connect(self.setFriendAutoReply)
        self.LogWin.mainButton.clicked.connect(self.slotButtonGetQR)

        self.LogWin.show()

        self.LogWin.setWindowIcon(QIcon('0qrc/icon.png'))



        self.MainWin.hide()
        self.rTime = None


    @pyqtSlot()
    def slotButtonGetQR(self):
        self.itchatThread = ItchatThread()
        self.itchatThread.LoginQR.connect(self.slotGetQR)
        self.itchatThread.Login.connect(self.slotLoginOK)
        self.itchatThread.recMessage.connect(self.msgProc)
        self.itchatThread.FriendsInfo.connect(self.initContact)
        self.itchatThread.ChatroomInfo.connect(self.initSetChatroom)
        self.itchatThread.noteMsg.connect(self.noteMsg) # 红包

        self.itchatThread.start()

        self.MainWin.selectAutoGroup.connect(self.itchatThread.setAutoGroupList)  # 确认自动回复群

    @pyqtSlot(str)
    def slotGetUUID(self,uuid):
        self.uuid = uuid

    @pyqtSlot(list)
    def slotGetQR(self, qrcode):
        self.LogWin.setLabelPic(qrcode[0])

    @pyqtSlot()
    def slotLoginOK(self):
        self.LogWin.hide()
        self.MainWin.show()

    # msg process
    @pyqtSlot(dict,bool,str)
    def msgProc(self,msg,isGroup,msgType):

        add_friend = msg['nickname']
        if msg['remarkname'] is not '':
            add_friend += '（'+ msg['remarkname']+'）'
        # show msg
        self.MainWin.showChatLog(msg)
        # add chatting friend
        if add_friend not in self.chattingFriends:
            self.chattingFriends.append(add_friend)
            self.chattingNum += 1
            self.MainWin.addChatFriend(msg['nickname'], msg['remarkname'])
            str = msg['nickname'] +'['+ msg['remarkname']+']'
            self.chattingFriendsInfo[str]= msg['fromusr']
        #当前聊天朋友
        if self.curChatFriID == None:
            self.curChatFriID = msg['fromusr']
            self.MainWin.changeChattingFri([msg['remarkname']])


    @pyqtSlot(list)
    def sendMsg(self,sMsg):
        if self.curChatFriID:
            sMsg += [self.curChatFriID]
            self.itchatThread.sendMsg(sMsg)
            self.MainWin.showSendChatLog(sMsg)

    @pyqtSlot(list)
    def changeChattingFriend(self,_friendName):
        try:
            self.curChatFriID = self.chattingFriendsInfo[_friendName[0]]
            self.MainWin.changeChattingFri(_friendName)
        except Exception as e:
            self.MainWin.changeChattingFri(['暂不支持发送群消息'])
            self.curChatFriID = None

    @pyqtSlot(list)
    def initContact(self, _fullContact):

        self.MainWin.fillContact(_fullContact)

    @pyqtSlot(list)
    def initSetChatroom(self,_chatroom):
        self.MainWin.setChatroomFill(_chatroom)

    @pyqtSlot(str)
    def userHeadRespond(self,_usrname):
        self.MainWin.postUserHead(self.itchatThread.get_head(_usrname))

    @pyqtSlot(int)
    def setFriendAutoReply(self,_state):
        self.itchatThread.setAutoReply(_state)

    @pyqtSlot(str,int)
    def noteMsg(self,_message,_type):

        self.MainWin.msgWarning(_message,_type)

if __name__ == '__main__':

    app= QApplication(sys.argv)
    wechat = WeChat()
    sys.exit(app.exec_())

 


# 参考链接：

[https://www.jianshu.com/p/d042ff5f4457](https://www.jianshu.com/p/d042ff5f4457)

[https://blog.csdn.net/PoetMeng/article/details/73466557](https://blog.csdn.net/PoetMeng/article/details/73466557)

[https://blog.csdn.net/t7sfokzord1jaymsfk4/article/details/79094849](https://blog.csdn.net/t7sfokzord1jaymsfk4/article/details/79094849)

[https://itchat.readthedocs.io/zh/latest/](https://itchat.readthedocs.io/zh/latest/)





