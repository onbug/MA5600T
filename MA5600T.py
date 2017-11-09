#coding:utf-8

#!/usr/bin/python

#import msvcrt, sys, ctypes, os
import threading

#import VOS
import CCmd
#import VVRP

threads = []

def main():
    #初始化MA5600T
    #VOS初始化
    #VOS.Init()
    global threads
    #創建VOS線程
    #hVOS = threading.Thread(target = VOS.Main, name = "VOS Main", args = ())
    #hVOS.start()
    #threads.append(hVOS)

    oCmd = CCmd.CCmd()
    #啟動命令行線程
    hCmd = threading.Thread(target = oCmd.Main, name = "CMD Main", args = ())
    hCmd.start()
    threads.append(hCmd)

    #初始化VVRP
    #VVRP.Init()

    for i in range(len(threads)):
        threads[i].join()

    return


if "__main__" == __name__:
    main()
