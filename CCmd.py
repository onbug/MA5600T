#coding:utf-8

#!/usr/bin/python

import struct
import copy
import sys
import socket

import VOS
import CCmdTree
import CCmdStkNode
import CRm

ERROR = -1

#唯一、完整匹配上，如display
SOLE_MATCHING_ON = 0

#唯一、部分匹配上，如displ唯一匹配display
SOLE_PARTLY_MATCHING_ON = 1

#多項、部分或全部匹配上，如i匹配ip、interface，又如ip匹配ip和ipos
MULTI_MATCHING_ON = 2

NO_MATCHING = 3


class CCmdNodesStack(VOS.CStack):
    def __init__(self):
        super(CCmdNodesStack, self).__init__()
        return

    def GetLastSegmentLen(self):
        if None == self.m_oList:
            return None 
        oList = copy.deepcopy(self.m_oList)
        strSegment = ''
        iCount = 0
        for i in range(VOS.Len(oList)):
            if "SPACE" == self.Top(oList).GetAttribute():
                if(0 < i):
                    break
                else:
                    self.Pop(oList)
                    continue
            oNode = self.Pop(oList).GetCmdNode()
            if None != oNode:
                iCount += 1
        return iCount
        

class CCmd(object):
    def __init__(self):
        self.m_strWelcome = "***********************************************************\
\n*Copyright (C) 2010-2012 FakeHuawei Technologies Co., Ltd.*\
\n*       Without the owner's prior written consent,        *\
\n* no decompiling or reverse-engineering shall be allowed. *\
\n* Notice:                                                 *\
\n*      This is a private communication system.            *\
\n*   Unauthorized access or use may lead to prosecution.   *\
\n***********************************************************\
\n\
\nUser interface con0 is available\
\n\
\n\
\n\
\nPlease Press ENTER.\
\n"
        self.m_oCmdTree = None
        self.m_strRawCmd = None     #用戶輸入的原始命令
        self.m_strCmd = None        #格式化過的標準命令，所以不會有tab或連續空格
        self.m_strCurrentLine = None  #當前行顯示的內容

        #存儲當前命令節點的棧，如display ip rou（正在分析rou時），棧裡的內容為display、ip
        self.m_ostkCmd = None
        self.m_ostkHistoryCmd = None
        return


    #實時格式化命令行函式
    #使用並可能影響m_strCmd
    def CharInputRealTimeProc(self, arg_cCh = ' '):
        self.m_strRawCmd += arg_cCh

        #第一行and第三行：_或_ _
        #第二行and第三行：d_ _
        if (((None == self.m_strCmd) or (0 == VOS.Len(self.m_strCmd))) or \
            ' ' == self.m_strCmd[-1]) \
            and (' ' == arg_cCh):
            if None == self.m_ostkCmd:
                self.m_ostkCmd = CCmdNodesStack()
            self.m_ostkCmd.Push(CCmdStkNode.CMDSTK_Node(arg_Attribute = "SPACE", arg_cCh = ' '))
            return

        #普通字符和非連續的空格、非頭部的空格追加（連續的空格不追加、頭部的空格不追加）
        if (' ' != arg_cCh) or \
            ((' ' == arg_cCh) and \   #未完工  这里错了，如果输入的时空格，不能随便追加，需要匹配后追加，万一能匹配关键字呢？
            ((0 < VOS.Len(self.m_strCmd)) and (' ' != self.m_strCmd[-1]))):
            self.m_strCmd += arg_cCh
        
        #如果此時的m_strCmd最後一個字符時空格，考慮如下情況：
        #display ip routing-table _    有效命令
        #display ip asdf _             無效命令
        #那麼空格前的關鍵字都已經做過了處理，這裡直接返回即可
        #輸入的是空格，就可能被追加到m_strCmd中（非連續空格），那麼它僅是第一個空格，就不必返回
        if (' ' == self.m_strCmd[-1]) and (' ' != arg_cCh):
            return

        #空格、普通字符模式：得到最後的一個關鍵字（其實是最後一個關鍵字的片段），即display ip rou中的rou
        KeywordsArray = self.m_strCmd.split(' ')

        #非連續空格輸入時，m_strCmd == “display ip_”，因此KeywordsArray[-1] == ''
        strSegment = (KeywordsArray[-1] if '' != KeywordsArray[-1] else KeywordsArray[-2])

        self.ProcessKeyword(strSegment, arg_cCh)  #不論匹配與否，都有節點被壓棧了
        if ' ' == arg_cCh:
            self.m_ostkCmd.Pop()
            self.m_ostkCmd.Push(CCmdStkNode.CMDSTK_Node(arg_Attribute = "SPACE", arg_cCh = arg_cCh))
        
        self.DisplayProcess(arg_cCh)
        return
    

    '''
    #實時格式化命令行函式
    #使用並可能影響m_strCmd
    def CmdFormatRealTime(self, arg_iPortal = "SPACE_WAY"):
        #如果此時的m_strCmd最後一個字符時空格，考慮如下情況：
        #display ip routing-table _    有效命令
        #display ip asdf _             無效命令
        #那麼空格前的關鍵字都已經做過了處理，這裡直接返回即可
        if 0 == VOS.Len(self.m_strCmd) or " " == self.m_strCmd[-1]:
            return

        #空格、普通字符模式：得到最後的一個關鍵字（其實是最後一個關鍵字的片段），即display ip rou中的rou
        KeywordsArray = self.m_strCmd.split(" ")

        strSegment = KeywordsArray[-1]
        if 0 == VOS.Len(strSegment):
            return

        iRetCode, strKeyword = self.ProcessKeyword(strSegment, arg_iPortal)
        self.DisplayProcess(iRetCode, strKeyword, strSegment, arg_iPortal)
        return
    '''


    def ClearCurrentLine(self):
        if None == self.m_strCurrentLine:
            return

        for cCh in self.m_strCurrentLine[::-1]:
            self.BackspaceDisplay()

        return


    #是否是第一個關鍵字
    def IsFirstKeyword(self, arg_strCmd = None):
        if None == arg_strCmd:
            return True if -1 == self.m_strCmd.rfind(' ') else False
        else:
            return True if -1 == arg_strCmd.rfind(' ') else False


    #盡量匹配關鍵字
    def KeywordMaxMatching(self, arg_oLastNode, arg_strSegment):
        #普通關鍵字精確、最大匹配

        if None == arg_oLastNode:
            oRootNode = None
        else:
            oRootNode = arg_oLastNode.m_oSubNode

        iRetCode, strKeyword, oCurrentNode = self.m_oCmdTree.NextNodeMaxMatching(oRootNode, arg_strSegment)

        #精確匹配上或唯一、部分匹配上     未完工：精確匹配上&&唯一、部分匹配上二合一，函數返回值沒對上
        if (CCmdTree.SOLE_MATCHING_ON == iRetCode) and (None != oCurrentNode):
            return SOLE_MATCHING_ON, strKeyword, oCurrentNode

        #多個匹配上
        if CCmdTree.MULTI_MATCHING_ON == iRetCode:
            return MULTI_MATCHING_ON, None, oCurrentNode

        #沒匹配上，表明不是合法關鍵字

        #變量關鍵字匹配，如$ipv4-address
        #未完工

        return NO_MATCHING, None, None


    def _PrintSkt(self):
        if None == self.m_ostkCmd:
            return

        ostkNode = copy.deepcopy(self.m_ostkCmd)
        while True:
            oNode = ostkNode.Pop()
            if None == oNode:
                break
            self.ExecStringOut("CCmd::STK: " + oNode.m_strKeyword)
        return


    #arg_strSegment關鍵字片段，返回-1表明關鍵字未匹配上，否則返回匹配上的關鍵字
    def ProcessKeyword(self, arg_strSegment, arg_cCh):
        if 0 == VOS.Len(arg_strSegment):
            return ERROR, None


        if None == self.m_ostkCmd:
            oLastNode = None
        else:
            oStkNode = self.m_ostkCmd.Top()
            if None == oStkNode:
                oLastNode = None
            else:
                if (None != oStkNode) and ("SPACE" == oStkNode.GetAttribute()):
                    oStkNode = self.m_ostkCmd.GetElement(-2)
                    oLastNode = (None if None == oStkNode else oStkNode.GetCmdNode())
                else:
                    oLastNode = None


        #最大匹配
        iRetCode, strKeyword, oNode = self.KeywordMaxMatching(oLastNode, arg_strSegment)

        if None == self.m_ostkCmd:
            self.m_ostkCmd = CCmdNodesStack()

        #精確匹配上 或 部分唯一匹配上，這裡不區分
        #精確匹配上的，不存在剩餘部分，所以無需追加
        #唯一但非精確匹配上的，如disp
        if SOLE_MATCHING_ON == iRetCode:
            self.m_ostkCmd.Push(CCmdStkNode.CMDSTK_Node(oNode, "SOLE MATCHING ON", arg_cCh))
            return SOLE_MATCHING_ON, strKeyword

        if MULTI_MATCHING_ON == iRetCode:
            self.m_ostkCmd.Push(CCmdStkNode.CMDSTK_Node("MULTI MATCHING ON", arg_cCh))
            return MULTI_MATCHING_ON, None

        #走到這就是沒匹配上，壓入空節點
        self.m_ostkCmd.Push(CCmdStkNode.CMDSTK_Node(oNode, "NO MATCHING", arg_cCh))
        #self._PrintStk()
        return NO_MATCHING, None


    '''
    #arg_strSegment關鍵字片段，返回-1表明關鍵字未匹配上，否則返回匹配上的關鍵字
    def ProcessKeyword(self, arg_strSegment, arg_iPortal = "SPACE_WAY"):
        if 0 == VOS.Len(arg_strSegment):
            return ERROR, None

        #退格進來的一律oLastNode = None，未完工
        if "BACKSPACE_FIRST_WAY" == arg_iPortal:
            oLastNode = None
            if None != self.m_ostkCmd:
                self.m_ostkCmd.PopAll()
        else:
            if None == self.m_ostkCmd:
                oLastNode = None
            else:
                oLastNode = self.m_ostkCmd.Top()

        #最大匹配
        iRetCode, strKeyword, oNode = self.KeywordMaxMatching(oLastNode, arg_strSegment)

        if (("SPACE_WAY" == arg_iPortal) or \
            ("BACKSPACE_FIRST_WAY" == arg_iPortal) or \
            ("BACKSPACE_NONFIRST_WAY" == arg_iPortal)) and \
            (None == self.m_ostkCmd):
            self.m_ostkCmd = VOS.CStack()

        #精確匹配上 或 部分唯一匹配上，這裡不區分
        #精確匹配上的，不存在剩餘部分，所以無需追加
        #唯一但非精確匹配上的，如disp
        if SOLE_MATCHING_ON == iRetCode:
            if ("SPACE_WAY" == arg_iPortal) or \
                ("BACKSPACE_FIRST_WAY" == arg_iPortal) or \
                ("BACKSPACE_NONFIRST_WAY" == arg_iPortal):
                self.m_ostkCmd.Push(oNode)
            return SOLE_MATCHING_ON, strKeyword

        if MULTI_MATCHING_ON == iRetCode:
            if ("SPACE_WAY" == arg_iPortal) or ("BACKSPACE_FIRST_WAY" == arg_iPortal):
                self.m_ostkCmd.Push()
            return MULTI_MATCHING_ON, None

        #走到這就是沒匹配上，壓入空節點
        if ("SPACE_WAY" == arg_iPortal) or ("BACKSPACE_FIRST_WAY" == arg_iPortal):
            self.m_ostkCmd.Push()
        #self._PrintStk()
        return NO_MATCHING, None
    '''


    def FormatKeywordDisplay(self, strSegment, strKeyword):
        if 0 == VOS.Len(strKeyword):
            return

        #刪除已鍵入的關鍵字片段
        for Letter in strSegment:
            self.BackspaceInput()
        #著色打印完整關鍵字
        VOS.set_cmd_text_color(VOS.FOREGROUND_GREEN)
        for Letter in strKeyword:
            VOS.PutCh(str.encode(Letter))
        VOS.resetColor()
        #不用加空格，用戶的空格命令行還沒加
        return


    def BackspaceDisplay(self):
        VOS.PutCh(b'\b')
        VOS.PutCh(b' ')
        VOS.PutCh(b'\b')
        sys.stdout.flush()

        if (None != self.m_strCurrentLine) and (1 <= VOS.Len(self.m_strCurrentLine)):
            self.m_strCurrentLine = self.m_strCurrentLine[:-1]

        return


    def BackspaceInput(self):
        #都刪空了就直接返回
        if 0 == VOS.Len(self.m_strCurrentLine):
            return

        #只要刪除的時空格，就無需觸發關鍵字重搜索
        if 1 <= VOS.Len(self.m_strCurrentLine) and ' ' == self.m_strCurrentLine[-1]:
            #如果是最後一個空格，如y _，還要刪除m_strCmd裡的
            if 2 <= VOS.Len(self.m_strCurrentLine) and \
                ' ' == self.m_strCurrentLine[-1] and \
                ' ' != self.m_strCurrentLine[-2]:
                self.m_strCmd = self.m_strCmd[:-1]
            self.BackspaceDisplay()
            return

        self.m_strCmd = self.m_strCmd[:-1]
        self.BackspaceDisplay()

        self.CmdFormat(self.m_strCmd, "BACKSPACE_FIRST_WAY")

        #只有從getch()返回的才需要寫成b' '的形式
        return


    #格式化命令行
    #一般為退格模式或命令恢復時使用。將字符串分解成關鍵字，重頭輸送給內部韓函式
    #可能使用并影響變量m_strCmd
    def CmdFormat(self, arg_strCmd, arg_iPortal = "BACKSPACE_FIRST_WAY"):
        if None == arg_strCmd:
            arg_strCmd = self.m_strCmd

        if 0 == VOS.Len(arg_strCmd):
            return

        if ' ' == arg_strCmd[-1]:
            return

        #命令行未補齊是不會有空格或tab了
        arg_strCmd = arg_strCmd.strip()
        if 0 == VOS.Len(arg_strCmd):
            return

        #分析標準命令行
        KeywordsArray = self.m_strCmd.split(' ')
        if 0 == VOS.Len(KeywordsArray[-1]):
            KeywordsArray.pop()

        #分析屏幕命令行關鍵字之間的空格數
        iSpaceArray = self.GetDisplaySpace(KeywordsArray)

        self.ClearCurrentLine()

        iLen = VOS.Len(KeywordsArray)
        for i, strSegment in enumerate(KeywordsArray):
            if 0 == VOS.Len(strSegment):
                continue
            if 0 == i:
                iRetCode, strKeyword = self.ProcessKeyword(strSegment, "BACKSPACE_FIRST_WAY")
            #最後一個關鍵字分析後，節點不壓棧
            elif (iLen - 1) == i:
                iRetCode, strKeyword = self.ProcessKeyword(strSegment, "NORMALCHAR_WAY")
            else:
                iRetCode, strKeyword = self.ProcessKeyword(strSegment, "BACKSPACE_NONFIRST_WAY")
            self.DisplayProcess(iRetCode, strKeyword, strSegment, "BACKSPACE_FIRST_WAY", iSpaceArray[i])

        return


    def GetDisplaySpace(self, arg_KeywordArray):
        iSpaceArray = list()
        cPreChar = None
        for i, cCh in enumerate(self.m_strCurrentLine):
            if (None == cPreChar and ' ' != cCh) or (' ' == cPreChar and ' ' != cCh):
                iSpaceArray.append(i)
            cPreChar = cCh

        for i, iPosition in enumerate(iSpaceArray):
            if 0 == i:
                continue

            iPrevCharNum = 0
            for j in range(i + 1):
                if 0 == j:
                    continue
                iPrevCharNum += (iSpaceArray[j - 1] + VOS.Len(arg_KeywordArray[j - 1]))

            iSpaceArray[i] -= iPrevCharNum

        return iSpaceArray


    def GetLastKeywordNo(self, arg_strCmd):
        KeywordsArray = arg_strCmd.split(' ')
        return VOS.Len(KeywordsArray)


    def DisplayProcess(self, arg_cCh):
        if ' ' == arg_cCh:
            #根據情況決定是否需要改變之前字符的顏色
            oCurrentStkNode = self.m_ostkCmd.GetElement(-2)
            #出錯處理
            if None == oCurrentStkNode:
                return

            #m_strCmd = "d_"這種情況oLastStkNode == None
            oLastStkNode = self.m_ostkCmd.GetElement(-3)
            
            if ("SOLE MATCHING ON" == oCurrentStkNode.GetAttribute()) and \
                (None != oCurrentStkNode.GetCmdNode()):
                n = self.m_ostkCmd.GetLastSegmentLen()
                strKeyword = oCurrentStkNode.GetCmdNode().GetKeyword()
                self.ExecStringOut(strKeyword[n:], VOS.FOREGROUND_GREEN)
                
            return

        
        #根據情況決定是否需要改變之前字符的顏色
        oCurrentStkNode = self.m_ostkCmd.Top()
        #出錯處理
        if None == oCurrentStkNode:
            return
            
        oLastStkNode = self.m_ostkCmd.GetElement(-2)
        strCurrentAttribute = oCurrentStkNode.GetAttribute()
        #第一個字符
        if None == oLastStkNode:
            if "SOLE MATCHING ON" == strCurrentAttribute:
                self.ExecStringOut(arg_cCh, VOS.FOREGROUND_GREEN)
            elif "MULTI MATCHING ON" == strCurrentAttribute:
                self.ExecStringOut(arg_cCh, VOS.FOREGROUND_DARKGREEN)
            elif "NO MATCHING" == strCurrentAttribute:
                self.ExecStringOut(arg_cCh, VOS.FOREGROUND_RED)
        #非第一個字符
        else:
            strLastAttribute = oLastStkNode.GetAttribute()
            #跟前一個字符的狀態一樣，無需變色
            if strCurrentAttribute == strLastAttribute:
                if "SOLE MATCHING ON" == strCurrentAttribute:
                    self.ExecStringOut(arg_cCh, VOS.FOREGROUND_GREEN)
                elif "MULTI MATCHING ON" == strCurrentAttribute:
                    self.ExecStringOut(arg_cCh, VOS.FOREGROUND_DARKGREEN)
                elif "NO MATCHING" == strCurrentAttribute:
                    self.ExecStringOut(arg_cCh, VOS.FOREGROUND_RED)
            #跟前一個字符的狀態不一樣，需要變色
            else:
                strTemp = ''
                if True == self.IsFirstKeyword():
                    for cLetter in self.m_strCmd:
                        self.BackspaceDisplay()
                        strTemp += cLetter
                else:
                    for cLetter in self.m_strCmd[self.m_strCmd.rfind(' ') + 1:]:
                        self.BackspaceDisplay()
                        strTemp += cLetter
                        
                if "SOLE MATCHING ON" == strCurrentAttribute:
                    self.ExecStringOut(strTemp, VOS.FOREGROUND_GREEN)
                elif "MULTI MATCHING ON" == strCurrentAttribute:
                    self.ExecStringOut(strTemp, VOS.FOREGROUND_DARKGREEN)
                elif "NO MATCHING" == strCurrentAttribute:
                    self.ExecStringOut(strTemp, VOS.FOREGROUND_RED)
        '''
        #先把用戶輸入的清理掉
        strSpace = ""
        if "BACKSPACE_FIRST_WAY" != arg_iPortal:
            for cLetter in arg_strSegment:
                self.BackspaceDisplay()

        for i in range(arg_iSpaceNum):
            strSpace += " "

        #空格字符串鍵入時
        if "SPACE_WAY" == arg_iPortal:
            if SOLE_MATCHING_ON == arg_iRetCode:
                if arg_strKeyword != arg_strSegment:
                    self.m_strCmd += arg_strKeyword[-(VOS.Len(arg_strKeyword) - VOS.Len(arg_strSegment)):]
                self.ExecStringOut(strSpace + arg_strKeyword, VOS.FOREGROUND_GREEN)
            elif MULTI_MATCHING_ON == arg_iRetCode:
                self.ExecStringOut(strSpace + arg_strSegment, VOS.FOREGROUND_DARKGREEN)
            else:
                self.ExecStringOut(strSpace + arg_strSegment, VOS.FOREGROUND_RED)

        #普通字符、退格字符鍵入時（實時匹配）
        else:
            #僅著色，但不補齊
            if SOLE_MATCHING_ON == arg_iRetCode:
                iTextColor = VOS.FOREGROUND_GREEN
            elif MULTI_MATCHING_ON == arg_iRetCode:
                iTextColor = VOS.FOREGROUND_DARKGREEN
            else:
                iTextColor = VOS.FOREGROUND_RED
            self.ExecStringOut(strSpace + arg_strSegment, iTextColor)
        '''
        return


    '''
    def DisplayProcess(self, arg_iRetCode, arg_strKeyword, arg_strSegment, arg_iPortal, arg_iSpaceNum = 0):
        #先把用戶輸入的清理掉
        strSpace = ''
        if "BACKSPACE_FIRST_WAY" != arg_iPortal:
            for cLetter in arg_strSegment:
                self.BackspaceDisplay()

        for i in range(arg_iSpaceNum):
            strSpace += " "

        #空格字符串鍵入時
        if "SPACE_WAY" == arg_iPortal:
            if SOLE_MATCHING_ON == arg_iRetCode:
                if arg_strKeyword != arg_strSegment:
                    self.m_strCmd += arg_strKeyword[-(VOS.Len(arg_strKeyword) - VOS.Len(arg_strSegment)):]
                self.ExecStringOut(strSpace + arg_strKeyword, VOS.FOREGROUND_GREEN)
            elif MULTI_MATCHING_ON == arg_iRetCode:
                self.ExecStringOut(strSpace + arg_strSegment, VOS.FOREGROUND_DARKGREEN)
            else:
                self.ExecStringOut(strSpace + arg_strSegment, VOS.FOREGROUND_RED)

        #普通字符、退格字符鍵入時（實時匹配）
        else:
            #僅著色，但不補齊
            if SOLE_MATCHING_ON == arg_iRetCode:
                iTextColor = VOS.FOREGROUND_GREEN
            elif MULTI_MATCHING_ON == arg_iRetCode:
                iTextColor = VOS.FOREGROUND_DARKGREEN
            else:
                iTextColor = VOS.FOREGROUND_RED
            self.ExecStringOut(strSpace + arg_strSegment, iTextColor)

        return
    '''

        
    def ExecStringOut(self, arg_strText, arg_iTextColor = VOS.FOREGROUND_DARKWHITE, arg_iBackgroundColor = VOS.FOREGROUND_BLACK):
        iRetCode, strLine = VOS.ExecStringOut(arg_strText, arg_iTextColor, arg_iBackgroundColor)
        if None == iRetCode:
            self.m_strCurrentLine += strLine
        else:
            self.m_strCurrentLine = strLine
        return


    def Init(self):
        self.m_strRawCmd = ''
        self.m_strCmd = ''
        self.m_strCurrentLine = ''
        #初始化命令樹
        self.m_oCmdTree = CCmdTree.CCmdTree()
        #註冊內部命令
        self.RegInterCmd()
        return


    #註冊內部命令
    #在CMD模塊層面不直接處理樹節點的東西，CMD模塊層面只處理命令結構，樹節點在樹的層面處理
    def RegInterCmd(self):
        self.m_oCmdTree.RegCmd("display version", "This command is print VVRP\'s version", self.CMD_DisplayVersion)
        self.m_oCmdTree.RegCmd("vrrp timer-advertise learning enable", "This command is vrrp timer-advertise learning enable", self.CMD_TimerAdvertiseLearningEnable)
        self.m_oCmdTree.RegCmd("display ip routing-table [verbose]", "None", CRm.CMD_DisplayIpRoutingTable)
        self.m_oCmdTree.RegCmd("display ipos version", "none", CRm.CMD_DisplayIpRoutingTable)
        return

    #display version回調函式
    def CMD_DisplayVersion(self):
        self.ExecStringOut("cmd \'display version\' has been called!")
        return


    #vrrp timer-advertise learning enable回調函式
    def CMD_TimerAdvertiseLearningEnable(self):
        self.ExecStringOut("cmd \'vrrp timer-advertise learning enable\' has been called!")
        return


    def Run(self):
        bQuit = False

        #命令行總循環
        while True:
            #關鍵字匹配循環
            while True:
                cRawCh = VOS.GetCh()
                if b'\t' == cRawCh:   #tab
                    cRawCh = b' '

                if b'\r' == cRawCh:    #回車
                    self.m_strCurrentLine = ''
                    self.CmdFormatRealTime()
                    self.ExecStringOut(arg_strText = '\nstrCmd = \"' + self.m_strCmd + '\"\n', arg_iTextColor = VOS.FOREGROUND_YELLOW)
                    if None != self.m_ostkCmd:
                        self.m_ostkCmd.PopAll()
                    break

                elif cRawCh == b'\b':    #退格
                    self.BackspaceInput()
                elif cRawCh == b' ':    #空格
                    self.SpaceTabInput()
                elif cRawCh == b'\xE0':    #向上
                    self.ExecStringOut("向上")
                elif cRawCh == b'\x50':    #向下
                    self.ExecStringOut("向下")
                elif cRawCh == b'\x1B':    #ESC
                    bQuit = True
                    break

                #普通字符，如a
                #彩色版本可變換顏色，以實時標記鍵入情況，故關鍵字匹配改為實時觸發
                else:
                    #VOS.PutCh(cRawCh)
                    #實時觸發
                    #self.m_strCurrentLine += cRawCh.decode()
                    self.CharInputRealTimeProc(cRawCh.decode())
                    #self.CmdFormatRealTime("NORMALCHAR_WAY")

            if True == bQuit:
                break

            #執行命令，未完工

            self.m_strCmd = ''
        return


    def PrintWelcome(self):
        self.ExecStringOut(self.m_strWelcome)
        return


    def SpaceTabInput(self):
        self.CharInputRealTimeProc(' ')
        self.ExecStringOut(' ')
        
        return


    def Main(self):
        self.Init()
        
        '''
        if CMD_OK != CMD-Init()
            return

        發消息給VOS，命令行初始化完畢
        if((VOS_NULL != g_pstTaskVOS) && (VOS_NULL != (g_pstTaskVOS->pstThread)))
        {
            VOS_SendQ(g_pstTaskVOS->pstThread->dwThreadId, VOS_MSG_CMD_INIT_FINISHED, VOS_ZERO, VOS_ZERO);
        }
        等待其他模塊初始化完成
        VOS_Delay(500)
        '''
        self.PrintWelcome()
        self.Run()
        return


    def RegCmd(self, strCmd):
        return