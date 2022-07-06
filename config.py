DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'  # 用户名
PASSWORD = 'Sd_12345'  # 密码
HOST = '127.0.0.1'  # IP
PORT = '3306'  # 端口号
DATABASE = 'byrsjyzx'  # 数据库名字

SERVER_HOST1 = "172.21.159.190"  # 外网IP
SERVER_HOST2 = "172.21.159.190"  # 内网IP
STATIC_FILE_PATH = "/data/local/lib/byrsjPro"
CONTROLLER_KEY = "ed803dfa-4900-4984-9c16-dba798a24537"

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,
                                                                       DATABASE)

SQLALCHEMY_BINDS = {
    'bysjybt': 'mysql://{}:{}@127.0.0.1:3306/bysjybt?charset=utf8&autocommit=true'.format(USERNAME,PASSWORD),  # 连接多方数据库
    'cyddjybt': 'mysql://{}:{}@127.0.0.1:3306/cyddjybt?charset=utf8&autocommit=true'.format(USERNAME,PASSWORD),
    'ycxcyzz': 'mysql://{}:{}@127.0.0.1:3306/ycxcyzz?charset=utf8&autocommit=true'.format(USERNAME,PASSWORD),
}
SQLALCHEMY_TRACK_MODIFICATIONS = False
