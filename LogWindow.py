from PyQt5.QtWidgets import QDialog,QLabel,QPushButton,QVBoxLayout,QApplication
from PyQt5 import QtGui
import math


LogDialogWidth = 300
LogDialogHeight = 500


class LogWindow(QDialog):

    def __init__(self):
        super(LogWindow, self).__init__()
        self.setStyle('qrc/dark.qss')
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



