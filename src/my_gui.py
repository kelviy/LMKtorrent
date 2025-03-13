import threading
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog
    
class Ui_MainWindow(object):
    peer = ""
    def __init__(self):
        self.last_height = 0
        self.wdgt_list =[]
    
    def setupUi(self, MainWindow):
        
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1032, 635)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(100, 80, 871, 271))
        self.scrollArea.setMouseTracking(False)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 848, 1222))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame.setMinimumSize(QtCore.QSize(0, 1200))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        
        self.cmb_fileList = QtWidgets.QComboBox(self.centralwidget)
        self.cmb_fileList.setGeometry(QtCore.QRect(410, 380, 211, 41))
        self.cmb_fileList.setObjectName("cmb_fileList")
        
        self.btn_Download = QtWidgets.QPushButton(self.centralwidget)
        self.btn_Download.setGeometry(QtCore.QRect(460, 450, 121, 41))
        self.btn_Download.setObjectName("btn_Download")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1032, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        self.btn_Download.clicked.connect(self.clicked)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        #self.lbl_filename.setText(_translate("MainWindow", "TextLabel"))
        #self.lbl_numSeed.setText(_translate("MainWindow", "TextLabel"))
        #self.lbl_numLeachers.setText(_translate("MainWindow", "TextLabel"))
        self.btn_Download.setText(_translate("MainWindow", "PushButton"))
    
        
    
    def update_file_list(self, file_list):
        bool = False


        if self.cmb_fileList.count() == 0:
            
            for i in file_list.keys():
                self.cmb_fileList.addItem(i)
            self.cmb_fileList.addItem("All files")
        else:

            for i in file_list.keys():
                

                for j in range(self.cmb_fileList.count()):
                    if i == self.cmb_fileList.itemText(j):
                        bool =True
                if bool == False:

                    self.cmb_fileList.addItem(i)
                    bool = False
    def add_file_item(self, file_name):
        # Create a new widget for the file
        wdgt_file = QtWidgets.QWidget()
        wdgt_file.setAutoFillBackground(True)
        wdgt_file.setObjectName("wdgt_file")
        wdgt_file.setStyleSheet("background-color: rgb(255, 255, 255);")

        # Create and configure the progress bar
        pgr_file = QtWidgets.QProgressBar(wdgt_file)
        pgr_file.setGeometry(QtCore.QRect(300, 15, 121, 23))
        pgr_file.setStyleSheet("")
        pgr_file.setProperty("value", 0)
        pgr_file.setInvertedAppearance(False)
        pgr_file.setObjectName("pgr_file")

        # Create and configure the filename label
        lbl_filename = QtWidgets.QLabel(wdgt_file)
        lbl_filename.setGeometry(QtCore.QRect(30, 15, 55, 16))
        lbl_filename.setObjectName("lbl_filename")
        lbl_filename.setText(file_name)

        # Create and configure the number of seeders label
        lbl_numSeed = QtWidgets.QLabel(wdgt_file)
        lbl_numSeed.setGeometry(QtCore.QRect(580, 15, 55, 16))
        lbl_numSeed.setObjectName("lbl_numSeed")

        # Create and configure the number of leechers label
        lbl_numLeachers = QtWidgets.QLabel(wdgt_file)
        lbl_numLeachers.setGeometry(QtCore.QRect(680, 15, 55, 16))
        lbl_numLeachers.setObjectName("lbl_numLeachers")

        # Create and configure the seeder image label
        lbl_seedImg = QtWidgets.QLabel(wdgt_file)
        lbl_seedImg.setGeometry(QtCore.QRect(550, 10, 21, 20))
        lbl_seedImg.setText("")
        lbl_seedImg.setPixmap(QtGui.QPixmap("../../CSC3002F - Assignment 1/LMKtorrent/src/assets/frame0/image_5.png"))
        lbl_seedImg.setScaledContents(True)
        lbl_seedImg.setObjectName("lbl_seedImg")

        # Create and configure the leecher image label
        lbl_LeachImg = QtWidgets.QLabel(wdgt_file)
        lbl_LeachImg.setGeometry(QtCore.QRect(650, 15, 21, 20))
        lbl_LeachImg.setText("")
        lbl_LeachImg.setPixmap(QtGui.QPixmap("../../CSC3002F - Assignment 1/LMKtorrent/src/assets/frame0/image_6.png"))
        lbl_LeachImg.setScaledContents(True)
        lbl_LeachImg.setObjectName("lbl_LeachImg")

        # Add the file widget to the vertical layout
        self.verticalLayout.addWidget(wdgt_file)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        #threading.Thread(target=self.getProgress,args=(pgr_file,)).start()
    def setPeer(self,peer):
        self.peer = peer
    def clicked(self):
        file_name = self.cmb_fileList.currentText()
        self.add_file_item(file_name)
        self.peer.download()
    def getProgress(self,pgr):
        while True:
            
            pgr.setValue(pgr.value() + 1)
            
            time.sleep(1)

            if pgr.value() == 100:
                break
