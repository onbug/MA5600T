#coding:utf-8

#!/usr/bin/python

import msvcrt, sys, ctypes, os

OK = 0

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

'''
字體顏色定義，關鍵在於顏色編碼，由2位十六進制數組成，分別取0~F。
前一位指的是背景色，後一位指的是字體色。
由於該函式的限制，應該是隻有這16種，可以前景色與背景色組合。
也可以幾種顏色通過運算組合，組合後還是在這16種顏色中
'''

#Windows CMD命令行，字體色定義
FOREGROUND_BLACK = 0x00
FOREGROUND_DARKBLUE = 0x01
FOREGROUND_DARKGREEN = 0x02
FOREGROUND_DARKSKYBLUE = 0x03
FOREGROUND_DARKRED = 0x04
FOREGROUND_DARKPINK = 0x05
FOREGROUND_DARKYELLOW = 0x06
FOREGROUND_DARKWHITE = 0x07
FOREGROUND_DARKGRAY = 0x08
FOREGROUND_BLUE = 0x09
FOREGROUND_GREEN = 0x0A
FOREGROUND_SKYBLUE = 0x0B
FOREGROUND_RED = 0x0C
FOREGROUND_PINK = 0x0D
FOREGROUND_YELLOW = 0x0E
FOREGROUND_WHITE = 0x0F

#Windows CMD命令行，背景色定義
BACKGROUND_BLUE = 0x10
BACKGROUND_GREEN = 0x20
BACKGROUND_DARKSKYBLUE = 0x30
BACKGROUND_DARKRED = 0x40
BACKGROUND_DARKPINK = 0x50
BACKGROUND_DARKYELLOW = 0x60
BACKGROUND_DARKWHITE = 0x70
BACKGROUND_DARKGRAY = 0x80
BACKGROUND_BLUE = 0x90
BACKGROUND_GREEN = 0xA0
BACKGROUND_SKYBLUE = 0xB0
BACKGROUND_RED = 0xC0
BACKGROUND_PINK = 0xD0
BACKGROUND_YELLOW = 0xE0
BACKGROUND_WHITE = 0xF0


std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


def Len(arg_oObject):
    return len(arg_oObject)


def set_cmd_text_color(color, handle = std_out_handle):
    Bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
    return Bool


def resetColor():
    set_cmd_text_color(FOREGROUND_DARKWHITE)
    return


def PutCh(arg_cCh):
    msvcrt.putch(arg_cCh)
    return


def GetCh():
    return msvcrt.getch()


def GetLastLine(arg_strText):
    if None == arg_strText:
        return None, None
    iIndex = arg_strText.rfind('\n')
    if -1 == iIndex:
        return None, arg_strText
    return OK, arg_strText[iIndex + 1:]


def ExecStringOut(arg_strText, arg_iTextColor = FOREGROUND_DARKWHITE, arg_iBackgroundColor = FOREGROUND_BLACK):
    set_cmd_text_color(arg_iTextColor)
    sys.stdout.write(arg_strText)
    sys.stdout.flush()
    resetColor()
    return GetLastLine(arg_strText)


def printDarkBlue(mess):
    set_cmd_text_color(FOREGROUND_DARKBLUE)
    sys.stdout.write(mess)
    resetColor()
    return


'''
該種函式若干
'''


def printYellowRed(mess):
    set_cmd_text_color(BACKGROUND_YELLOW | FOREGROUND_RED)
    sys.stdout.write(mess)
    resetColor()
    return


class CStack(object):
    def __init__(self):
        self.m_oList = None
        return


    def Push(self, arg_Object = None):
        if None == arg_Object:
            return
        if None == self.m_oList:
            self.m_oList = [arg_Object]
        else:
            self.m_oList.append(arg_Object)
        return


    def Pop(self, arg_oList = None):
        if None == arg_oList:
            arg_oList = self.m_oList
        return None if (None == arg_oList) or (0 == Len(arg_oList)) else arg_oList.pop()


    def PopAll(self):
        oAll = self.m_oList[:]
        self.DeleteAll()
        return oAll


    def Top(self, arg_oList = None):
        if None == arg_oList:
            arg_oList = self.m_oList
        return None if (None == arg_oList) or (0 == Len(arg_oList)) else arg_oList[-1]


    def DeleteAll(self):
        del self.m_oList[:]
        return


    def Remove(self, arg_oElement):
        if (None != self.m_oList) and (0 == Len(self.m_oList)):
            self.m_oList.remove(arg_oElement)
        if None == arg_oElement:
            DeleteAll()
        return


    #未完工，考慮泛型，如果元素不是列表未必能用append方法
    def TopAppend(self, arg_oObject):
        if (None == self.m_oList) or (0 == Len(self.m_oList)):
            self.m_oList = [arg_oObject]
        else:
            self.m_oList[-1].append(arg_oObject)
        return


    #未完工，考慮用 = 重載方式實現
    def TopReplace(self, arg_oObject):
        if (None == self.m_oList) or (0 == Len(self.m_oList)):
            self.m_oList = [arg_oObject]
        else:
            self.m_oList[-1] = arg_oObject
        return


    def Size(self):
        return 0 if None == self.m_oList else Len(self.m_oList)


    def GetElement(self, arg_iSubscript):
        if abs(arg_iSubscript) > Len(self.m_oList):
            return None
        return self.m_oList[arg_iSubscript]