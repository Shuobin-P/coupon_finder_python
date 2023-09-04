#!/bin/bash
# 设置时区为Asia/Shanghai
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
# 同步系统时间
ntpd -q -g
