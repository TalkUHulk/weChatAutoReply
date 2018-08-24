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