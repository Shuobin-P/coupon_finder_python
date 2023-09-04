FROM python:3.8
# 设置工作目录
WORKDIR /app
# 复制应用程序代码到容器中
COPY . /app
# 安装项目依赖项

RUN apt-get update && \
    apt-get install -y ntp && \
    chmod +x /app/set_time.sh && \
    /app/set_time.sh && \
    pip install -r requirements.txt

ENV FLASK_APP=app/__init__.py
# 暴露应用程序的端口（Flask 默认是 5000 端口）
EXPOSE 5000
# 设置容器启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]