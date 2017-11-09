#coding:utf-8

#!/usr/bin/python

import socket, struct, os, time
import VOS
import CCmd


#display ip routing-table回調函式
def CMD_DisplayIpRoutingTable():
    CCmd.ExecStringOut("cmd \'display ip routing-table [verbose]\' has been called!")
    return
