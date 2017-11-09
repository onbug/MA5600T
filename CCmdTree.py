#coding:utf-8

#!/usr/bin/python

import struct, re, time, os

import VOS
import CNode

'''
display------------------------vrrp-----------------------ip--------------------ipos
|                               |                         |
|                               |                         |
version--------ip            timer-adv                 interface
               |                |
               |                |
          routing-table      learning
                                |
                                |
                              enable
'''

#唯一、完整匹配上，如display
SOLE_WHOLE_MATCHING_ON = 0

#唯一、部分匹配上，如disp唯一匹配display
SOLE_PARTLY_MATCHING_ON = 1

#多項、部分匹配上，如i匹配ip、interface
MULTI_MATCHING_ON = 2

#唯一匹配上（也不知道是完整匹配上的還是部分匹配上的）
SOLE_MATCHING_ON = 3

#沒匹配上
NO_MATCHING = 4

ERROR = 5

class CCmdTree(object):
    def __init__(self, arg_oRootNode = None):
        self.m_oRootNode = arg_oRootNode
        return


    def RegCmd(self, arg_strCmd, arg_strHelpInfo, arg_fCmdProc):
        oNodeArray = []
        oKeywordArray = arg_strCmd.split(' ')

        #準備待註冊命令的節點串
        for strKeyword in oKeywordArray:
            #新建一個節點
            #strKeyword裡可能帶有$、[]等等特殊標識，由Node處理
            if 0 < VOS.Len(strKeyword):
                oNode = CNode.CMD_Node(arg_strKeyword = strKeyword)
                oNodeArray.append(oNode)

        #串接起來
        self.MakeCmdNodesLink(oNodeArray)

        def AppendCmdProc(arg_oNodeArray = None, arg_fCmdProc = None):
            if (None == arg_oNodeArray) or (None == arg_fCmdProc):
                return
            
            def GetLastRequiredNode(arg_oNodeArray = None):
                for oNode in reversed(arg_oNodeArray):
                    if True == oNode.IsRequired():
                        return oNode
                return

            #獲取最後一個必填節點
            oNode = GetLastRequiredNode(arg_oNodeArray)
            if None != oNode:
                oNode.m_fCmdProc = arg_fCmdProc
            return

        #加上回調函式
        AppendCmdProc(oNodeArray, arg_fCmdProc)

        self.Insert(oNodeArray)
        return


    def Insert(self, arg_oNodeArray):
        #空樹
        if True == self.IsEmptyTree():
            self.m_oRootNode = arg_oNodeArray[0]
        else:
            #對比
            self.NodeKeywordCompareInsert(self.m_oRootNode, arg_oNodeArray[0])
        return


    def NodeKeywordCompareInsert(self, arg_oRootNode, arg_oNode):
        oRootNode = arg_oRootNode
        if oRootNode.m_strKeyword == arg_oNode.m_strKeyword:
            self.NodeKeywordCompareInsert(oRootNode.m_oSubNode, arg_oNode.m_oSubNode)
        else:
            if None == oRootNode.m_oNextNode:
                oRootNode.m_oNextNode = arg_oNode
            else:
                self.NodeKeywordCompareInsert(arg_oRootNode.m_oNextNode, arg_oNode)
        return


    def MakeCmdNodesLink(self, arg_oNodeArray = None):
        if (None == arg_oNodeArray) or (1 == VOS.Len(arg_oNodeArray)):
            return
        else:
            for i, oNode in enumerate(arg_oNodeArray):
                if (VOS.Len(arg_oNodeArray) - 1) != i:
                    oNode.m_oSubNode = arg_oNodeArray[i + 1]
        return


    #遞歸函式
    def _DbgPrintTree(self, arg_oRootNode):
        oMainNode = arg_oRootNode
        while None != oMainNode:
            print("m: %s - attr = %s - m_fCmdProc = %s" % (oMainNode.m_strKeyword, oMainNode.m_Attribute, oMainNode.m_fCmdProc))

            oAuxiliaryNode = oMainNode.m_oSubNode
            while None != oAuxiliaryNode:
                print("a: %s - attr = %s - m_fCmdProc = %s" % (oAuxiliaryNode.m_strKeyword, oAuxiliaryNode.m_Attribute, oAuxiliaryNode.m_fCmdProc))
                #遞歸點
                self._DbgPrintTree(oAuxiliaryNode)
                oAuxiliaryNode = oAuxiliaryNode.m_oSubNode
            oMainNode = oMainNode.m_oNextNode
        return


    def IsEmptyTree(self):
        return True if None == self.m_oRootNode else False


    #精確匹配、最大匹配
    #如ip匹配ip
    #如i匹配ip、interface等
    def NextNodeMaxMatching(self, arg_oRootNode = None, arg_strSegment = None):
        #沒指定根節點就用整個命令樹的根節點
        if None == arg_oRootNode:
            arg_oRootNode = self.m_oRootNode

        oCurrentNode = arg_oRootNode
        MatchingCount = 0
        oNode = None
        strKeyword = None

        while None != oCurrentNode:
            #如果註冊關鍵字的長度小於輸入關鍵字，顯然匹配失敗
            #情形一：display
            #精確匹配上仍需遍歷全樹，看看有無其他節點部分匹配
            #考慮ip，與ip節點完全匹配（MATCHING_ON），同時與ipos節點部分匹配（PARTLY_MATCHING_ON），這種情況將產生多重匹配
            iRetCode, strTempKeyword = oCurrentNode.KeywordMaxCompare(arg_strSegment)

            #精確（唯一）匹配
            if CNode.MATCHING_ON == iRetCode:
                strKeyword = strTempKeyword
                oNode = oCurrentNode
                #一旦精確匹配，就可以返回了
                return SOLE_MATCHING_ON, strKeyword, oNode

            #部分匹配
            elif CNode.PARTLY_MATCHING == iRetCode:
                strKeyword = strTempKeyword
                oNode = oCurrentNode
                MatchingCount += 1
                #這裡由於尚未遍歷完整棵樹，所以還不能判斷部分匹配的是否是唯一匹配，如i或ip匹配ip或ipos的情況，所以不能返回

            oCurrentNode = oCurrentNode.GetNextNode()

        #無匹配
        if 0 == MatchingCount:
            return NO_MATCHING, None, None

        #唯一匹配
        elif 1 == MatchingCount:
            return SOLE_MATCHING_ON, strKeyword, oNode

        #多匹配
        elif 1 < MatchingCount:
            return MULTI_MATCHING_ON, None, None

        else:
            return ERROR, None, None