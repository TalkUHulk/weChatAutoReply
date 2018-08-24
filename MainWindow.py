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

        # count = -1
#         # for count, line in enumerate(open(thefilepath, 'rU')):
#         #     pass
#         # count += 1
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
