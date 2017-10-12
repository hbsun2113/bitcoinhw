#!/usr/bin/env python

import os
import time

for ctrl_idx in range(1, 5):
    gp_name = "nodes_21"#这个测试组名称的group name
    spacing = 10*ctrl_idx #spacing 区块间隔,秒为单位（我认为就是每隔多久产生一个区块）
    interval = 50 #interval 几个区块重算一次难度
    ctn_amount = 20 #几个节点，即container的数量
    nw_delay = 0 #nw_delay 网络延迟（毫秒）
    nw_loss = 0 #网络丢包（百分率，与nw_delay不可同时非零）
    cpu_quota = 1000 #CFS中给每个容器的cpu权重
    cpu_period = cpu_quota * (ctn_amount + 1) #CFS总权重

    dfcl_bias = 25
    time_bias = 200
    time_window = spacing * time_bias
    net_wait = 2 * 60 * 60
    dfcl_wait = 4 * 60 * 60
    ctn_memory = "20m"
    proj_path = "/root/btcl"

    nw_cmd = ""
    if nw_delay != 0:
        nw_cmd += "tc qdisc add dev eth0 root netem delay {}ms && ".format(nw_delay)
    if nw_loss != 0:
        nw_cmd += "tc qdisc add dev eth0 root netem loss {}% && ".format(nw_loss)
    ts_name = "{}_s{}i{}c{}d{}l{}q{}p{}f{}t{}".format(gp_name,spacing, interval, 
        ctn_amount, nw_delay, nw_loss, cpu_quota, cpu_period, dfcl_bias, time_bias)
    gp_path = "{}/{}".format(proj_path, gp_name)
    ts_path = "{}/{}".format(gp_path, ts_name)

    try:
        # run containers
        for nd_idx in range(ctn_amount):
            ctn_cmd = """docker run --cpu-period={cpu_period} --cpu-quota={cpu_quota} -m {ctn_memory} --rm(Clean Up ) -d(后台启动) \
            --memory-swap(好像没什么用，因为这个参数的数值小于-m) 0m --cap-add=NET_ADMIN(添加权限：默认情况下，docker的容器中的root的权限是有严格限制的，比如，网络管理（NET_ADMIN等很多权限都是没有的。) -v {proj_path}/bitcoind:/bitcoind \
            -v(挂载) {ts_path}/node{nd_idx}:/bitcoin_data \
            bitcoinl:base(镜像的名称) /bin/bash -c(选项表明string中包含了一条命令) "{nw_cmd} /bitcoind/bitcoind(一下就都是bitcoin的命令了) -spacing={spacing} -interval={interval} \
            -conf(dockfile中写入了rpcuser和password)=/root/.bitcoin/bitcoin.conf -datadir=/bitcoin_data(只是用来产生日志？) -gen(生成比特币——挖矿，-gen=0表示不生成比特币) -addnode=172.17.0.2(添加一个节点以供连接，并尝试保持与该节点的连接，并且告知您的节点所有与它相连接的其它节点，另外它还会将您的节点信息告知与其相连接的其它节点，这样它们也可以连接到您的节点)"
            """.format(cpu_period, cpu_quota, ctn_memory, proj_path, 
                ts_path, nd_idx, nw_cmd, spacing, interval)
            os.system(ctn_cmd)
        print "Test name: {}, all container ran. Checking net status.".format(ts_name)

        # check network established
        net_established = True
        print "Test name: {}. Checking net status.".format(ts_name)
        for atp_idx in range(net_wait/60):#最坏的情况下会等待net_wait(秒为单位)个时间，还没有建立的话会退出，否则每一分钟检查一次，一共检查net_wait／60次
            time.sleep(60)
            net_established = True
            for nd_idx in range(ctn_amount):
                outbound = 0
                inbound = 0
                disconnect = 0
                with open("{}/node{}/debug.log".format(ts_path, nd_idx), 'r') as ndlog:
                    for line in ndlog:
                        if "connected" in line:
                            outbound += 1
                        if "accepted connection" in line:
                            inbound += 1
                        if "disconnecting" in line:
                            disconnect += 1
                if outbound+inbound-disconnect < 2:
                    net_established = False
                    print "Node{} not ready: {}.".format(nd_idx, (outbound, inbound, disconnect))
            if net_established:
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print "Net established."
                break
            else:
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print "Sleep now\n-----"
        if not net_established:
            print "Can't establish network."
            exit()


        # check difficulty converged 每spacing产生一个区块，每interval计算一次难度，所以难度检测的时间间隔为spacing*interval
        dfcl_converged = True
        print "Test name: {}. Checking difficulty converged.".format(ts_name)
        for atp_idx in range(dfcl_wait/600):
            time.sleep(10*60)#每10min检查一次
            dfcl_converged = True
            for nd_idx in range(ctn_amount):
                actual_span = [0,]
                with open("{}/node{}/debug.log".format(ts_path, nd_idx), 'r') as ndlog:
                    for line in ndlog:
                        if "nActualTimespan" in line and "nTargetTimespan" in line:
                            newspan = int(line.strip().split()[-1])
                            if newspan != actual_span[-1]:
                                actual_span.append(newspan)
                    if len(actual_span) < 3:
                        dfcl_converged = False
                    else:
                        for idx in range(1, 3):
                            if abs(spacing*interval - actual_span[-idx]) > spacing*interval*dfcl_bias/100:
                                dfcl_converged = False
                    if not dfcl_converged:
                        print "Target timespan: {}".format(spacing*interval)
                        print "Actual timespan of node{}: {}".format(nd_idx, actual_span)
                        break#只要有一个节点不收敛，立即sleep，并且进行下一次判断
            if dfcl_converged: #所有节点都判断收敛
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print "Difficulty converged."
                break
            else:
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print "Sleep now\n-----"
        if not dfcl_converged:
            print "Difficulty not converged."
            exit()


        # monitoring
        start_time = -1
        for nd_idx in range(ctn_amount):
            with open("{}/node{}/debug.log".format(ts_path, nd_idx), 'r') as ndlog:
                for line in ndlog:
                    if line[:11] == "CBlock(hash":
                        newtime = int([k[k.find('=')+1: -1] for k in line.split()][4])
                        if newtime > start_time:
                            start_time = newtime
        stop_time = start_time + time_window
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print "Monitor start_time set as {}. Will stop after {} seconds.".format(start_time, time_window)
        time.sleep(int(time_window*1.05))

        print "Start counting."
        cblks = set()
        for nd_idx in range(ctn_amount):
            with open("{}/node{}/debug.log".format(ts_path, nd_idx), 'r') as ndlog:
                for line in ndlog:
                    if line[:11] == "CBlock(hash":
                        tmp = [k[k.find('=')+1: -1] for k in line.split()]
                        cblks.add((tmp[0], tmp[2], int(tmp[4]))) # hash, prevhash, ntime

        prev2leaf = dict()#  prevhash->hash
        leaf2prev = dict()#  hash->prevhash
        for k in cblks:
            if k[1] not in prev2leaf:
                prev2leaf[k[1]] = list()
            prev2leaf[k[1]].append(k[0])
            if k[0] in leaf2prev:   
                print "Error: ", k[0]   #hash只能出现一次喽
            leaf2prev[k[0]] = k[1]
        hh = dict()  #记录了累加次数 hash->time
        hh["00000000000000000000"] = 0
        stack = list()
        stack.append("00000000000000000000")
        while True:
            k = stack.pop(0)
            for leaf in prev2leaf[k]:
                hh[leaf] = hh[k] + 1 #孩子比父亲的累加值多于1
                if leaf in prev2leaf:#作为种子节点压栈
                    stack.append(leaf)
            if len(stack) == 0:
                break

        fine_blks = set([k[0] for k in cblks if start_time< k[2]<= stop_time])  #(规定一下当前的监视时间)
        maxh = -1 #最大次数(记得是当前的测试测时间哦)
        hhk = ""  #记录最大次数的节点的hash值(记得是当前的测试测时间哦)
        for k in fine_blks:
            if hh[k] > maxh:
                hhk = k
                maxh = hh[k]
        tail = hhk #记录最大次数的节点的祖宗节点的hash值(记得是当前的测试测时间哦)
        while tail in fine_blks:
            tail = leaf2prev[tail] 
        mainh = hh[hhk] - hh[tail] #次数差值
        print ts_name, mainh, len(fine_blks) #测试名称 增长最快的分支所增长的长度(high increased of highest chain) 监视窗口内总共生成了多少个区块的数目(total blocks generated)
        with open("{}/result.log".format(gp_path), 'a') as fp:
            fp.write("{}\t{}\t{}\n".format(ts_name, mainh, len(fine_blks)))

        # clean up
        print "Test name: {}, finished.".format(ts_name)
        os.system("docker kill $(docker ps -q)")
        print "Test name: {}, cleaned.".format(ts_name)

    except Exception, e:
        print e
        os.system("docker kill $(docker ps -q)")

print "Group: {} finished".format(gp_name)



http://8btc.com/article-1702-1.html

addnode这一选项的作用是啥？固定了自己监听的端口号了吗？如何允许自己连接他人，如何允许他人连接自己？
答案：每个节点至少会连接其他8个节点(主动+被动)，被动连接监听固定端口：8233，主动连接的时候是随机选取端口。
真实网络中也是有种子节点的，只是不止一个，自己做的时候可以考虑多加一些种子节点哈(但是基于什么策略加呢)。

起了这么多容器，作用是不是就是挖矿啊，其他比特币网络中的行为其实都没有模拟？
答案：是。自己可以考虑再加一些行为。比如交易。

check network established中我写的注释对吗？
答案：对。

outbound+inbound-disconnect < 2这个公式哪里来的？  
答案：自己定义的。outbound——主动连接的数量 inbound——被动连接的数量 disconnect——之前建立的连接被取消的数量(节点数目>50才会发生)

为什么 len(actual_span) < 3，难度就不收敛？是因为数目太少吗，数目<3的话一定不稳定吗？理论依据是？
答案：自定义的 真实网络中不需要考虑——真实网络中默认难度已经收敛了，因为真实比特币系统已经运行了很久，难度是否收敛这件事情只在比特币系统刚刚运行的时候需要考虑。
由于我们模拟的这个系统是从头开始，因此一开始难度是不收敛的，因此需要等待收敛。

为什么要这么设置：actual_span = [0,]？
答案：第一个元素可以为任意值，陈辰设置的是只要倒数第一个和倒数第二个的难度和目标值差距不大(百分25)，就认为难度收敛。难度收敛之后，才开始监控的。

128行代码睡眠时间的设定有什么含义吗？
答案：只是在等待LOG写入，其实没有必要是time_window*1.05，设置time_window+30就可以————认为30s内就可以写入文件完毕。参看161行代码，会明白time_window是如何起作用的。

146行代码为什么hash只能出现一次？ 
答案：在测试哈希碰撞，其实没有什么意义。

172行代码的这几个数据说明了什么？

bitcoin命令行和官方的比，可以接受哪些可变参数？ 
答案：自己 --h 查看即可。

time_window和spacing的关系，time_bias根据什么设置为200？

种子节点是随机选取的吗？我要想多加几个种子节点的话，种子节点需要满足什么策略呢？







