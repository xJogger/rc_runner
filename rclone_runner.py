#!/usr/bin/env python3

import os
import sys
import time
import base64
import signal
import subprocess
import requests

def to64(input_str):
    return base64.b64encode(input_str.encode('utf8')).decode('utf8')
def from64(input_str):
    return base64.b64decode(input_str).decode('utf8')
def print_check(input_str):
    res = to64(input_str)
    print(res)
    print(10*'=',from64(res)==input_str,10*'=')

def write_config(config_path,rclone_config):
    with open(config_path,'w') as f:
        f.writelines(rclone_config)

def get_info(log_path):
    cmd = f'tail -n 10 {log_path}  | grep --color=never -o Transferred.*'
    out_bytes = subprocess.check_output(cmd,shell=True)
    out_text  = out_bytes.decode('utf-8')
    line = out_text.split('\n')[-3]
    line = line.replace('Transferred:','')
    line = line.strip()
    info = line.split(',')
    transfered = info[0].replace('iByte','').replace('i','')
    percentage = info[1]
    return transfered,percentage.strip(),line

def run_job(args,job_time,log_path): # time单位：s
    start_time = time.time()
    process = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    while process.poll()==None:
        time.sleep(1)
        elapsed_time = int(time.time() - start_time)
        try:
            _,_,line = get_info(log_path)
        except:
            print('信息读取错误')
            line = str(0)
        print(line)
        if elapsed_time > job_time :
            os.killpg(process.pid, signal.SIGTERM)
            return 1 # 超时退出
    return 0 # 正常退出

def main():
    home_path     = sys.argv[1]
    rclone_config = from64(sys.argv[2])
    cmd_in        = from64(sys.argv[3]) # 示例：rclone sync remote1:path remote2:path --exclude=**/.@__thumb/** 
    push_url      = from64(sys.argv[4]) # 示例：https://wx.vercel.app/11223344.send

    log_path      = os.path.join(home_path,'rclone.log')
    config_path   = os.path.join(home_path,'rclone.conf')
    cmd           = cmd_in + f' --progress --transfers 4 --config="{config_path}" > {log_path} 2>&1'
    job_time      = 5*3600 # 五个小时的秒数 Github action单次最长5小时

    write_config(config_path,rclone_config)
    requests.post(push_url, data={"text" : f"Github传输已开始"})
    code     = run_job(cmd,job_time,log_path)
    if code == 1:
        res = '超时结束'
    elif code==0:
        res = '正常结束'
    else:
        res = '异常结束'
    try:
        transfered,percentage,_ = get_info(log_path)
    except:
        transfered = str(0)
        percentage = str(0)
        print('信息读取错误')
    requests.post(push_url, data={"text" : f'Github传输已完成({percentage})：\n{transfered}\n({res})'})

if __name__ == '__main__':
    main()
