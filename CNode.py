#coding:utf-8

#!/usr/bin/python

import VOS

CNODE_REQUIRED = 0
CNODE_ALIAS = 1
CNODE_OPTIONAL = 2

CNODE_IPV4_ADDRESS = 3
CNODE_IPV6_ADDRESS = 4
CNODE_VLAN_ID = 5
CNODE_INTERFACE_CARD = 6
CNODE_INTERFACE_MODULE = 7
CNODE_INTERFACE_NO = 8

MATCHING_ON = 9
NO_MATCHING = 10
PARTLY_MATCHING = 11

class CMD_Node(object):
    def __init__(self, arg_oNextNode = None, arg_oSubNode = None, arg_strKeyword = None, arg_strHelpInfo = None, arg_fCmdProc = None):
        self.m_oNextNode = arg_oNextNode
        self.m_oSubNode = arg_oSubNode
        self.m_strKeyword = arg_strKeyword
        self.m_Attribute = None
        self.m_strHelpInfo = arg_strHelpInfo
        self.m_fCmdProc = arg_fCmdProc
        
        if True == self.IsOptionalKeyword():
            self.m_Attribute = CNODE_OPTIONAL
        elif True == self.IsParameterKeyword():
            self.SetParameterType()
        else:
            self.m_Attribute = CNODE_REQUIRED
        return


    def SetParameterType(self):
        if "$ipv4-address" == self.m_strKeyword:
            self.m_Attribute = CNODE_IPV4_ADDRESS
        elif "$ipv6-address" == self.m_strKeyword:
            self.m_Attribute = CNODE_IPV6_ADDRESS
        elif "$vlan-id" == self.m_strKeyword:
            self.m_Attribute = CNODE_VLAN_ID
        elif "$interface-card" == self.m_strKeyword:
            self.m_Attribute = CNODE_INTERFACE_CARD
        elif "$interface-module" == self.m_strKeyword:
            self.m_Attribute = CNODE_INTERFACE_MODULE
        elif "$interface-no" == self.m_strKeyword:
            self.m_Attribute = CNODE_INTERFACE_NO
        else:
            pass
        self.m_strKeyword = None
        return


    def IsOptionalKeyword(self):
        return True if (('[' == self.m_strKeyword[0]) and (']' == self.m_strKeyword[-1])) else False


    def IsParameterKeyword(self):
        return True if ('$' == self.m_strKeyword[0]) else False


    def IsRequired(self):
        return True if(CNODE_REQUIRED == self.m_Attribute) else False


    #返回值：NO_MATCHING        未匹配（如asdf、displayaaa）
    #      PARTLY_MATCHING    部分匹配（如disp）
    #      MATCHING_ON        完全匹配
    def KeywordMaxCompare(self, arg_strSegment = None):
        if None == arg_strSegment:
            return NO_MATCHING, None

        #假設節點為display

        #displayaaa
        elif VOS.Len(arg_strSegment) > VOS.Len(self.m_strKeyword):
            return NO_MATCHING, None
        
        #display
        elif arg_strSegment == self.m_strKeyword:
            return MATCHING_ON, self.m_strKeyword
        
        #disp
        elif arg_strSegment == self.m_strKeyword[0:VOS.Len(arg_strSegment)]:
            return PARTLY_MATCHING, self.m_strKeyword

        #asdf
        else:
            return NO_MATCHING, None


    def GetNextNode(self):
        return self.m_oNextNode


    def GetKeyword(self):
        return self.m_strKeyword