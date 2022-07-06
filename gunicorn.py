import multiprocessing

# 绑定端口
bind = '0.0.0.0:5000'
backlog = 512
# 启动目录
chdir = '/usr/local/lib/jyzx'
# timeout = 30
# 工作方式
worker_class = 'eventlet'
# 设置最大并发量
worker_connections = 2000

# 指定每个进程开启的线程数
workers = multiprocessing.cpu_count() * 2 + 1
# 指定每个进程开启的线程数
threads = 2
# 设置日志记录水平
loglevel = 'info'
# 设置进程文件目录
pidfile = 'gunicorn.pid'

# 访问日志文件
accesslog = "./logs/gunicorn_access.log"
# 错误日志文件
errorlog = "./logs/gunicorn_error.log"
# 代码发生变化是否自动重启
reload = True
