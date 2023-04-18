# -*- coding: utf-8 -*-
import sys, random, os, time, gc
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.task.Task import Task
from panda3d.core import WindowProperties
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from panda3d.core import WindowProperties
from panda3d.core import loadPrcFileData
import numpy as np
import scipy
import scipy.ndimage
import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2
from panda3d.core import WindowProperties
from Sensor import Sensor
from ProjectorCtl import *
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
import threading
import socketserver
import framework.tickmodule


#panda3d.core 中的配置文件
loadPrcFileData('', 'show-frame-rate-meter false')
loadPrcFileData('', 'win-size 1920 1080')  # 用于全屏
# loadPrcFileData('', 'win-size 720 960')  # 用于全屏
loadPrcFileData('', 'window-title 奇境沙盒')
loadPrcFileData('', 'undecorated true')  # 无框



class XY(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # UpdateThread().start()
        #开启服务器，新的线程
        # UDPServerThread().start()

        self.DefalutScale = .05
        self.DefalutFont = loader.loadFont('./data/font/思源黑体R.ttf', pointSize=10)
        self.cam.setPos((0, 0, 100))
        self.cam.setHpr((0, -90, 0))
        base.setBackgroundColor(0, 0, 0)

        self.Dev = 0
        base.disableMouse()
        self.DefaultStableData = np.load("./data/DefaultData.npy")

        props = WindowProperties()
        props.setSize(1920, 1080)
        props.setFullscreen(True)
        base.win.requestProperties(props)

        width = 1.78 * 2
        hight = 2

        self.MainPage = DirectFrame(pos=(-1.78, 0, 1.91),
                                    frameSize=(0, 0, 0, 0),
                                    frameColor=(0, 0, 0, 0),
                                    #主界面的视频
                                    image="./data/texture/MainPageMovie.mp4",
                                    image_scale=(width / 1.7, 0, hight / 1.04),
                                    image_pos=(width / 2, 0, -hight / 2)
                                    )

        self.Topics = NodePath("Menu")

        self.MainPage.attachNewNode(self.Topics.node())

        self.TopicNodeActor = NodePath("TopicNode")
        base.render.attachNewNode(self.TopicNodeActor.node())
        self.TopicNode3D = NodePath("TopicNode")
        base.render.attachNewNode(self.TopicNode3D.node())
        self.TopicNode2D = NodePath("TopicNode")
        base.render2d.getChild(0).attachNewNode(self.TopicNode2D.node())
        self.TopicNode1D = NodePath("TopicNode")
        base.render2d.getChild(0).getChild(9).attachNewNode(self.TopicNode1D.node())

        # 绑定事件
        for bt in base.buttonThrowers:
            bt.node().setSpecificFlag(False)
            bt.node().setButtonDownEvent("ButtonDownEvent")
            bt.node().setButtonUpEvent("ButtonUpEvent")
            bt.node().setButtonRepeatEvent("ButtonRepeatEvent")
        self.accept("ButtonDownEvent", self.ButtonDownEvent)
        self.accept("ButtonUpEvent", self.ButtonUpEvent)
        self.accept("ButtonRepeatEvent", self.ButtonRepeatEvent)

        self.Text_C = OnscreenText(text="Fankid出品",
                                   style=2,
                                   fg=(1, 1, 1, 1),
                                   scale=self.DefalutScale,
                                   parent=aspect2d,
                                   pos=(-1.77, -0.99),
                                   align=TextNode.ALeft,
                                   font=self.DefalutFont)

        self.InputText = OnscreenText(text="",
                                      style=2,
                                      fg=(1, 1, 1, 1),
                                      scale=self.DefalutScale * 3,
                                      parent=aspect2d,
                                      pos=(0, 0),
                                      align=TextNode.ALeft,
                                      font=self.DefalutFont)

        self.Title = OnscreenText(text="奇境沙盒",
                                  style=1,
                                  pos=(1.43, -0.2 - 1.05),
                                  fg=(1, 1, 1, 1),
                                  font=self.DefalutFont,
                                  scale=0.15,
                                  parent=self.MainPage,
                                  align=TextNode.ALeft)

        self.HintTitle = OnscreenText(text="FantaBox",
                                      style=1,
                                      pos=(1.625, -1.36),
                                      fg=(1, 1, 1, 1),
                                      font=self.DefalutFont,
                                      scale=0.05,
                                      parent=self.MainPage,
                                      align=TextNode.ALeft)

        self.UI_C = self.Text_C
        self.UI_C_XY = [0.01, 0.01]
        self.Sensor = Sensor(n_frames=3, gauss_sigma=3.5)
        self.Text_C.hide()
        self.InitializeTopic()
        self.UpdateConfig()
        self.CurrentPage = "MainPage"

        self.Code = []
        self.CodeDuration = time.time()

        self.taskMgr.add(self.KeyCode, "KeyCode")

        self.MapList = [
            'cubehelix_r', 'brg_r', 'hsv_r', 'jet',
            'viridis', 'plasma', 'Paired', 'Set1', 'tab10',
            'flag', 'terrain', 'gist_stern', 'brg', 'rainbow', 'gist_ncar',
            'gnuplot2', 'viridis_r', 'plasma_r', 'Pastel1_r', 'Accent_r',
            'Dark2_r', 'Set1_r', 'Set2_r', 'Set3_r', 'tab20_r',
            'tab20c_r', 'flag_r', 'prism_r', 'ocean_r', 'gist_earth_r',
            'terrain_r', 'CMRmap_r', 'jet_r', 'nipy_spectral_r', 'gist_ncar_r',
            'Pastel1', 'Dark2', 'Set3', 'tab20b', 'tab20c',
            'prism', 'gist_earth', 'CMRmap', 'cubehelix', 'hsv',
        ]

        plt.cm.get_cmap("gist_rainbow")

        with open("./config/debug.txt", "a") as f:
            f.write("1    %s\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        try:
            pStart()
        except:
            pass

        self.ChooseQuit = 0
        self.QuitTime = time.time()
        self.PushTime = time.time()
        with open("./config/debug.txt", "a") as f:
            f.write("2    %s\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        time.sleep(10)
        # self.BaseLandOpen()
        # self.IslandOpen()
        # self.ClibOpen()
        # self.FarmOpen()
        self.RegisterColorMap()

    # self.Text_C.setText("成都凡童科技出品")

    def GoToCoor(self, Actor, TargetCoor):
        # 向坐标移动，只移动一个目标方向的距离，返回1个坐标Coor，
        # 需要多次调用,并且只有在StartCoor!=TargetCoor的时候才调用
        PosX = int(Actor.getPos()[0] / (1920 / self.SandWidth))
        PosY = int(Actor.getPos()[1] / (1080 / self.SandHight))
        StartCoor = [PosX, PosY]
        if StartCoor[0] < TargetCoor[0]:
            X = StartCoor[0] + 1
        elif StartCoor[0] > TargetCoor[0]:
            X = StartCoor[0] - 1
        else:
            X = StartCoor[0]
        if StartCoor[1] < TargetCoor[1]:
            Y = StartCoor[1] + 1
        elif StartCoor[1] > TargetCoor[1]:
            Y = StartCoor[1] - 1
        else:
            Y = StartCoor[1]
        MoveOnX = [X, StartCoor[1]]
        MoveOnY = [StartCoor[0], Y]
        if StartCoor[0] == TargetCoor[0]:
            PlanCoors = [MoveOnY]
        elif StartCoor[1] == TargetCoor[1]:
            PlanCoors = [MoveOnX]
        else:
            PlanCoors = [MoveOnX, MoveOnY]
        PlanCoors = self.CheckCoorsInRange(PlanCoors)
        ChoosePlanIndx = random.randint(0, len(PlanCoors) - 1)
        NextCoor = PlanCoors[ChoosePlanIndx]
        if NextCoor[0] > PosX:
            # 向左
            NextHpr = (-90, 180, 90)
        elif NextCoor[0] < PosX:
            # 向右
            NextHpr = (-90, 0, 90)
        elif NextCoor[1] > PosY:
            # 向下
            NextHpr = (0, 180, 90)
        elif NextCoor[1] < PosY:
            # 向上
            NextHpr = (0, 0, 90)
        else:
            NextHpr = (-90, 180, 90)
        return NextCoor, NextHpr

    def ButtonRepeatEvent(self, bt):
        if self.MainPage.isHidden() == False:
            self.CoorCheckLogic(bt)

    def ButtonDownEvent(self, bt):
        if self.MainPage.isHidden() == False:
            self.CoorCheckLogic(bt)

    def ButtonUpEvent(self, bt):

        if self.CurrentPage == "Quit":
            if bt == "enter":
                self.OnExitbyKey(1)
            if bt in ["escape", "backspace"]:
                self.OnExitbyKey(0)

            #######################################################################

        if self.CurrentPage == "MainPage":
            if bt in ["1", "2", "3", "4", "5", "6", "7"] and self.Code == []:
                if bt == "1":
                    self.ShaderLandSoloOpen()
                if bt == "2":
                    self.BaseLandOpen()
                if bt == "3":
                    self.ShaderLandOpen()
                if time.time() - self.PushTime > 10:
                    if bt == "4":
                        self.IslandOpen()
                    elif bt == "5":
                        self.LandOpen()
                    self.PushTime = time.time()
                if bt == "6":
                    self.FootballOpen()
                if bt == "7":
                    self.OceanOpen()

            if bt == "*":
                self.CodeDuration = time.time()
                self.Code.append("*")
            if "*" in self.Code:
                if bt != "*":
                    self.Code.append(bt)
            if bt in ["escape", "backspace"] and time.time() - self.QuitTime > 1:
                self.Dialog = YesNoDialog(dialogName="YesNoCancelDialog",
                                          text="是否关闭",
                                          text_font=self.DefalutFont,
                                          command=self.OnExitbyMouse,
                                          )
                self.MainPage.hide()
                self.CurrentPage = "Quit"
                self.QuitTime = time.time()

    def OnExitbyMouse(self, arg):
        if arg:
            pStop()
            os.system("shutdown -s -t 0")
            sys.exit()

    # else:
    # self.Dialog.cleanup()
    # self.MainPage.show()
    # self.CurrentPage="MainPage"

#退出直接关机
    def OnExitbyKey(self, arg):
        if arg:
            pStop()
            os.system("shutdown -s -t 0")
            sys.exit()

    # else:
    # self.Dialog.cleanup()
    # self.MainPage.show()
    # self.CurrentPage="MainPage"

#键盘控制
    def KeyCode(self, task):
        if self.CurrentPage == "MainPage":
            if time.time() - self.CodeDuration < 3:
                # print(self.Code)
                Code = "".join(self.Code)
                self.InputText.setText(Code)
                pass
            else:
                Code = "".join(self.Code)
                if Code == "*999":
                    self.ClibOpen()
                    self.CurrentPage = "Clib"
                if Code == "*000":
                    sys.exit()

                if Code == "*101":
                    self.ShaderLandSoloOpen()
                if Code == "*102":
                    self.ShaderLandOpen()
                if Code == "*103":
                    self.BaseLandOpen()
                if Code == "*104":
                    self.LandOpen()
                if Code == "*105":
                    self.IslandOpen()
                if Code == "*106":
                    self.FootballOpen()
                if Code == "*107":
                    self.OceanOpen()

                if Code == "*201":
                    self.PandaLifeOpen()
                if Code == "*202":
                    self.BoatFloatOpen()
                if Code == "*203":
                    self.SanxingduiOpen()
                if Code == "*204":
                    self.StoneOpen()
                if Code == "*205":
                    self.HongJunOpen()
                if Code == "*206":
                    self.FarmOpen()
                if Code == "*207":
                    self.LearnDayTimeOpen()

                if Code == "*301":
                    self.LearnShapeOpen()
                if Code == "*302":
                    self.NetMapOpen()
                if Code == "*303":
                    self.NetCustomOpen()
                if Code == "*304":
                    self.NetDrawOpen()
                self.Code = []
                self.InputText.setText("")

        return task.cont

#修改界面按钮
    def InitializeTopic(self):
        hight = 4
        width = 15

        self.BaseLandButton = DirectButton(pos=(1.8, 0, -1.8 + (0.2 * 0)),
                                           command=self.BaseLandOpen,
                                           frameSize=(0, width, 0, hight),
                                           text="沙绘艺术",
                                           text_font=self.DefalutFont,
                                           text_scale=2,
                                           text_align=TextNode.ACenter,
                                           text_pos=(width / 2, hight / 2 - 0.55, 0),
                                           scale=self.DefalutScale * 0.66,
                                           parent=self.Topics,
                                           relief=1,
                                           frameColor=(1, 1, 1, 1),
                                           text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                           )
#控制按键的位置
        # self.ShaderLandButton = DirectButton(pos=(1.8, 0, -1.6 + (0.2 * -2)),
        #                                      command=self.ShaderLandOpen,
        #                                      frameSize=(0, width, 0, hight),
        #                                      text="渐变渲染",
        #                                      text_font=self.DefalutFont,
        #                                      text_scale=2,
        #                                      text_align=TextNode.ACenter,
        #                                      text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                      scale=self.DefalutScale * 0.66,
        #                                      parent=self.Topics,
        #                                      relief=1,
        #                                      frameColor=(1, 1, 1, 1),
        #                                      text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                      )

        self.Classical = DirectButton(pos=(1.8, 0, -1.8 + (0.2 * -1)),
                                      command=self.LandOpen,
                                      frameSize=(0, width, 0, hight),
                                      text="手势下雨",
                                      text_font=self.DefalutFont,
                                      text_scale=2,
                                      text_align=TextNode.ACenter,
                                      text_pos=(width / 2, hight / 2 - 0.55, 0),
                                      scale=self.DefalutScale * 0.66,
                                      parent=self.Topics,
                                      relief=1,
                                      frameColor=(1, 1, 1, 1),
                                      text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                      )
        self.Island = DirectButton(pos=(1.8, 0, -1.8 + (0.2 * -2)),
                                   command=self.IslandOpen,
                                   frameSize=(0, width, 0, hight),
                                   # text="天堂海岛",
                                   text="海洋生物",
                                   text_font=self.DefalutFont,
                                   text_scale=2,
                                   text_align=TextNode.ACenter,
                                   text_pos=(width / 2, hight / 2 - 0.55, 0),
                                   scale=self.DefalutScale * 0.66,
                                   parent=self.Topics,
                                   relief=1,
                                   frameColor=(1, 1, 1, 1),
                                   text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                   )
        # self.Classical = DirectButton(pos=(1.8, 0, -1.6 + (0.2 * -3)),
        #                               command=self.LandOpen,
        #                               frameSize=(0, width, 0, hight),
        #                               text="手势下雨",
        #                               text_font=self.DefalutFont,
        #                               text_scale=2,
        #                               text_align=TextNode.ACenter,
        #                               text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                               scale=self.DefalutScale * 0.66,
        #                               parent=self.Topics,
        #                               relief=1,
        #                               frameColor=(1, 1, 1, 1),
        #                               text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                               )
        self.Football = DirectButton(pos=(1.8, 0, -1.8 + (0.2 * -3)),
                                     command=self.FootballOpen,
                                     frameSize=(0, width, 0, hight),
                                     text="其它应用",
                                     text_font=self.DefalutFont,
                                     text_scale=2,
                                     text_align=TextNode.ACenter,
                                     text_pos=(width / 2, hight / 2 - 0.55, 0),
                                     scale=self.DefalutScale * 0.66,
                                     parent=self.Topics,
                                     relief=1,
                                     frameColor=(1, 1, 1, 1),
                                     text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                     )
        # self.Football = DirectButton(pos=(1.8, 0, -1.6 + (0.2 * -5)),
        #                              command=self.FootballOpen,
        #                              frameSize=(0, width, 0, hight),
        #                              text="沙滩足球",
        #                              text_font=self.DefalutFont,
        #                              text_scale=2,
        #                              text_align=TextNode.ACenter,
        #                              text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                              scale=self.DefalutScale * 0.66,
        #                              parent=self.Topics,
        #                              relief=1,
        #                              frameColor=(1, 1, 1, 1),
        #                              text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                              )
        # self.OceanButton = DirectButton(pos=(1.8, 0, -1.6 + (0.2 * -6)),
        #                                 command=self.OceanOpen,
        #                                 frameSize=(0, width, 0, hight),
        #                                 text="场景定制",
        #                                 text_font=self.DefalutFont,
        #                                 text_scale=2,
        #                                 text_align=TextNode.ACenter,
        #                                 text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                 scale=self.DefalutScale * 0.66,
        #                                 parent=self.Topics,
        #                                 relief=1,
        #                                 frameColor=(1, 1, 1, 1),
        #                                 text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                 )
        self.ShaderLandSoloButton = DirectButton(pos=(2.39, 0, -1.8 + (0.2 * 0)),
                                                 command=self.ShaderLandSoloOpen,
                                                 frameSize=(0, width, 0, hight),
                                                 text="地形地貌",
                                                 text_font=self.DefalutFont,
                                                 text_scale=2,
                                                 text_align=TextNode.ACenter,
                                                 text_pos=(width / 2, hight / 2 - 0.55, 0),
                                                 scale=self.DefalutScale * 0.66,
                                                 parent=self.Topics,
                                                 relief=1,
                                                 frameColor=(1, 1, 1, 1),
                                                 text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                                 )
        # self.PandaLifeButton = DirectButton(pos=(2.39, 0, -1.6 + (0.2 * 0)),
        #                                     command=self.PandaLifeOpen,
        #                                     frameSize=(0, width, 0, hight),
        #                                     text="熊猫",
        #                                     text_font=self.DefalutFont,
        #                                     text_scale=2,
        #                                     text_align=TextNode.ACenter,
        #                                     text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                     scale=self.DefalutScale * 0.66,
        #                                     parent=self.Topics,
        #                                     relief=1,
        #                                     frameColor=(1, 1, 1, 1),
        #                                     text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                     )
        self.BoatFloatButton = DirectButton(pos=(2.39, 0, -1.8 + (0.2 * -1)),
                                            command=self.BoatFloatOpen,
                                            frameSize=(0, width, 0, hight),
                                            text="江河航船",
                                            text_font=self.DefalutFont,
                                            text_scale=2,
                                            text_align=TextNode.ACenter,
                                            text_pos=(width / 2, hight / 2 - 0.55, 0),
                                            scale=self.DefalutScale * 0.66,
                                            parent=self.Topics,
                                            relief=1,
                                            frameColor=(1, 1, 1, 1),
                                            text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                            )
        self.BoatFloatButton = DirectButton(pos=(2.39, 0, -1.8 + (0.2 * -2)),
                                            command=self.VolcanicEruption,
                                            frameSize=(0, width, 0, hight),
                                            text="火山喷发",
                                            text_font=self.DefalutFont,
                                            text_scale=2,
                                            text_align=TextNode.ACenter,
                                            text_pos=(width / 2, hight / 2 - 0.55, 0),
                                            scale=self.DefalutScale * 0.66,
                                            parent=self.Topics,
                                            relief=1,
                                            frameColor=(1, 1, 1, 1),
                                            text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                            )
        self.BoatFloatButton = DirectButton(pos=(2.39, 0, -1.8 + (0.2 * -3)),
                                            command=self.BoatFloatOpen,
                                            frameSize=(0, width, 0, hight),
                                            text="退出",
                                            text_font=self.DefalutFont,
                                            text_scale=2,
                                            text_align=TextNode.ACenter,
                                            text_pos=(width / 2, hight / 2 - 0.55, 0),
                                            scale=self.DefalutScale * 0.66,
                                            parent=self.Topics,
                                            relief=1,
                                            frameColor=(1, 1, 1, 1),
                                            text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
                                            )
        # self.SanxingduiButton = DirectButton(pos=(2.39, 0, -1.6 + (0.2 * -2)),
        #                                      command=self.SanxingduiOpen,
        #                                      frameSize=(0, width, 0, hight),
        #                                      text="化石考古",
        #                                      text_font=self.DefalutFont,
        #                                      text_scale=2,
        #                                      text_align=TextNode.ACenter,
        #                                      text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                      scale=self.DefalutScale * 0.66,
        #                                      parent=self.Topics,
        #                                      relief=1,
        #                                      frameColor=(1, 1, 1, 1),
        #                                      text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                      )
        #
        # self.StoneButton = DirectButton(pos=(2.39, 0, -1.6 + (0.2 * -3)),
        #                                 command=self.StoneOpen,
        #                                 frameSize=(0, width, 0, hight),
        #                                 text="星际穿越",
        #                                 text_font=self.DefalutFont,
        #                                 text_scale=2,
        #                                 text_align=TextNode.ACenter,
        #                                 text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                 scale=self.DefalutScale * 0.66,
        #                                 parent=self.Topics,
        #                                 relief=1,
        #                                 frameColor=(1, 1, 1, 1),
        #                                 text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                 )
        #
        # self.HongJunButton = DirectButton(pos=(2.39, 0, -1.6 + (0.2 * -4)),
        #                                   command=self.HongJunOpen,
        #                                   frameSize=(0, width, 0, hight),
        #                                   text="红军长征",
        #                                   text_font=self.DefalutFont,
        #                                   text_scale=2,
        #                                   text_align=TextNode.ACenter,
        #                                   text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                   scale=self.DefalutScale * 0.66,
        #                                   parent=self.Topics,
        #                                   relief=1,
        #                                   frameColor=(1, 1, 1, 1),
        #                                   text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                   )
        #
        # self.FarmButton = DirectButton(pos=(2.39, 0, -1.6 + (0.2 * -5)),
        #                                command=self.FarmOpen,
        #                                frameSize=(0, width, 0, hight),
        #                                text="蔬菜种植",
        #                                text_font=self.DefalutFont,
        #                                text_scale=2,
        #                                text_align=TextNode.ACenter,
        #                                text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                scale=self.DefalutScale * 0.66,
        #                                parent=self.Topics,
        #                                relief=1,
        #                                frameColor=(1, 1, 1, 1),
        #                                text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                )
        #
        # self.LearnDayTimeButton = DirectButton(pos=(2.39, 0, -1.6 + (0.2 * -6)),
        #                                        command=self.LearnDayTimeOpen,
        #                                        frameSize=(0, width, 0, hight),
        #                                        text="认识时间",
        #                                        text_font=self.DefalutFont,
        #                                        text_scale=2,
        #                                        text_align=TextNode.ACenter,
        #                                        text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                        scale=self.DefalutScale * 0.66,
        #                                        parent=self.Topics,
        #                                        relief=1,
        #                                        frameColor=(1, 1, 1, 1),
        #                                        text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                        )
        #
        # self.LearnShapeButton = DirectButton(pos=(2.98, 0, -1.6 + (0.2 * 0)),
        #                                      command=self.LearnShapeOpen,
        #                                      frameSize=(0, width, 0, hight),
        #                                      text="几何学习",
        #                                      text_font=self.DefalutFont,
        #                                      text_scale=2,
        #                                      text_align=TextNode.ACenter,
        #                                      text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                      scale=self.DefalutScale * 0.66,
        #                                      parent=self.Topics,
        #                                      relief=1,
        #                                      frameColor=(1, 1, 1, 1),
        #                                      text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                      )
        #
        # self.NetMapButton = DirectButton(pos=(2.98, 0, -1.6 + (0.2 * -1)),
        #                                  command=self.NetMapOpen,
        #                                  frameSize=(0, width, 0, hight),
        #                                  text="坐标学习",
        #                                  text_font=self.DefalutFont,
        #                                  text_scale=2,
        #                                  text_align=TextNode.ACenter,
        #                                  text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                  scale=self.DefalutScale * 0.66,
        #                                  parent=self.Topics,
        #                                  relief=1,
        #                                  frameColor=(1, 1, 1, 1),
        #                                  text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                  )
        #
        # self.NetCustomButton = DirectButton(pos=(2.98, 0, -1.6 + (0.2 * -2)),
        #                                     command=self.NetCustomOpen,
        #                                     frameSize=(0, width, 0, hight),
        #                                     text="自定网格",
        #                                     text_font=self.DefalutFont,
        #                                     text_scale=2,
        #                                     text_align=TextNode.ACenter,
        #                                     text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                     scale=self.DefalutScale * 0.66,
        #                                     parent=self.Topics,
        #                                     relief=1,
        #                                     frameColor=(1, 1, 1, 1),
        #                                     text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                     )
        #
        # self.NetDrawButton = DirectButton(pos=(2.98, 0, -1.6 + (0.2 * -3)),
        #                                   command=self.NetDrawOpen,
        #                                   frameSize=(0, width, 0, hight),
        #                                   text="平面绘画",
        #                                   text_font=self.DefalutFont,
        #                                   text_scale=2,
        #                                   text_align=TextNode.ACenter,
        #                                   text_pos=(width / 2, hight / 2 - 0.55, 0),
        #                                   scale=self.DefalutScale * 0.66,
        #                                   parent=self.Topics,
        #                                   relief=1,
        #                                   frameColor=(1, 1, 1, 1),
        #                                   text_fg=(10 / 255, 86 / 255, 102 / 255, 1)
        #                                   )

    #		self.Clib = DirectButton(	pos=(2.36,0,-1.6+(0.2*4)),
    #																		command=self.ClibOpen,
    #																		frameSize=(0,width,0,hight),
    #																		text="调试",
    #																		text_font=self.DefalutFont,
    #																		text_scale=2,
    #																		text_align=TextNode.ACenter,
    #																		text_pos=(width/2,hight/2-0.55,0),
    #																		scale=self.DefalutScale*0.8,
    #																		parent=self.Topics,
    #																		relief=1,
    #																		frameColor=(1,1, 1, 1),
    #																		text_fg=(10/255,86/255,102/255,1)
    #																		)

    # start the UDP server for remote control
        self._init_udp_server("127.0.0.1", 8888)
    #     self._init_udp_server("192.168.33.106", 8888)


    def GameOpen(self):
        self.InitializeTopic()
        self.UpdateConfig()

    def BackToMainPage(self):
        self.GameButton.show()
        self.ClibButton.show()
        self.ExitButton.show()
        self.Title.setPos(1.43, -0.2 - 1.05)
        self.Title.setScale(0.15)
        self.TypeTitle.hide()
        self.HintTitle.show()
        self.MainPage["image"] = "./data/texture/MainPageMovie.mp4"

        for node in self.Topics.getChildren():
            node.hide()

#############################下面是打开场景的逻辑
    def FarmOpen(self):
        from Farm import Farm
        self.MainPage.hide()
        Farm()
        self.CurrentPage = "Farm"

    def HongJunOpen(self):
        from HongJun import HongJun
        self.MainPage.hide()
        HongJun()
        self.CurrentPage = "HongJun"

    def StoneOpen(self):
        from Stone import Stone
        self.MainPage.hide()
        Stone()
        self.CurrentPage = "Stone"

    def SanxingduiOpen(self):
        from Sanxingdui import Sanxingdui
        self.MainPage.hide()
        Sanxingdui()
        self.CurrentPage = "Sanxingdui"

    def BoatFloatOpen(self):
        from BoatFloat import BoatFloat
        self.MainPage.hide()
        BoatFloat()
        self.CurrentPage = "BoatFloat"
    def VolcanicEruption(self):
        from VolcanicEruption import VolcanicEruption
        self.MainPage.hide()
        VolcanicEruption()
        self.CurrentPage = "VolcanicEruption"
    def PandaLifeOpen(self):
        from PandaLife import PandaLife
        self.MainPage.hide()
        PandaLife()
        self.CurrentPage = "PandaLife"

    def LearnShapeOpen(self):
        from LearnShape import LearnShape
        self.MainPage.hide()
        LearnShape()
        self.CurrentPage = "LearnShape"

    def NetMapOpen(self):
        from NetMap import NetMap
        self.MainPage.hide()
        NetMap()
        self.CurrentPage = "NetMap"

    def LearnDayTimeOpen(self):
        from LearnDayTime import LearnDayTime
        self.MainPage.hide()
        LearnDayTime()
        self.CurrentPage = "LearnDayTime"

    def NetCustomOpen(self):
        from NetCustom import NetCustom
        self.MainPage.hide()
        NetCustom()
        self.CurrentPage = "NetCustom"

    def NetDrawOpen(self):
        from NetDraw import NetDraw
        self.MainPage.hide()
        NetDraw()
        self.CurrentPage = "NetDraw"

    def LandOpen(self):
        from LandOpen import LandThread
        LandThread().start()

    def IslandOpen(self):
        from IsLandOpen import IsLandThread
        IsLandThread().start()

    def FootballOpen(self):
        from Football import Football
        self.MainPage.hide()
        Football()
        self.CurrentPage = "Football"

    def OceanOpen(self):
        from Ocean import Ocean
        Ocean()
        self.MainPage.hide()
        self.CurrentPage = "Ocean"

    def ShaderLandOpen(self):
        from ShaderMap import ShaderMap
        ShaderMap()
        self.MainPage.hide()
        self.CurrentPage = "ShaderLand"

    def ShaderLandSoloOpen(self):
        from ShaderMapSolo import ShaderMapSolo
        ShaderMapSolo()
        self.MainPage.hide()
        self.CurrentPage = "ShaderLand"

    def BaseLandOpen(self):
        from BaseLand import BaseLand
        BaseLand()
        self.MainPage.hide()
        self.CurrentPage = "BaseLand"

    def ClibOpen(self):
        try:
            config1 = open("./config/FirstStep.txt", "r").readlines()
        except:
            config1 = open("./config/DefaultFirstStep.txt", "r").readlines()

        self.VisibaleSliderValue = int(float(config1[0].replace("\n", "")))
        self.ClibBoxSliderValue = float(config1[1].replace("\n", ""))
        self.ClibBoxXSliderValue = int(float(config1[2].replace("\n", "")))
        self.ClibBoxYSliderValue = int(float(config1[3].replace("\n", "")))

        self.GrayDeep = self.VisibaleSliderValue

        try:
            config3 = open("./config/SecondStep.txt", "r").readlines()
        except:
            config3 = open("./config/DefaultSecondStep.txt", "r").readlines()
        self.ClibColorHightLineStep = int(float(config3[0].replace("\n", "")))
        self.LineStep = int(float(config3[1].replace("\n", "")))
        self.SandH = int(float(config3[2].replace("\n", "")))
        self.Level = int(float(config3[3].replace("\n", "")))
        self.UpdateDT = int(float(config3[4].replace("\n", "")))
        self.dpi = round(float(config3[5].replace("\n", "")), 2)

        try:
            config2 = open("./config/ThirdStep.txt", "r").readlines()
        except:
            config2 = open("./config/DefaultThirdStep.txt", "r").readlines()

        self.CamHight = int(float(config2[0].replace("\n", "")))
        self.CamX = int(float(config2[1].replace("\n", "")))
        self.CamY = int(float(config2[2].replace("\n", "")))
        base.cam.setPos((self.CamX, self.CamY, self.CamHight))
        base.cam.setHpr((0, -90, 0))

        try:
            config4 = open("./config/FourthStep.txt", "r").readlines()
        except:
            config4 = open("./config/DefaultFourthStep.txt", "r").readlines()

        self.Scale = float(config4[0].replace("\n", ""))
        self.OffX = float(config4[1].replace("\n", ""))
        self.OffY = float(config4[2].replace("\n", ""))

        self.SandWidth = int(512 * self.ClibBoxSliderValue)
        self.SandHight = int(288 * self.ClibBoxSliderValue)
        self.SandOffX = int(self.ClibBoxXSliderValue)
        self.SandOffY = int(self.ClibBoxYSliderValue)
        self.StableData = np.zeros((self.SandHight, self.SandWidth))

        TryTime = time.time()

        while self.StableData.max() <= 1:
            self.StableData = self.Sensor.Sensor.get_frame()
            self.StableData = self.StableData[self.SandOffY:self.SandHight + self.SandOffY,
                              self.SandOffX:self.SandWidth + self.SandOffX]
            self.StableData.dtype = np.int16
            self.Distance = self.StableData.max()
            self.StableData[:][np.where(self.StableData[:] < self.Distance - 300)[:]] = self.Distance - 300
            if time.time() - TryTime > 5:
                self.Text_C.setText("Kinect连接失败")
                self.Text_C.show()
                return
            self.Text_C.hide()

        from ClibMapFourStep import FirstStep
        self.MainPage.hide()
        FirstStep()

    def ClearNode(self):
        for node in self.TopicNode2D.getChildren():
            node.remove_node()
        for node in self.TopicNode3D.getChildren():
            node.remove_node()
        for node in self.TopicNode1D.getChildren():
            node.remove_node()
        for node in self.TopicNodeActor.getChildren():
            node.remove_node()

    def UpdateConfig(self):
        try:
            config1 = open("./config/FirstStep.txt", "r").readlines()
        except:
            config1 = open("./config/DefaultFirstStep.txt", "r").readlines()

        self.VisibaleSliderValue = int(float(config1[0].replace("\n", "")))
        self.ClibBoxSliderValue = float(config1[1].replace("\n", ""))
        self.ClibBoxXSliderValue = int(float(config1[2].replace("\n", "")))
        self.ClibBoxYSliderValue = int(float(config1[3].replace("\n", "")))

        self.GrayDeep = self.VisibaleSliderValue

        try:
            config3 = open("./config/SecondStep.txt", "r").readlines()
        except:
            config3 = open("./config/DefaultSecondStep.txt", "r").readlines()
        self.ClibColorHightLineStep = int(float(config3[0].replace("\n", "")))
        self.LineStep = int(float(config3[1].replace("\n", "")))
        self.SandH = int(float(config3[2].replace("\n", "")))
        self.Level = int(float(config3[3].replace("\n", "")))
        self.UpdateDT = int(float(config3[4].replace("\n", "")))
        self.dpi = round(float(config3[5].replace("\n", "")), 2)

        try:
            config2 = open("./config/ThirdStep.txt", "r").readlines()
        except:
            config2 = open("./config/DefaultThirdStep.txt", "r").readlines()

        self.CamHight = int(float(config2[0].replace("\n", "")))
        self.CamX = int(float(config2[1].replace("\n", "")))
        self.CamY = int(float(config2[2].replace("\n", "")))
        base.cam.setPos((self.CamX, self.CamY, self.CamHight))
        base.cam.setHpr((0, -90, 0))

        try:
            config4 = open("./config/FourthStep.txt", "r").readlines()
        except:
            config4 = open("./config/DefaultFourthStep.txt", "r").readlines()

        self.Scale = float(config4[0].replace("\n", ""))
        self.OffX = float(config4[1].replace("\n", ""))
        self.OffY = float(config4[2].replace("\n", ""))

        self.SandWidth = int(512 * self.ClibBoxSliderValue)
        self.SandHight = int(288 * self.ClibBoxSliderValue)
        self.SandOffX = int(self.ClibBoxXSliderValue)
        self.SandOffY = int(self.ClibBoxYSliderValue)
        self.StableData = np.zeros((self.SandHight, self.SandWidth))

        TryTime = time.time()

        if self.Dev == 0:
            while self.StableData.max() <= 1:
                self.StableData = self.Sensor.Sensor.get_frame()
                self.StableData = self.StableData[self.SandOffY:self.SandHight + self.SandOffY,
                                  self.SandOffX:self.SandWidth + self.SandOffX]
                self.StableData.dtype = np.int16
                self.Distance = self.StableData.max()
                self.StableData[:][np.where(self.StableData[:] < self.Distance - 300)[:]] = self.Distance - 300
                if time.time() - TryTime > 5:
                    self.Text_C.setText("Kinect连接失败")
                    self.Text_C.show()
                    break
                self.Text_C.hide()
        else:
            self.StableData = self.DefaultStableData
            self.StableData = self.StableData[self.SandOffY:self.SandHight + self.SandOffY,
                              self.SandOffX:self.SandWidth + self.SandOffX]
            self.StableData.dtype = np.int16
            self.Distance = self.StableData.max()
            self.StableData[:][np.where(self.StableData[:] < self.Distance - 300)[:]] = self.Distance - 300
            self.Text_C.hide()
            self.SandWidth = len(self.StableData[0])
            self.SandHight = len(self.StableData)

    def GetHand(self):
        if self.Dev == 0:
            color_data = base.Sensor.Sensor.get_frame()
        else:
            color_data = self.DefaultStableData
        color_data = color_data[self.SandOffY:self.SandHight + self.SandOffY,
                     self.SandOffX:self.SandWidth + self.SandOffX]
        color_data.dtype = np.int16
        color_data[:][np.where(color_data[:] <= 400)[:]] = 255
        # color_data[:][np.where(color_data[:]>900)[:]]=0
        color_data[:][np.where(color_data[:] > 1400)[:]] = 0
        # 转换为contiguousarray
        color_data = np.ascontiguousarray(color_data, dtype=np.uint8)
        contours, h = cv2.findContours(color_data, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        vaildContours = []
        closecoor = [0, 0]
        for cont in contours:
            if cv2.contourArea(cont) > 100:  # 这个也是一个要校对的参数
                vaildContours.append(cv2.convexHull(cont))

                hull = cv2.convexHull(cont)
                tblist = []
                for i in range(hull.shape[0]):
                    tblist.append(hull[i][0])
                centercoor = [self.SandHight / 2, self.SandWidth / 2]
                distance = []
                for tb in tblist:
                    distance.append(np.linalg.norm(centercoor - tb))
                closecoor = tblist[distance.index(min(distance))]
        return closecoor

    def UpdateDeep(self):
        if self.Dev == 0:
            color_data = base.Sensor.Sensor.get_frame()
        else:
            color_data = self.DefaultStableData
        color_data = color_data[self.SandOffY:self.SandHight + self.SandOffY,
                     self.SandOffX:self.SandWidth + self.SandOffX]
        color_data.dtype = np.int16
        color_data[:][np.where(color_data[:] < self.Distance - self.SandH)[:]] = self.Distance - self.SandH
        dt_data = color_data - self.StableData
        data_p = dt_data.copy()
        data_p[:][np.where(data_p[:] <= self.UpdateDT)[:]] = 0
        data_n = dt_data.copy()
        data_n[:][np.where(data_n[:] >= -self.UpdateDT)[:]] = 0
        data_p[:][np.where(data_p[:] != 0)[:]] = 3
        data_n[:][np.where(data_n[:] != 0)[:]] = -3
        self.StableData += data_p
        self.StableData += data_n

    def MakeGrayMap(self):
        base.UpdateDeep()
        StableData = base.StableData.copy()
        # 可能除下来之后在乘有问题，导致异常点过高
        StableData = StableData / base.Distance * 255
        minfloat = (base.Distance - self.SandH) / base.Distance * 255
        StableData = (1 / (255 - minfloat)) * (255 - StableData) * 255
        # 可能除下来之后在乘有问题，导致异常点过高
        StableData = np.flipud(StableData)
        cv2.imwrite("./render/graymapforblender.png", StableData)

    def MakeLinesMap(self):
        base.UpdateDeep()
        StableData = self.StableData.copy()
        StableData = scipy.ndimage.filters.gaussian_filter(StableData, 1.33)
        fig = plt.figure(frameon=False)
        fig.set_size_inches(1920 / 300, 1080 / 300)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.axis('off')
        fig.add_axes(ax)
        N2 = np.arange(self.Distance - self.SandH, self.Distance - self.Level, 12)
        contour = ax.contour(StableData, N2, alpha=1, colors="k", linewidths=0.1)
        # lb=ax.clabel(contour,fontsize=10,colors='k',inline=True,fmt='%3.0f')
        # for i in lb:
        #	i.set_rotation(180)
        # print(help(i))

        plt.savefig("./data/shader/ctlines.png")
        plt.close()
        gc.collect()

    def RegisterColorMap(self):
        for filename in os.listdir("./data/colormap"):
            if ".txt" in filename:
                colormap_name = filename.replace(".txt", "")

                data = open("./data/colormap/%s" % filename).readlines()

                #				tiposition=[]
                #				ticolors=[]
                #				for line in data:
                #					arr=line.split(",")
                #					tiposition.append(float(arr[0]))
                #					if "\n" in arr[3]:
                #						arr[3].replace("\n","")
                #					print(arr,[int(int(arr[1])/255),int(int(arr[2])/255),int(int(arr[3])/255)])
                #					ticolors.append([float(int(arr[1])/255),float(int(arr[2])/255),float(int(arr[3])/255)])
                #
                #				myrange=self.SandH-self.Level
                #
                #				tirange=max(tiposition)-min(tiposition)
                #
                #
                #				position=[]
                #				colors=[]
                #				minp=tiposition[0]
                #				for i in range(len(tiposition)):
                #					tiposition[i]-=minp
                #					p=tiposition[i]/tirange
                #					if p not in position:
                #						position.append(p)
                #						colors.append(ticolors[i])
                #
                #
                #				for i in range(len(position)):
                #					print(position[i],colors[i],ticolors[i])
                #
                #
                #				my_cmap = LinearSegmentedColormap.from_list(colormap_name, list(zip(position,colors)))
                #
                #				cm.register_cmap(cmap=my_cmap)
                #
                #				self.MapList.append(colormap_name)

                tiposition = []
                ticolors = []
                for line in data:
                    arr = line.split(",")
                    tiposition.append(float(arr[0]))
                    if "\n" in arr[3]:
                        arr[3].replace("\n", "")
                    ticolors.append([float(int(arr[1]) / 255), float(int(arr[2]) / 255), float(int(arr[3]) / 255)])

                myrange = self.SandH - self.Level

                tirange = max(tiposition) - min(tiposition)

                position = []
                colors = []
                minp = tiposition[0]
                for i in range(len(tiposition)):
                    tiposition[i] -= minp
                    p = int(myrange * (tiposition[i] / tirange))
                    if p not in position:
                        position.append(p)
                        colors.append(ticolors[i])

                # colors.reverse()

                rows, cols = np.shape(colors)

                color_map = []

                for i in range(0, rows - 1):
                    # 遍历区间中的所有像素点
                    for j in range(position[i], position[i + 1]):
                        color_r = (colors[i + 1][0] - colors[i][0]) * (j - position[i]) / (
                                    position[i + 1] - position[i]) + colors[i][0]
                        color_g = (colors[i + 1][1] - colors[i][1]) * (j - position[i]) / (
                                    position[i + 1] - position[i]) + colors[i][1]
                        color_b = (colors[i + 1][2] - colors[i][2]) * (j - position[i]) / (
                                    position[i + 1] - position[i]) + colors[i][2]

                        color = (color_r, color_g, color_b)
                        color_map.append(color)
                color_map.append(colors[rows - 1])

                # color_map=colors

                my_cmap = LinearSegmentedColormap.from_list(colormap_name, color_map)
                cm.register_cmap(cmap=my_cmap)

                base.MapList.append(colormap_name)

                map_image_arr = np.zeros((50, len(color_map), 3), np.uint8)

                for i in range(0, len(color_map), 1):
                    map_image_arr[:, i, 0] = color_map[i][0] * 255
                    map_image_arr[:, i, 1] = color_map[i][1] * 255
                    map_image_arr[:, i, 2] = color_map[i][2] * 255

                map_image = Image.fromarray(map_image_arr)
                # map_image=map_image.resize((255,50))
                map_image.save("./data/colormap/%s.png" % colormap_name)

    def GetContour(self):
        if self.Dev == 0:
            color_data = base.Sensor.Sensor.get_frame()
        else:
            color_data = self.DefaultStableData
        color_data = color_data[self.SandOffY:self.SandHight + self.SandOffY,
                     self.SandOffX:self.SandWidth + self.SandOffX]
        color_data.dtype = np.int16
        color_data[:][np.where(color_data[:] < self.Distance - self.SandH)[:]] = self.Distance - self.SandH
        StableData = scipy.ndimage.filters.gaussian_filter(color_data, 1.33)
        # StableData=color_data

        fig = plt.figure(frameon=False)
        fig.set_size_inches(self.SandWidth / 26, self.SandHight / 26)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.axis('off')
        fig.add_axes(ax)
        N2 = np.arange(self.Distance - self.SandH, self.Distance - self.Level,
                       (50 - self.LineStep) * int(self.ClibColorHightLineStep))
        contour = ax.contour(StableData, N2, alpha=1, colors="k", linewidths=self.dpi)
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        tex = Texture()
        tex.setup2dTexture(w, h, Texture.TUnsignedByte, Texture.FRgba)
        tex.setRamImageAs(fig.canvas.tostring_argb(), "ARGB")
        plt.close()
        gc.collect()

        return tex

    def UpdateTex(self, ColorMapName="gist_rainbow", ShowLine=1, GaussOpen=1, Mask=[0, 0], SandH=None, IsGray=0):
        if self.Dev == 0:
            color_data = base.Sensor.Sensor.get_frame()
        else:
            color_data = self.DefaultStableData
        color_data = color_data[self.SandOffY:self.SandHight + self.SandOffY,
                     self.SandOffX:self.SandWidth + self.SandOffX]
        color_data.dtype = np.int16

        color_data[:][np.where(color_data[:] < self.Distance - self.SandH)[:]] = self.Distance - self.SandH

        dt_data = color_data - self.StableData
        data_p = dt_data.copy()
        data_p[:][np.where(data_p[:] <= self.UpdateDT)[:]] = 0
        data_n = dt_data.copy()
        data_n[:][np.where(data_n[:] >= -self.UpdateDT)[:]] = 0

        if Mask[0] == 0:
            data_p[:][np.where(data_p[:] != 0)[:]] = 5
            data_n[:][np.where(data_n[:] != 0)[:]] = -5

        self.StableData += data_p
        self.StableData += data_n
        StableData = self.StableData.copy()
        StableData = np.flipud(StableData)
        if Mask[0] != 0:
            StableData -= Mask[1]
        if GaussOpen:
            StableData = scipy.ndimage.filters.gaussian_filter(StableData, 1.33)
        # ---------------------------------------------------

        fig = plt.figure(frameon=False)
        fig.set_size_inches(self.SandWidth / 25, self.SandHight / 25)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.axis('off')
        fig.add_axes(ax)
        try:
            N1 = np.arange(self.Distance - self.SandH, self.Distance - self.Level, (50 - self.LineStep))
            N2 = np.arange(self.Distance - self.SandH, self.Distance - self.Level,
                           (50 - self.LineStep) * int(self.ClibColorHightLineStep))
        except:
            N1 = np.arange(self.Distance - 500, self.Distance, 50)
            N2 = np.arange(self.Distance - 500, self.Distance, 50)
        if SandH != None:
            N1 = np.arange(self.Distance - self.SandH, self.Distance - self.Level + SandH, 5)
            StableData[:][np.where(StableData[:] >= self.Distance - SandH)[:]] = 0

        if IsGray == 0:
            ax.contourf(StableData, N1, cmap=plt.cm.get_cmap(ColorMapName))
        else:
            ax.contourf(StableData, N1, cmap="gray")

        if ShowLine:
            contour = ax.contour(StableData, N2, alpha=1, colors="k", linewidths=self.dpi)
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        tex = Texture()
        tex.setup2dTexture(w, h, Texture.TUnsignedByte, Texture.FRgba)

        # buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        # buf.shape = (h, w, 4)
        # buf = np.roll(buf, 3, axis=2)
        # buf=np.flipud(buf)

        # image = Image.frombytes("RGBA", (w, h), buf.tostring())
        # image = np.asarray(image)
        # tex.setRamImageAs(image, "RGBA")

        tex.setRamImageAs(fig.canvas.tostring_argb(), "ARGB")
        plt.close()
        gc.collect()
        return tex

    def CoorCheckLogic(self, bt):
        UI = self.UI_C
        if "direct.actor" in str(type(UI)):
            if bt == "arrow_up":
                UI.setPos(UI.getPos()[0], UI.getPos()[1] - self.UI_C_XY[1], UI.getPos()[2])
                PosX = int(UI.getPos()[0] / (1024 / self.GlobalX))
                PosY = int(UI.getPos()[1] / (848 / self.GlobalY))
                self.Text_C.setText("控件actor坐标：%s,深度:%s" % (UI.getPos(), base.StableData[PosY][PosX]))
            if bt == "arrow_down":
                UI.setPos(UI.getPos()[0], UI.getPos()[1] + self.UI_C_XY[1], UI.getPos()[2])
                PosX = int(UI.getPos()[0] / (1024 / self.GlobalX))
                PosY = int(UI.getPos()[1] / (848 / self.GlobalY))
                self.Text_C.setText("控件actor坐标：%s,深度:%s" % (UI.getPos(), base.StableData[PosY][PosX]))
            if bt == "arrow_left":
                UI.setPos(UI.getPos()[0] + self.UI_C_XY[0], UI.getPos()[1], UI.getPos()[2])
                PosX = int(UI.getPos()[0] / (1024 / self.GlobalX))
                PosY = int(UI.getPos()[1] / (848 / self.GlobalY))
                self.Text_C.setText("控件actor坐标：%s,深度:%s" % (UI.getPos(), base.StableData[PosY][PosX]))
            if bt == "arrow_right":
                UI.setPos(UI.getPos()[0] - self.UI_C_XY[0], UI.getPos()[1], UI.getPos()[2])
                PosX = int(UI.getPos()[0] / (1024 / self.GlobalX))
                PosY = int(UI.getPos()[1] / (848 / self.GlobalY))
                self.Text_C.setText("控件actor坐标：%s,深度:%s" % (UI.getPos(), base.StableData[PosY][PosX]))
        elif "ModelRoot" in str(UI.node()):
            if bt == "arrow_up":
                UI.setPos(UI.getPos()[0], UI.getPos()[1] - self.UI_C_XY[1], UI.getPos()[2])
                self.Text_C.setText("控件obj坐标：%s" % UI.getPos())
            if bt == "arrow_down":
                UI.setPos(UI.getPos()[0], UI.getPos()[1] + self.UI_C_XY[1], UI.getPos()[2])
                self.Text_C.setText("控件obj坐标：%s" % UI.getPos())
            if bt == "arrow_left":
                UI.setPos(UI.getPos()[0] + self.UI_C_XY[0], UI.getPos()[1], UI.getPos()[2])
                self.Text_C.setText("控件obj坐标：%s" % UI.getPos())
            if bt == "arrow_right":
                UI.setPos(UI.getPos()[0] - self.UI_C_XY[0], UI.getPos()[1], UI.getPos()[2])
                self.Text_C.setText("控件obj坐标：%s" % UI.getPos())
        else:
            try:
                if bt == "arrow_up":
                    UI.setPos(UI.getPos()[0], UI.getPos()[1], UI.getPos()[2] + self.UI_C_XY[1])
                    self.Text_C.setText("控件box坐标：%s" % UI.getPos())
                if bt == "arrow_down":
                    UI.setPos(UI.getPos()[0], UI.getPos()[1], UI.getPos()[2] - self.UI_C_XY[1])
                    self.Text_C.setText("控件box坐标：%s" % UI.getPos())
                if bt == "arrow_left":
                    UI.setPos(UI.getPos()[0] - self.UI_C_XY[0], UI.getPos()[1], UI.getPos()[2])
                    self.Text_C.setText("控件box坐标：%s" % UI.getPos())
                if bt == "arrow_right":
                    UI.setPos(UI.getPos()[0] + self.UI_C_XY[0], UI.getPos()[1], UI.getPos()[2])
                    self.Text_C.setText("控件box坐标：%s" % UI.getPos())
            except:
                if bt == "arrow_up":
                    UI.setPos(UI.getPos()[0], UI.getPos()[1] + +self.UI_C_XY[1])
                    self.Text_C.setText("控件text坐标：%s %s" % (UI.getPos()[0], UI.getPos()[1]))
                if bt == "arrow_down":
                    UI.setPos(UI.getPos()[0], UI.getPos()[1] - +self.UI_C_XY[1])
                    self.Text_C.setText("控件text坐标：%s %s" % (UI.getPos()[0], UI.getPos()[1]))
                if bt == "arrow_left":
                    UI.setPos(UI.getPos()[0] - +self.UI_C_XY[0], UI.getPos()[1])
                    self.Text_C.setText("控件text坐标：%s %s" % (UI.getPos()[0], UI.getPos()[1]))
                if bt == "arrow_right":
                    UI.setPos(UI.getPos()[0] + +self.UI_C_XY[0], UI.getPos()[1])
                    self.Text_C.setText("控件text坐标：%s %s" % (UI.getPos()[0], UI.getPos()[1]))


# XY().run()

    def _init_udp_server(self, host, port):
        # """Initialize the remote control server."""保存从手机来的命令到变量destination中
        #		destination = self._remote_commands
        class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):

            def handle(self):

                try:
                    print("Client connection opened.")

                    client_data = self.request[0]
                    server = self.request[1]
                    client_address = self.client_address
                    print('client send date:%s' % client_data)
                    print('client send date:%s' % client_data.decode('utf-8'))

                    # 沙绘艺术返回主界面
                    if client_data.decode('utf-8') == "main_page":
                        if app.CurrentPage == "BaseLand":
                            app.BackToMainPage()
                            app.CurrentPage = "BaseLand"

                            from BaseLand import BaseLand
                            BaseLand.BackButtonFunc()

                    #沙绘艺术
                    if client_data.decode('utf-8') == "sand_painting":
                        from BaseLand import BaseLand
                        BaseLand()
                        app.MainPage.hide()
                        app.CurrentPage = "BaseLand"

                    # 切换色卡
                    if client_data.decode('utf-8') == "prev":
                        from BaseLand import BaseLand
                        BaseLand.ColorChangeLButtonFunc()
                    if client_data.decode('utf-8') == "next":
                        from BaseLand import BaseLand
                        BaseLand.ColorChangeNButtonFunc()

                    ###################海洋生物###########################
                    if client_data.decode('utf-8') == "marine_organism_return":
                        # 退出海岛
                        os.system('taskkill /f /t /im '+ 'KinectSandbox.exe')#MESMTPC.exe程序名字
                        app.CurrentPage = "MainPage"


                except:
                    print("Connection closed by client.")

        class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
            pass

        try:
            server = ThreadedUDPServer((host, port), ThreadedUDPRequestHandler)

            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            print("Server started at {} port {}".format(host, port))

        # while True:
        #	time.sleep(100)

        except (KeyboardInterrupt, SystemExit):
            server.shutdown()
            server.server_close()
            exit()


app = XY()

app.run()

while True:
    framework.tickmodule.shared_lock.acquire()
    # framework.tickmodule.engine_lock.acquire()
    app.taskMgr.step()
    # framework.tickmodule.engine_lock.release()
    framework.tickmodule.shared_lock.release()
