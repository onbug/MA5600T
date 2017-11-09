#coding:utf-8

#!/usr/bin/python

import VOS

XXX = 0



class CMDSTK_Node(object):
    def __init__(self, arg_oCmdNode = None, arg_Attribute = None, arg_cCh = None):
        self.m_oCmdNode = arg_oCmdNode
        self.m_Attribute = arg_Attribute
        self.m_cCh = arg_cCh
        return


    def GetCmdNode(self):
        return self.m_oCmdNode

        
    def GetAttribute(self):
        return self.m_Attribute