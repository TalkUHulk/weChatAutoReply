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