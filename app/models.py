# from flask_migrate import Migrate, MigrateCommand
# from flask_script import Shell, Manager
# import config
import pymysql
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TIMESTAMP, text
from sqlalchemy.sql import func

pymysql.install_as_MySQLdb()
USER = "root"
PASSWORD = "Sd_12345"
SQLALCHEMY_DATABASE_URI = 'mysql://{}:{}@127.0.0.1:3306/byrsjyzx?charset=utf8&autocommit=true'.format(USER, PASSWORD)

app = Flask(__name__)
# manager = Manager(app)

# app.config.from_object('../config.py')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_BINDS'] = {
    'bysjybt': 'mysql://{}:{}@127.0.0.1:3306/bysjybt?charset=utf8&autocommit=true'.format(USER, PASSWORD),
    "cyddjybt": 'mysql://{}:{}@127.0.0.1:3306/cyddjybt?charset=utf8&autocommit=true'.format(USER, PASSWORD),
    "ycxcyzz": 'mysql://{}:{}@127.0.0.1:3306/ycxcyzz?charset=utf8&autocommit=true'.format(USER, PASSWORD)
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# migrate = Migrate(app, db)
# manager.add_command('db', MigrateCommand)


# db.create_all()

# todo:====================================招用工补贴=====================================
# todo:======================================================================================
class CompanyInfo(db.Model):
    """
    公司信息列表
    """
    __tablename__ = 'company_info'
    # 基本信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    c_apply_num = db.Column(db.String(255), nullable=False)  # 申领编号，公司唯一ID
    c_register_num = db.Column(db.String(255), nullable=True)  # 统一信用证代码
    c_name = db.Column(db.String(255), nullable=True)  # 公司名称
    c_social_num = db.Column(db.String(255), nullable=True)  # 公司社保号
    c_size = db.Column(db.String(255), nullable=True)  # 企业规模
    c_bank = db.Column(db.String(255), nullable=True)  # 开户银行
    c_account = db.Column(db.String(255), nullable=True)  # 开户户名
    c_bank_card = db.Column(db.String(255), nullable=True)  # 银行账号
    c_charge_ID = db.Column(db.String(255), nullable=True)  # 法人证件号码
    c_charge_name = db.Column(db.String(255), nullable=True)  # 法人名字
    c_contact_name = db.Column(db.String(255), nullable=True)  # 单位联系人
    c_contact_phone = db.Column(db.String(255), nullable=True)  # 联系电话
    c_apply_count = db.Column(db.Integer, nullable=True)  # 申领人数
    c_hard_employ_count = db.Column(db.Integer, nullable=True)  # 就业困难人数
    c_graduate_count = db.Column(db.Integer, nullable=True)  # 高校毕业生人数
    c_army_count = db.Column(db.Integer, nullable=True)  # 随军家属
    c_affect_person_count = db.Column(db.Integer, nullable=True)  # 受影响职工

    c_poor_count = db.Column(db.Integer, nullable=True)  # 建档立卡贫困劳动人数
    c_total = db.Column(db.Integer, nullable=True)  # 合计
    c_old_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 养老保险金额
    c_unemploy_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 失业保险金额
    c_injury_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 工伤保险金额
    c_birth_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 生育保险金额
    c_medical_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 医疗保险金额
    c_social_total = db.Column(db.DECIMAL(10, 2), nullable=True)  # 社保补贴合计
    c_general_post_subsidy = db.Column(db.DECIMAL(10, 2), nullable=True)  # 一般性岗位补贴
    c_special_fund_count = db.Column(db.Integer, nullable=True)  # 专项资金人数
    c_unemploy_fund_count = db.Column(db.Integer, nullable=True)  # 失业基金人数
    c_net_office = db.Column(db.Boolean, nullable=True)  # 是否网办提交
    c_special_fund = db.Column(db.DECIMAL(10, 2), nullable=True)  # 专项资金金额
    c_unemploy_fund = db.Column(db.DECIMAL(10, 2), nullable=True)  # 失业基金金额
    c_success_count = db.Column(db.Integer, nullable=True)  # 成功人数
    c_success_fund = db.Column(db.DECIMAL(10, 2), nullable=True)  # 成功总金额
    c_fail_count = db.Column(db.Integer, nullable=True)  # 失败人数
    c_fail_fund = db.Column(db.DECIMAL(10, 2), nullable=True)  # 失败总金额
    # state 各种状态
    c_robot_result = db.Column(db.Boolean, nullable=True)  # 机器人预审结果0为不通过1为通过)
    c_explain = db.Column(db.String(255), nullable=True)  # 预审说明
    c_detail = db.Column(db.Text, nullable=True)  # 预审详情
    c_get_person_state = db.Column(db.Boolean, nullable=False, server_default=text('False'))  # 抓取员工数据状态0为未完成1为完成
    c_search_charge = db.Column(db.String(255), nullable=True)  # 法人名字结果(数据来源：市场监督局)
    c_search_location = db.Column(db.String(255), nullable=True)  # 企业地址结果(数据来源：市场监督局)
    c_search_name = db.Column(db.String(255), nullable=True)  # 企业名称结果
    c_search_operatingStatus = db.Column(db.String(255), nullable=True)  # 企业经营状态
    c_person_result = db.Column(db.Boolean, nullable=True)  # 人工审核结果(0为不通过1为通过)
    c_date = db.Column(db.DateTime, nullable=True)  # 审核时间
    c_identify_person = db.Column(db.String(255), nullable=True)  # 审核人
    c_identify_comment = db.Column(db.Text, nullable=True)  # 审核说明
    c_apply_season = db.Column(db.String(255), nullable=True)  # 申报年季
    c_isnet = db.Column(db.Boolean, nullable=True)  # 是否网办(0为否1为是)
    c_isprovince = db.Column(db.Boolean, nullable=True)  # 是否省投保0为否1为是)
    c_isseason = db.Column(db.Boolean)  # 是否本季度新增0为否1为是)
    c_season_add_count = db.Column(db.Integer, nullable=True)  # 本季度新增人数
    isIdentify = db.Column(db.Boolean, nullable=True)  # 企业是否可审核
    c_audit_order = db.Column(db.Integer, nullable=True, server_default=text('0'))  # 审核顺序

    # 额外参数
    c_extra_social_count = db.Column(db.Integer, nullable=True)  # 参保人数
    c_outputFile = db.Column(db.Boolean, server_default=text("False"))  # 是否导出过表格
    c_isSendEmail = db.Column(db.Boolean, server_default=text("False"))  # 是否发送过短信

    # 街道审核新增字段
    c_street_author = db.Column(db.String(255), nullable=True)  # 街道审核人
    c_street_result = db.Column(db.Boolean, nullable=True)  # 街道审核结果
    c_street_comment = db.Column(db.String(255), nullable=True)  # 街道审核结果
    c_street_belong = db.Column(db.String(255), nullable=True)  # 所属区街

    # 2022-2季度新增
    c_has_repeat_person = db.Column(db.Boolean, nullable=True)  # 是否有重复人员
    c_repeat_detail = db.Column(db.String(255), nullable=True)  # 重复人员信息

    # 时间
    c_create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    c_update_time = db.Column(TIMESTAMP, nullable=False)  # 更新时间


class PersonInfo(db.Model):
    """
    人员信息表
    """
    __tablename__ = 'person_info'
    # 基本信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    p_c_apply_num = db.Column(db.String(255), nullable=False)  # 关联公司的申领编号（一对多）
    p_list_place = db.Column(db.String(255), nullable=False)  # 人员所在列表(0为成功，1为失败，2为待审核)
    p_ID_type = db.Column(db.String(255), nullable=False)  # 证件类型
    p_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    p_name = db.Column(db.String(255), nullable=False)  # 名字
    p_sex = db.Column(db.String(255), nullable=False)  # 性别
    p_age = db.Column(db.Integer, nullable=False)  # 年龄
    p_type = db.Column(db.String(255), nullable=False)  # 人员类型
    p_hard_type = db.Column(db.String(255), nullable=False)  # 就业困难类别
    p_contract_start_date = db.Column(db.String(255), nullable=False)  # 合同起始日期
    p_contract_end_date = db.Column(db.String(255), nullable=False)  # 合同结束日期
    p_old_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 养老保险
    p_injury_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 工伤保险
    p_unemploy_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 失业保险
    p_medical_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 医疗保险
    p_birth_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 生育保险

    p_society_total = db.Column(db.DECIMAL(10, 2), nullable=True)  # 社保补贴合计
    p_normal_fund = db.Column(db.DECIMAL(10, 2), nullable=True)  # 一般性岗位补贴
    p_apply_month = db.Column(db.Integer, nullable=True)  # 申领月数
    p_iscarry = db.Column(db.Boolean, nullable=False)  # 是否结转(0为否1为是)
    p_unemploy_register = db.Column(db.String(255), nullable=False)  # 失业登记退出去向
    p_verify_explain = db.Column(db.String(255), nullable=False)  # 审核说明
    p_pass_num = db.Column(db.String(255), nullable=True)  # 通行证号码
    p_social_num = db.Column(db.String(255), nullable=True)  # 个人社保号
    p_disabled_num = db.Column(db.String(255), nullable=True)  # 残疾人证书号码
    p_isgraduate = db.Column(db.String(255), nullable=True)  # 是否毕业2年内(0为否1为是)
    p_graduate_type = db.Column(db.String(255), nullable=True)  # 毕业生类别
    p_graduate_school = db.Column(db.String(255), nullable=True)  # 毕业院校
    p_graduate_date = db.Column(db.String(255), nullable=True)  # 毕业时间
    p_pass_date = db.Column(db.String(255), nullable=True)  # 考核合格时间
    p_isprovince = db.Column(db.String(255), nullable=False)  # 是否省投保为否1为是)
    p_help_type = db.Column(db.String(255), nullable=True)  # 资助类型
    p_reamark = db.Column(db.Text, nullable=True)  # 备注
    p_new_comment = db.Column(db.Text, nullable=True)  # 新增审核说明
    p_identify_date = db.Column(db.String(255), nullable=True)  # 经办日期
    p_local_area = db.Column(db.String(255), nullable=True)  # 经办机构

    # 人员的失业登记日期、困难认定日期和就业登记日期
    p_start_unemploy_date = db.Column(db.String(255), server_default='-')  # 失业始期 用于导出报表
    p_end_unemploy_date = db.Column(db.String(255), server_default='-')  # 失业终期 用于导出报表
    p_hard_identify_date = db.Column(db.String(255), server_default='-')  # 困难认定日期 用于导出报表
    p_start_contract_date = db.Column(db.String(255), server_default='-')  # 合同始期 用于导出报表
    p_end_contract_date = db.Column(db.String(255), server_default='-')  # 合同终期 用于导出报表
    p_contract_register_date = db.Column(db.String(255), server_default='-')  # 合同登记日期

    # state 各种状态
    p_detail_pay_state = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 是否抓取了补贴月份表格
    p_robot_result = db.Column(db.Boolean, nullable=True)  # 机器人预审结果False为不通过，True为通过)
    p_explain = db.Column(db.String(255), nullable=True)  # 预审说明
    p_detail = db.Column(db.Text, nullable=True)  # 预审详情
    p_medical_check = db.Column(db.Boolean, nullable=False, server_default=text('False'))  # 医保查询状态False为未完成，True为完成
    p_medical_update = db.Column(db.String(255), nullable=True)  # 是否添加补贴月份
    p_person_result = db.Column(db.Boolean, nullable=True)  # 人工审核结果(False为不通过，True为通过)
    p_date = db.Column(db.DateTime, nullable=True, server_default=func.now())  # 审核时间
    p_identify_person = db.Column(db.String(255), nullable=True)  # 审核人
    p_identify_comment = db.Column(db.Text, nullable=True)  # 审核说明

    p_social_company_identical = db.Column(db.Boolean, nullable=True)  # 入职前参保单位一致
    p_file_path = db.Column(db.String(255), nullable=True)  # 附件列表字符串
    p_social_state = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 人员社保信息获取状态(默认为False)
    p_detail_info = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 人员详情信息状态(默认为False)
    p_hasFile = db.Column(db.Boolean, server_default=text("False"))  # 人员是否有附件

    p_insured_identity = db.Column(db.String(255), nullable=True)  # 人员参保身份：主要针对50-55周岁女性
    p_final_list = db.Column(db.Integer, nullable=False,
                             server_default=text('0'))  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)
    # 街道审核
    p_street_author = db.Column(db.String(255), nullable=True)  # 街道审核人
    p_street_result = db.Column(db.Boolean, nullable=True)  # 街道审核结果
    p_street_comment = db.Column(db.String(255), nullable=True)  # 街道审核结果

    # 其他信息
    p_other_allowance = db.Column(db.String(1000),nullable=True)  # 人员享受其他补贴信息
    # 时间
    p_create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    p_update_time = db.Column(TIMESTAMP, nullable=False)


class XwCompanyInfo(db.Model):
    """
    小微企业信息
    """
    __tablename__ = "xwCompany_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    main_num = db.Column(db.String(255), nullable=False)  # 主体身份代码
    social_num = db.Column(db.String(255), nullable=False)  # 社会信用代码
    register_num = db.Column(db.String(255), nullable=False)  # 注册号
    company_name = db.Column(db.String(255), nullable=False)  # 企业名称
    main_type = db.Column(db.String(255), nullable=False)  # 市场主体类型
    setup_date = db.Column(db.String(255), nullable=False)  # 成立时间
    register_fund = db.Column(db.String(255), nullable=False)  # 注册资本
    register_location_num = db.Column(db.String(255), nullable=False)  # 登记机关
    register_location = db.Column(db.String(255), nullable=False)  # 登记机关（中文名称）
    belong_type = db.Column(db.String(255), nullable=False)  # 所属门类
    work_num = db.Column(db.String(255), nullable=False)  # 行业代码
    work_name = db.Column(db.String(255), nullable=False)  # 行业代码(中文名称)
    xw_type = db.Column(db.String(255), nullable=False)  # 小微企业分类
    xw_type_name = db.Column(db.String(255), nullable=False)  # 小微企业分类（中文名称）
    join_datetime = db.Column(db.String(255), nullable=False)  # 加入时间
    exit_datetime = db.Column(db.String(255), nullable=False)  # 退出时间
    exit_reason = db.Column(db.String(255), nullable=False)  # 退出原因
    exit_reasons = db.Column(db.String(255), nullable=False)  # 退出原因（中文名称）
    xw_state = db.Column(db.String(255), nullable=False)  # 小微企业状态
    xw_state_name = db.Column(db.String(255), nullable=False)  # 小微企业状态（中文名称）
    total_unit = db.Column(db.String(255), nullable=False)  # 数据汇总单位
    total_unit_date = db.Column(db.String(255), nullable=False)  # 数据汇总单位时间

    def to_dict(self):
        dic = {
            "main_num": self.main_num,
            "social_num": self.social_num,
            "register_num": self.register_num,
            "company_name": self.company_name,
            "main_type": self.main_type,
            "setup_date": self.setup_date,
            "register_fund": self.register_fund,
            "register_location_num": self.register_location_num,
            "register_location": self.register_location,
            "belong_type": self.belong_type,
            "work_num": self.work_num,
            "work_name": self.work_name,
            "xw_type": self.xw_type,
            "xw_type_name": self.xw_type_name,
            "join_datetime": self.join_datetime,
            "exit_datetime": self.exit_datetime,
            "exit_reason": self.exit_reason,
            "exit_reasons": self.exit_reasons,
            "xw_state": self.xw_state,
            "xw_state_name": self.xw_state_name,
            "total_unit": self.total_unit,
            "total_unit_date": self.total_unit_date,
        }
        return dic


class DetailPayInfo(db.Model):
    """
    具体月份补贴金额信息
    """
    __tablename__ = 'detail_pay_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    d_apply_num = db.Column(db.String(255), nullable=False)
    d_ID = db.Column(db.String(255), nullable=False)  # 证件号码(关联人员列表的证件号码
    d_pay_month = db.Column(db.String(255), nullable=True)  # 投保日期
    d_old_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 养老保险
    d_injury_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 工伤保险
    d_unemploy_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 失业保险
    d_birth_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 生育保险
    d_medical_insur = db.Column(db.DECIMAL(10, 2), nullable=True)  # 医疗保险
    d_normal_fund = db.Column(db.DECIMAL(10, 2), nullable=True)  # 一般性岗位补贴
    is_checked = db.Column(db.Boolean, nullable=False, server_default=text('True'))  # 是否选中


class DegreeInfo(db.Model):
    """学历信息"""
    __tablename__ = "degreeInfo"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    card_ID = db.Column(db.String(255), nullable=True)  # 证件号码
    name = db.Column(db.String(255), nullable=True)  # 姓名
    identifyCode = db.Column(db.String(255), nullable=True)  # 请求标识码
    graduate_school = db.Column(db.String(255), nullable=True)  # 毕业学校名称
    graduate_subject = db.Column(db.String(255), nullable=True)  # 专业名称
    graduation = db.Column(db.String(255), nullable=True)  # 层次
    admission_date = db.Column(db.String(255), nullable=True)  # 入学时间
    graduate_date = db.Column(db.String(255), nullable=True)  # 毕业时间
    study_type = db.Column(db.String(255), nullable=True)  # 学习形式
    graduate_num = db.Column(db.String(255), nullable=True)  # 学历证书编号

    def to_dict(self):
        dic = {
            "card_ID": self.card_ID,
            "name": self.name,
            "identifyCode": self.identifyCode,
            "graduate_school": self.graduate_school,
            "graduate_subject": self.graduate_subject,
            "graduation": self.graduation,
            "admission_date": self.admission_date,
            "graduate_date": self.graduate_date,
            "study_type": self.study_type,
            "graduate_num": self.graduate_num,
        }
        return dic


class UnemployInfo(db.Model):
    """
    失业登记信息
    """
    __tablename__ = 'unemploy_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    e_serial_num = db.Column(db.String(255), nullable=True)  # 失业记录流水号
    e_employ_num = db.Column(db.String(255), nullable=True)  # 就业创业证号码
    e_ID = db.Column(db.String(255), nullable=True)  # 公民身份证号码关联人员信息的证件号码
    e_name = db.Column(db.String(255), nullable=True)  # 姓名
    e_population = db.Column(db.String(255), nullable=True)  # 户口性质
    e_register_num = db.Column(db.String(255), nullable=True)  # 失业登记号

    e_register_type = db.Column(db.String(255), nullable=True)  # 登记类别
    e_start_date = db.Column(db.String(255), nullable=True)  # 失业有效始期
    e_end_date = db.Column(db.String(255), nullable=True)  # 失业有效终期
    e_register_date = db.Column(db.String(255), nullable=True)  # 登记日期
    e_exist_forward = db.Column(db.String(255), nullable=True)  # 注销去向


class HardIdentifyInfo(db.Model):
    """
    困难认定信息
    """
    __tablename__ = 'hard_identify_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    h_name = db.Column(db.String(255), nullable=True)  # 姓名
    h_ID = db.Column(db.String(255), nullable=True)  # 公民身份证号码关联人员信息的证件号码
    h_employ_type = db.Column(db.String(255), nullable=True)  # 就业困难人员类型
    h_apply_date = db.Column(db.String(255), nullable=True)  # 认定申请日期
    h_identify_date = db.Column(db.String(255), nullable=True)  # 审核认定日期
    h_exit_date = db.Column(db.String(255), nullable=True)  # 退出认定日期
    h_state = db.Column(db.String(255), nullable=True)  # 审核状态
    h_ID_state = db.Column(db.String(255), nullable=True)  # 身份认定状态
    h_identify_way = db.Column(db.String(255), nullable=True)  # 认定申请途径
    h_apply_location = db.Column(db.String(255), nullable=True)  # 认定申请行政区划


class RecordInfo(db.Model):
    """
    就业登记信息
    """
    __tablename__ = 'record_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    r_accept_batch = db.Column(db.String(255), nullable=True)  # 受理批次
    r_company_name = db.Column(db.String(255), nullable=True)  # 单位名称
    r_ID = db.Column(db.String(255), nullable=True)  # 公民身份证号码关联人员信息的证件号码
    r_name = db.Column(db.String(255), nullable=True)  # 姓名
    r_sex = db.Column(db.String(255), nullable=True)  # 性别
    r_birth = db.Column(db.String(255), nullable=True)  # 出生日期
    r_degree = db.Column(db.String(255), nullable=True)  # 文化程度
    r_population = db.Column(db.String(255), nullable=True)  # 户口性质
    r_location = db.Column(db.String(255), nullable=True)  # 户口所在地
    r_register_type = db.Column(db.String(255), nullable=True)  # 登记类别
    r_contract_start_date = db.Column(db.String(255), nullable=True)  # 合同始期
    r_contract_end_date = db.Column(db.String(255), nullable=True)  # 合同终期
    r_relieve_date = db.Column(db.String(255), nullable=True)  # 解除合同日期
    r_register_date = db.Column(db.String(255), nullable=True)  # 登记日期
    r_isapply = db.Column(db.String(255), nullable=True)  # 是否已申领就业创业证
    r_date_source = db.Column(db.String(255), nullable=True, server_default='-')  # 数据来源


class SocialPayInfo(db.Model):
    """
    社保缴纳信息
    """
    __tablename__ = 'social_pay_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    s_ID = db.Column(db.String(255), nullable=True)  # 公民身份证号码 关联人员信息的证件号码
    s_pay_date = db.Column(db.String(255), nullable=True)  # 投保日期
    s_old_base = db.Column(db.String(255), nullable=True)  # 养老缴费基数
    s_medical_base = db.Column(db.String(255), nullable=True)  # 医疗缴费基数
    s_old_insur = db.Column(db.String(255), nullable=True)  # 个人养老保险
    s_unemploy_insur = db.Column(db.String(255), nullable=True)  # 个人失业保险
    s_injury_insur = db.Column(db.String(255), nullable=True)  # 个人工伤保险
    s_medical_insur = db.Column(db.String(255), nullable=True)  # 个人医疗保险
    s_c_old_insur = db.Column(db.String(255), nullable=True)  # 单位养老保险
    s_c_unemploy_insur = db.Column(db.String(255), nullable=True)  # 单位失业保险
    s_c_injury_insur = db.Column(db.String(255), nullable=True)  # 单位工伤保险
    s_c_medical_insur = db.Column(db.String(255), nullable=True)  # 单位医疗保险
    s_c_disease_insur = db.Column(db.String(255), nullable=True)  # 单位重大疾病保险
    s_c_birth_insur = db.Column(db.String(255), nullable=True)  # 单位生育保险
    s_social_num = db.Column(db.String(255), nullable=True)  # 个人社保号(社保)
    s_social_c_num = db.Column(db.String(255), nullable=True)  # 单位社保号（社保)
    s_social_c_name = db.Column(db.String(255), nullable=True)  # 单位名称(社保)
    s_social_credit_num = db.Column(db.String(255), nullable=True)  # 社会统一信用代码(社保)
    s_medical_num = db.Column(db.String(255), nullable=True)  # 个人社保号医保)
    s_medical_c_num = db.Column(db.String(255), nullable=True)  # 单位社保号医保)
    s_medical_c_name = db.Column(db.String(255), nullable=True)  # 单位名称(医保)
    s_medical_credit_num = db.Column(db.String(255), nullable=True)  # 社会统一信用代码(医保)


class BusinessInfo(db.Model):
    """
    商事记录信息
    """
    __tablename__ = 'business_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    b_register_num = db.Column(db.String(255), nullable=True)  # 商事注册号
    b_credit_num = db.Column(db.String(255), nullable=True)  # 统一社会信用代码
    b_company = db.Column(db.String(255), nullable=True)  # 单位名称
    b_charge_name = db.Column(db.String(255), nullable=True)  # 法定代表人
    b_ID = db.Column(db.String(255), nullable=True)  # 法人证件号码  关联人员信息的证件号码
    b_main_type = db.Column(db.String(255), nullable=True)  # 商事主体类型
    b_pro_type = db.Column(db.String(255), nullable=True)  # 主营项目类别
    b_date = db.Column(db.String(255), nullable=True)  # 成立时间
    b_state = db.Column(db.String(255), nullable=True)  # 状态
    b_relieve_date = db.Column(db.String(255), nullable=True, server_default='-')  # 状态


class AllowanceInfo(db.Model):
    """个人补贴享受情况查询"""
    __tablename__ = "allowance_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    z_reason = db.Column(db.String(255), nullable=True)
    z_name = db.Column(db.String(255), nullable=True)
    z_sex = db.Column(db.String(255), nullable=True)
    z_age = db.Column(db.String(255), nullable=True)
    z_ID = db.Column(db.String(255), nullable=True)
    z_login_num = db.Column(db.String(255), nullable=True)
    z_free_num = db.Column(db.String(255), nullable=True)
    z_person_type = db.Column(db.String(255), nullable=True)
    z_hard_type = db.Column(db.String(255), nullable=True)
    z_contract_date = db.Column(db.String(255), nullable=True)
    z_authority_count = db.Column(db.String(255), nullable=True)
    z_old_insur = db.Column(db.String(255), nullable=True)
    z_unemploy_insur = db.Column(db.String(255), nullable=True)
    z_injury_insur = db.Column(db.String(255), nullable=True)
    z_birth_insur = db.Column(db.String(255), nullable=True)
    z_medical_insur = db.Column(db.String(255), nullable=True)
    z_social_insur = db.Column(db.String(255), nullable=True)
    z_postion_insur = db.Column(db.String(255), nullable=True)
    z_allow_count = db.Column(db.String(255), nullable=True)
    z_help_type = db.Column(db.String(255), nullable=True)
    z_state = db.Column(db.String(255), nullable=True)
    z_author = db.Column(db.String(255), nullable=True)
    z_isRegister = db.Column(db.String(255), nullable=True)
    z_company_name = db.Column(db.String(255), nullable=True)
    z_social_fund_type = db.Column(db.String(255), nullable=True)
    z_position_fund_type = db.Column(db.String(255), nullable=True)
    z_refund_mark = db.Column(db.String(255), nullable=True)
    z_approved_date = db.Column(db.String(255), nullable=True)
    z_total = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        dic = {
            'id': self.id,
            'z_reason': self.z_reason,
            'z_name': self.z_name,
            'z_sex': self.z_sex,
            'z_age': self.z_age,
            'z_ID': self.z_ID,
            'z_login_num': self.z_login_num,
            'z_free_num': self.z_free_num,
            'z_person_type': self.z_person_type,
            'z_hard_type': self.z_hard_type,
            'z_contract_date': self.z_contract_date,
            'z_authority_count': self.z_authority_count,
            'z_old_insur': self.z_old_insur,
            'z_unemploy_insur': self.z_unemploy_insur,
            'z_injury_insur': self.z_injury_insur,
            'z_birth_insur': self.z_birth_insur,
            'z_medical_insur': self.z_medical_insur,
            'z_social_insur': self.z_social_insur,
            'z_postion_insur': self.z_postion_insur,
            'z_allow_count': self.z_allow_count,
            'z_help_type': self.z_help_type,
            'z_state': self.z_state,
            'z_author': self.z_author,
            'z_isRegister': self.z_isRegister,
            'z_company_name': self.z_company_name,
            'z_social_fund_type': self.z_social_fund_type,
            'z_position_fund_type': self.z_position_fund_type,
            'z_refund_mark': self.z_refund_mark,
            'z_approved_date': self.z_approved_date,
            'z_total': self.z_total,
        }
        return dic


class UpdateRecordInfo(db.Model):
    """
    审核记录记录信息
    """
    __tablename__ = 'update_record_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    u_ID = db.Column(db.String(255), nullable=False)  # 人员证件号码  关联人员信息的证件号码
    u_result = db.Column(db.Boolean, nullable=True)  # 审核结果
    u_new_comment = db.Column(db.Text, nullable=True)  # 审核说明
    u_name = db.Column(db.String(255), nullable=True)  # 审核人名称
    u_update_date = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间


class CheckInfo(db.Model):
    """
    核验数据抓取进度表
    """
    __tablename__ = 'check_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    check_type = db.Column(db.String(255), nullable=True)  # 校验项目类型
    state = db.Column(db.String(255), nullable=True)  # 抓取状态/进度
    remark = db.Column(db.String(10000), nullable=True)  # 未抓取完数据备注
    update_time = db.Column(db.TIMESTAMP, nullable=False)  # 更新时间


class Back_record_info(db.Model):
    """回填回退记录信息"""
    __tablename__ = "back_record_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    br_apply_season = db.Column(db.String(255), nullable=False)  # 申报年季
    br_apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    br_company = db.Column(db.String(255), nullable=False)  # 企业名称
    br_person_ID = db.Column(db.String(255), nullable=False, default="", server_default='')  # 人员证件号码
    br_person_name = db.Column(db.String(255), nullable=False, default="", server_default='')  # 人员名字
    br_fill_back = db.Column(db.Integer, nullable=False, server_default=text('0'))  # 操作名称
    br_detail = db.Column(db.String(255), nullable=False, default="", server_default='无')  # 操作详情
    br_state = db.Column(db.String(255), nullable=False)  # 操作状态
    br_identify_person = db.Column(db.String(255), nullable=True)  # 审核人名字
    br_cid = db.Column(db.Integer, nullable=True)  # 关联id 用于定位个人

    # 审核等级
    br_type = db.Column(db.Integer, nullable=True)  # 0是街道审核 1是区审核
    # 时间
    br_create_date = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    br_update_date = db.Column(TIMESTAMP, nullable=False)  # 更新时间


class Controller_info(db.Model):
    """所有项目监控表"""
    __tablename__ = "controller_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_ID = db.Column(db.String(255), nullable=False)  # 项目编号
    project_name = db.Column(db.String(255), nullable=False)  # 项目名称
    apply_season = db.Column(db.String(255), nullable=False)  # 申报年季
    detail = db.Column(db.JSON, nullable=True)  # 详情信息


class FieldMapping(db.Model):
    """
    字段映射
    """
    __tablename__ = 'field_mapping'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sql_table = db.Column(db.String(255))  # 表名
    sql_key = db.Column(db.String(255))  # 英文名
    sql_zh = db.Column(db.String(255))  # 中文解释


class RecatchDataInfo(db.Model):
    """
    重新抓取回退到待报批企业
    """
    __tablename__ = "recatchData_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    apply_num = db.Column(db.String(255), nullable=True)  # 申领编号
    company_name = db.Column(db.String(255), nullable=True)  # 企业名称
    register_num = db.Column(db.String(255), nullable=True)  # 企业统一行用代码
    remark = db.Column(db.String(255), nullable=True)  # 备注
    state = db.Column(db.Boolean, default=False, server_default=text('False'))  # 重新抓取状态
    identify_person = db.Column(db.String(255))  # 审核人

    def to_dict(self):
        dic = {
            "id": self.id,
            "apply_num": self.apply_num,
            "company_name": self.company_name,
            "remark": self.remark,
            "state": "成功" if self.state else "未完成",
            "identify_person": self.identify_person
        }
        return dic


class RecatchPersonDataInfo(db.Model):
    """
    重新抓取人员详情信息
    """
    __tablename__ = "recatchPersonData_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_ID = db.Column(db.String(255), nullable=True)  # 人员证件号码
    info_ID = db.Column(db.String(255), nullable=True)  # 重抓个人详情信息编号
    state = db.Column(db.Integer, default=0, server_default=text('0'))  # 重新抓取状态
    identify_person = db.Column(db.String(255))  # 审核人
    create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    update_time = db.Column(TIMESTAMP, nullable=False)

    def to_dict(self):
        dic = {
            "id": self.id,
            "card_ID": self.card_ID,
            "info_ID": self.info_ID,
            "state": self.state,
            "identify_person": self.identify_person,
            "create_time": self.create_time,
            "update_time": self.update_time
        }
        return dic


class AccountInfo(db.Model):
    """
    匹配审核人员账号与序号

    """
    __tablename__ = "account_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_num = db.Column(db.Integer, nullable=True)
    p_identify_person = db.Column(db.String(255), nullable=True)


class DoubtCompany_Info(db.Model):
    """
    存疑企业名单
    """
    __tablename__ = "doubt_company_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dtype = db.Column(db.Integer, nullable=True)  # 存疑类型，0为黑名单，1为可疑企业名单
    company_name = db.Column(db.String(255), nullable=True)  # 企业名称
    social_num = db.Column(db.String(255), nullable=True)  # 统一信用代码
    season = db.Column(db.String(1000), nullable=True)  # 录入原因
    isOutRegister = db.Column(db.Boolean, default=False, server_default=text("False"))  # 是否退出登记
    outRegisterDate = db.Column(db.String(255), nullable=True)  # 退出登记时间
    remark = db.Column(db.JSON, nullable=True)  # 备注
    # 时间
    create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    update_time = db.Column(TIMESTAMP, nullable=False)


class DoubtPerson_Info(db.Model):
    """
    存疑人员名单
    """
    __tablename__ = "doubt_person_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dtype = db.Column(db.Integer, nullable=True)  # 存疑类型，0为黑名单，1为可疑人员名单
    card_num = db.Column(db.String(255), nullable=True)  # 证件号码
    name = db.Column(db.String(255), nullable=True)  # 姓名
    company = db.Column(db.String(255), nullable=True)  # 用人单位
    season = db.Column(db.String(1000), nullable=True)  # 录入原因
    isOutRegister = db.Column(db.Boolean, default=False, server_default=text("False"))  # 是否退出登记
    outRegisterDate = db.Column(db.String(255), nullable=True)  # 退出登记时间
    remark = db.Column(db.JSON, nullable=True)  # 备注
    # 时间
    create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    update_time = db.Column(TIMESTAMP, nullable=False)


"""毕业生就业补贴数据库表"""


# todo:====================================高校毕业生补贴=====================================
# todo:======================================================================================
class StudentInfo(db.Model):
    """
    毕业生信息
    """
    __tablename__ = 'student_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    # todo:新增字段
    apply_num = db.Column(db.String(255), nullable=True)  # 申领编号
    apply_season = db.Column(db.String(255), nullable=True)  # 申办年季
    isnet = db.Column(db.Boolean, nullable=True)  # 是否网办
    name = db.Column(db.String(255), nullable=True)  # 姓名
    card_ID = db.Column(db.String(255), nullable=True)  # 证件号码
    sex = db.Column(db.String(255), nullable=True)  # 性别
    age = db.Column(db.String(255), nullable=True)  # 年龄
    student_type = db.Column(db.String(255), nullable=True)  # 毕业生类别
    company_name = db.Column(db.String(255), nullable=True)  # 单位名称
    credit_num = db.Column(db.String(255), nullable=True)  # 统一社会信用代码
    employment_type = db.Column(db.String(255), nullable=True)  # 就业类型
    contract_time = db.Column(db.String(255), nullable=True)  # 合同起止日期
    subsidies = db.Column(db.String(255), nullable=True)  # 补贴金额
    audit_status = db.Column(db.String(255), nullable=True)  # 审核状态
    audit_instructions = db.Column(db.String(200), nullable=True)  # 审核说明
    company_contact = db.Column(db.String(255), nullable=True)  # 单位里联系人
    company_phone = db.Column(db.String(255), nullable=True)  # 单位联系电话
    claimant_phone = db.Column(db.String(255), nullable=True)  # 申领人联系电话
    company_address = db.Column(db.String(255), nullable=True)  # 单位所属地
    document_type = db.Column(db.String(255), nullable=True)  # 证件类型
    contract_start = db.Column(db.String(255), nullable=True)  # 合同开始日期
    contract_end = db.Column(db.String(255), nullable=True)  # 合同结束日期
    social_security_ID = db.Column(db.String(255), nullable=True)  # 个人社保号
    graduation_time = db.Column(db.String(255), nullable=True)  # 毕业时间
    registration_time = db.Column(db.String(255), nullable=True)  # 报到时间
    is_social_card = db.Column(db.Boolean)  # 是否发放到社保卡
    social_cardID = db.Column(db.String(255), nullable=True, server_default="")  # 社保卡号
    bank = db.Column(db.String(255), nullable=True)  # 开户银行
    account_name = db.Column(db.String(255), nullable=True)  # 开户名称
    passID = db.Column(db.String(255), nullable=True)  # 通行证号码
    graduate_school = db.Column(db.String(255), nullable=True)  # 毕业院校
    qualified_time = db.Column(db.String(255), nullable=True)  # 考核合格时间
    bank_account = db.Column(db.String(255), nullable=True)  # 银行账号
    remark = db.Column(db.String(255), nullable=True)  # 备注
    diploma_path = db.Column(db.String(200), nullable=True)  # 毕业证附件路径
    agent = db.Column(db.String(255), nullable=True)  # 经办人
    agent_date = db.Column(db.String(255), nullable=True)  # 经办时间
    agent_institution = db.Column(db.String(255), nullable=True)  # 经办机构
    get_data_state = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 数据抓取状态
    robot_result = db.Column(db.Boolean, nullable=True)  # 机器人预审结果
    explain = db.Column(db.String(200), nullable=True)  # 预审说明
    isaudit = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 是否审核完成

    audit_date = db.Column(db.String(255), nullable=True)  # 审核时间
    is_ent = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 是否创业或高管
    is_summary = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 是否区汇总
    company_type = db.Column(db.String(255), nullable=True)  # 企业类型
    extra_social_count = db.Column(db.Integer, nullable=True)  # 企业参保人数

    # 额外状态位
    social_security_state = db.Column(db.Integer, nullable=True, server_default=text('0'))  # 社保抓取状态
    employment_state = db.Column(db.Integer, nullable=True, server_default=text('0'))  # 就业登记抓取状态
    ent_state = db.Column(db.Integer, nullable=True, server_default=text('0'))  # 商事登记信息抓取状态
    graduate_state = db.Column(db.Integer, nullable=True, server_default=text('0'))  # 毕业生信息抓取状态
    xwCompany_state = db.Column(db.Integer, nullable=True, server_default=text('0'))  # 小微企业信息抓取状态
    is_sendEmail = db.Column(db.Boolean, server_default=text("False"))  # 是否发送短信
    outputFile = db.Column(db.Boolean, server_default=text("False"))  # 是否导出过表格

    # 时间
    create_datetime = db.Column(db.DateTime, nullable=True, server_default=func.now())  # 创建时间
    update_datetime = db.Column(TIMESTAMP, nullable=False)  # 更新时间

    screen_path = db.Column(db.String(200), nullable=True)  # 截屏路径
    company_addr = db.Column(db.String(500), nullable=True)  # 企业地址等信息

    final_list = db.Column(db.Integer, nullable=False, server_default=text('0'))  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)

    # todo:区级审核
    artificial_audit = db.Column(db.Integer, nullable=True)  # 区审核结果 0失败 1成功
    auditor = db.Column(db.String(255), nullable=True)  # 区审核人
    region_remark = db.Column(db.String(255), nullable=False, server_default="")  # 区级审核说明
    # todo:街道审核
    street_result = db.Column(db.Boolean, nullable=True)  # 街道人员审核结果
    street_person = db.Column(db.String(255), nullable=True)  # 街道审核人
    street_remark = db.Column(db.String(255), nullable=False, server_default="")  # 街道审核说明

    def to_dict(self):
        """转成字典"""
        dic = {
            'id': self.id,
            'apply_num': self.apply_num,
            'apply_season': self.apply_season,
            'isnet': self.isnet,
            'name': self.name,
            'card_ID': self.card_ID,
            'sex': self.sex,
            'age': self.age,
            'student_type': self.student_type,
            'company_name': self.company_name,
            'credit_num': self.credit_num,
            'employment_type': self.employment_type,
            'contract_time': self.contract_time,
            'subsidies': self.subsidies,
            'audit_status': self.audit_status,
            'audit_instructions': self.audit_instructions,
            'company_contact': self.company_contact,
            'company_phone': self.company_phone,
            'claimant_phone': self.claimant_phone,
            'company_address': self.company_address,
            'document_type': self.document_type,
            'contract_start': self.contract_start,
            'contract_end': self.contract_end,
            'social_security_ID': self.social_security_ID,
            'graduation_time': self.graduation_time,
            'registration_time': self.registration_time,
            'is_social_card': self.is_social_card,
            'social_cardID': self.social_cardID,
            'bank': self.bank,
            'account_name': self.account_name,
            'passID': self.passID,
            'graduate_school': self.graduate_school,
            'qualified_time': self.qualified_time,
            'bank_account': self.bank_account,
            'remark': self.remark,
            'diploma_path': self.diploma_path,
            'agent': self.agent,
            'agent_date': self.agent_date,
            'agent_institution': self.agent_institution,
            'get_data_state': self.get_data_state,
            'robot_result': self.robot_result,
            'explain': self.explain,
            'artificial_audit': self.artificial_audit,
            'isaudit': self.isaudit,
            'auditor': self.auditor,
            'audit_date': self.audit_date,
            'social_security_state': self.social_security_state,
            'employment_state': self.employment_state,
            'ent_state': self.ent_state,
            'is_ent': self.is_ent,
            'is_summary': self.is_summary,
            'company_type': self.company_type,
        }
        return dic


class DegreeInfo(db.Model):
    """学历信息"""
    __tablename__ = "degree_info"
    __bind_key__ = "bysjybt"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    name = db.Column(db.String(255), nullable=False)  # 姓名
    identifyCode = db.Column(db.String(255), nullable=False)  # 请求标识码
    graduate_school = db.Column(db.String(255), nullable=False)  # 毕业学校名称
    graduate_subject = db.Column(db.String(255), nullable=False)  # 专业名称
    graduation = db.Column(db.String(255), nullable=False)  # 层次
    admission_date = db.Column(db.String(255), nullable=False)  # 入学时间
    graduate_date = db.Column(db.String(255), nullable=False)  # 毕业时间
    study_type = db.Column(db.String(255), nullable=False)  # 学习形式
    graduate_num = db.Column(db.String(255), nullable=False)  # 学历证书编号

    def to_dict(self):
        dic = {
            "id": self.id,
            "card_ID": self.card_ID,
            "name": self.name,
            "identifyCode": self.identifyCode,
            "graduate_school": self.graduate_school,
            "graduate_subject": self.graduate_subject,
            "graduation": self.graduation,
            "admission_date": self.admission_date,
            "graduate_date": self.graduate_date,
            "study_type": self.study_type,
            "graduate_num": self.graduate_num,
        }

        return dic


class SocialSecurity(db.Model):
    """
    社保信息
    """
    __tablename__ = 'social_security'
    __bind_key__ = 'bysjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    insured_date = db.Column(db.String(255), nullable=False)  # 投保日期
    old_base = db.Column(db.String(255), nullable=False)  # 养老缴费基数
    medical_base = db.Column(db.String(255), nullable=False)  # 医疗缴费基数
    old_insur = db.Column(db.String(255), nullable=False)  # 个人养老保险
    unemploy_insur = db.Column(db.String(255), nullable=False)  # 个人失业保险
    injury_insur = db.Column(db.String(255), nullable=False)  # 个人工伤保险
    medical_insur = db.Column(db.String(255), nullable=False)  # 个人医疗保险
    c_old_insur = db.Column(db.String(255), nullable=False)  # 单位养老保险
    c_unemploy_insur = db.Column(db.String(255), nullable=False)  # 单位失业保险
    c_injury_insur = db.Column(db.String(255), nullable=False)  # 单位工伤保险
    c_medical_insur = db.Column(db.String(255), nullable=False)  # 单位医疗保险
    c_disease_insur = db.Column(db.String(255), nullable=False)  # 单位重大疾病
    c_birth_insur = db.Column(db.String(255), nullable=False)  # 单位生育保险
    social_num = db.Column(db.String(255), nullable=False)  # 社保个人社保号
    social_c_num = db.Column(db.String(255), nullable=False)  # 社保单位社保号
    social_c_name = db.Column(db.String(255), nullable=False)  # 社保单位名称
    social_credit_num = db.Column(db.String(255), nullable=False)  # 社保统一信用代码
    medical_num = db.Column(db.String(255), nullable=False)  # 医保个人社保号
    medical_c_num = db.Column(db.String(255), nullable=False)  # 医保单位社保号
    medical_c_name = db.Column(db.String(255), nullable=False)  # 医保单位名称
    medical_credit_num = db.Column(db.String(255), nullable=False)  # 医保统一信用代码

    def to_dict(self):
        dic = {
            'id': self.id,
            'card_ID': self.card_ID,
            'insured_date': self.insured_date,
            'old_base': self.old_base,
            'medical_base': self.medical_base,
            'old_insur': self.old_insur,
            'unemploy_insur': self.unemploy_insur,
            'injury_insur': self.injury_insur,
            'medical_insur': self.medical_insur,
            'c_old_insur': self.c_old_insur,
            'c_unemploy_insur': self.c_unemploy_insur,
            'c_injury_insur': self.c_injury_insur,
            'c_medical_insur': self.c_medical_insur,
            'c_disease_insur': self.c_disease_insur,
            'c_birth_insur': self.c_birth_insur,
            'social_num': self.social_num,
            'social_c_num': self.social_c_num,
            'social_c_name': self.social_c_name,
            'social_credit_num': self.social_credit_num,
            'medical_num': self.medical_num,
            'medical_c_num': self.medical_c_num,
            'medical_c_name': self.medical_c_name,
            'medical_credit_num': self.medical_credit_num,
        }
        return dic


class EmploymentRegistration(db.Model):
    """
    就业登记信息
    """
    __tablename__ = 'employment_registration'
    __bind_key__ = 'bysjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    accept_batch = db.Column(db.String(255), nullable=False)  # 受理批次
    company_name = db.Column(db.String(255), nullable=False)  # 单位名称
    name = db.Column(db.String(255), nullable=False)  # 姓名
    sex = db.Column(db.String(255), nullable=False)  # 性别
    birth = db.Column(db.String(255), nullable=False)  # 出生日期
    degree = db.Column(db.String(255), nullable=False)  # 文化程度
    population = db.Column(db.String(255), nullable=False)  # 户口性质
    location = db.Column(db.String(255), nullable=False)  # 户口所在地
    register_type = db.Column(db.String(255), nullable=False)  # 登记类别
    contract_end_date = db.Column(db.String(255), nullable=False)  # 合同终期
    contract_start_date = db.Column(db.String(255), nullable=True)  # 合同始期
    relieve_date = db.Column(db.String(255), nullable=True)  # 解除合同日期
    register_date = db.Column(db.String(255), nullable=False)  # 登记日期
    isapply = db.Column(db.String(255), nullable=False)  # 是否以申领就业创业证
    date_source = db.Column(db.String(255), nullable=False)  # 数据来源

    def to_dict(self):
        dic = {
            'id': self.id,
            'card_ID': self.card_ID,
            'accept_batch': self.accept_batch,
            'company_name': self.company_name,
            'name': self.name,
            'sex': self.sex,
            'birth': self.birth,
            'degree': self.degree,
            'population': self.population,
            'location': self.location,
            'register_type': self.register_type,
            'contract_start_date': self.contract_start_date,
            'contract_end_date': self.contract_end_date,
            'relieve_date': self.relieve_date,
            'register_date': self.register_date,
            'isapply': self.isapply,
            'date_source': self.date_source,
        }
        return dic


class DataPageInfo(db.Model):
    """
    爬取页面记录
    """
    __tablename__ = 'data_page_info'
    __bind_key__ = 'bysjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    page = db.Column(db.Integer, nullable=True)  # 爬取的页数


class BysBackInfo(db.Model):
    """
    回填、回退表
    """
    __tablename__ = 'bys_back_info'
    __bind_key__ = 'bysjybt'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    fill_back = db.Column(db.Integer, nullable=False)  # 回填还是回退# 操作名称0：无操作，1：回填，2：回退
    fill_back_link = db.Column(db.Integer, nullable=False, server_default=text('0'))  # 回退环节
    state = db.Column(db.String(255), nullable=False)  # 回填回退状态
    detail = db.Column(db.String(255), nullable=True)  # 详情，操作失败原因
    identify_person = db.Column(db.String(255), nullable=True)  # 办理人
    create_date = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    update_date = db.Column(TIMESTAMP, nullable=False)  # 更新时间

    # 审核级别
    br_type = db.Column(db.Integer, nullable=True)  # 审核权限类型，（0：街道，1：区级）
    br_street_name = db.Column(db.String(255), nullable=True)  # 所属街道
    name = db.Column(db.String(255), nullable=True)  # 人名
    company_name = db.Column(db.String(255), nullable=True)  # 企业名
    result = db.Column(db.Integer, nullable=True)  # 审核结果

    def to_dict(self):
        dic = {
            'id': self.id,
            'apply_num': self.apply_num,
            'card_ID': self.card_ID,
            'fill_back': self.fill_back,
            'fill_back_link': self.fill_back_link,
            'state': self.state,
            'detail': self.detail,
            'identify_person': self.identify_person,
            'create_date': self.create_date,
            'update_date': self.update_date,
        }
        return dic


class UpdateAuditInfo(db.Model):
    """
    审核记录信息表
    """
    __tablename__ = 'update_audit_info'
    __bind_key__ = 'bysjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    result = db.Column(db.Boolean, nullable=True)  # 人工审核结果
    new_comment = db.Column(db.String(1000), nullable=True)  # 新增审核说明
    name = db.Column(db.String(255), nullable=True)  # 审核人名称
    update_date = db.Column(db.TIMESTAMP, nullable=False)  # 更新时间

    def to_dict(self):
        dic = {
            'id': self.id,
            'apply_num': self.apply_num,
            'card_ID': self.card_ID,
            'result': self.result,
            'new_comment': self.new_comment,
            'name': self.name,
            'update_date': self.update_date,
        }
        return dic


class EntInfo(db.Model):
    """
    商事登记信息表
    """
    __tablename__ = 'ent_info'
    __bind_key__ = 'bysjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    regnum = db.Column(db.String(255), nullable=True)  # 商事注册号
    uniscid = db.Column(db.String(255), nullable=True)  # 统一社会信用代码
    entname = db.Column(db.String(255), nullable=True)  # 单位名称
    name = db.Column(db.String(255), nullable=True)  # 法定代表人
    enttype = db.Column(db.String(255), nullable=True)  # 商事主体类型
    opscotype = db.Column(db.String(255), nullable=True)  # 主营项目类别
    estdate = db.Column(db.String(255), nullable=True)  # 成立时间
    state = db.Column(db.String(255), nullable=True)  # 状态
    relieve_date = db.Column(db.String(255), nullable=True, server_default='-')  # 状态

    def to_dict(self):
        dic = {
            'id': self.id,
            'apply_num': self.apply_num,
            'card_ID': self.card_ID,
            'regnum': self.regnum,
            'uniscid': self.uniscid,
            'entname': self.entname,
            'name': self.name,
            'enttype': self.enttype,
            'opscotype': self.opscotype,
            'estdate': self.estdate,
            'state': self.state,
            "relieve_date": self.relieve_date
        }
        return dic


# todo:=====================================创业带动就业补贴=====================================
# todo:=============================================================================================
class CyCompanyInfo(db.Model):
    __tablename__ = 'cyCompany_info'
    __bind_key__ = 'cyddjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    e_apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    e_declaration_period = db.Column(db.String(255), nullable=False)  # 申报期
    e_declaration_date = db.Column(db.String(255), nullable=False)  # 申报日期
    e_quarter_add = db.Column(db.Boolean, nullable=False)  # 是否本季度新增
    e_socialcredit_code = db.Column(db.String(255), nullable=False)  # 统一信用代码
    e_company_name = db.Column(db.String(255), nullable=False)  # 单位名称
    e_register_location = db.Column(db.String(255), nullable=True)  # 单位注册地
    e_establishment_date = db.Column(db.String(255), nullable=False)  # 创业成立日期
    e_recruits_num = db.Column(db.Integer, nullable=False)  # 本期招用人数
    e_recruits_price = db.Column(db.String(255), nullable=False)  # 本期招用补贴金额
    e_online_processing = db.Column(db.Boolean, nullable=False)  # 是否网办
    e_company_social_security = db.Column(db.String(255), nullable=False)  # 单位社保号
    e_company_type = db.Column(db.String(255), nullable=False)  # 单位类型
    e_legal_person = db.Column(db.String(255), nullable=False)  # 法定代表人
    e_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    e_manager = db.Column(db.String(255), nullable=False)  # 经手人
    e_manager_phone = db.Column(db.String(255), nullable=False)  # 经手人电话
    e_company_worktel = db.Column(db.String(255), nullable=False)  # 单位办公电话
    e_bank = db.Column(db.String(255), nullable=False)  # 开户银行
    e_bank_company = db.Column(db.String(255), nullable=False)  # 开户名称
    e_bank_num = db.Column(db.String(255), nullable=False)  # 银行账号
    e_success_count = db.Column(db.Integer, nullable=False)  # 本期成功人数
    e_success_price = db.Column(db.String(255), nullable=False)  # 本期成功补贴金额
    e_failure_count = db.Column(db.Integer, nullable=False)  # 本期失败人数
    e_cum_count = db.Column(db.Integer, nullable=False)  # 累计招用人数
    e_eco_price_count = db.Column(db.Integer, nullable=False)  # 其中省资金招用人数
    e_cum_price = db.Column(db.String(255), nullable=False)  # 累计招用补贴金额
    e_eco_price = db.Column(db.String(255), nullable=False)  # 其中省资金招用补贴金额
    e_remarks = db.Column(db.String(255), nullable=True)  # 备注
    e_price_type = db.Column(db.String(255), nullable=True)  # 资金类别
    # 额外参数
    e_first_social_count = db.Column(db.Integer, nullable=True)  # 企业第一个月参保人数
    e_second_social_count = db.Column(db.Integer, nullable=True)  # 企业第二个月参保人数
    e_is_xwCompany = db.Column(db.Boolean, nullable=True)  # 是否小微企业
    # e_search_location = db.Column(db.String(255),nullable=True)  # 查询企业地址
    e_robot_result = db.Column(db.Boolean, nullable=True)  # 机器人预审结果

    # todo:区级预审结果
    e_detail = db.Column(db.String(1000), nullable=True)  # 预审详情
    e_person_result = db.Column(db.Boolean, nullable=True)  # 人员审核结果
    e_instructions = db.Column(db.String(1000), nullable=True)  # 审核说明
    e_identify_person = db.Column(db.String(255), nullable=True)  # 审核人

    e_get_person_state = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 抓取单位人员数据状态
    e_isPush = db.Column(db.Boolean, nullable=False, server_default=text('False'))  # 是否推送，根据此字段向明动推送数据
    e_addr = db.Column(db.String(255), nullable=True)  # 企业地址

    # 额外参数（海珠）
    e_street_name = db.Column(db.String(255), nullable=True)  # 所属街道
    e_search_name = db.Column(db.String(255), nullable=True)  # 信用中国查询名称
    e_search_established_time = db.Column(db.String(255), nullable=True)  # 信用中国查询成立时间

    # todo:街道审核
    e_street_result = db.Column(db.Boolean, nullable=True)  # 街道人员审核结果 1通过 0不通过
    e_street_person = db.Column(db.String(255), nullable=True)  # 街道审核人
    e_street_remark = db.Column(db.String(255), nullable=False, server_default="")  # 街道审核说明

    # 时间
    e_create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    e_update_time = db.Column(TIMESTAMP, nullable=False)  # 更新时间

    def to_dict(self):
        dic = {
            "id": self.id,
            "e_robot_result": 1 if self.e_robot_result else 0,
            "e_detail": self.e_detail,
            "e_get_person_state": self.e_get_person_state,
            "e_apply_num": self.e_apply_num,
            "e_declaration_period": self.e_declaration_period,
            "e_declaration_date": self.e_declaration_date,
            "e_quarter_add": self.e_quarter_add,
            "e_socialcredit_code": self.e_socialcredit_code,
            "e_company_name": self.e_company_name,
            "e_establishment_date": self.e_establishment_date,
            "e_recruits_num": self.e_recruits_num,
            "e_recruits_price": self.e_recruits_price,
            "e_online_processing": self.e_online_processing,
            "e_company_social_security": self.e_company_social_security,
            "e_company_type": self.e_company_type,
            "e_legal_person": self.e_legal_person,
            "e_ID": self.e_ID,
            "e_manager": self.e_manager,
            "e_manager_phone": self.e_manager_phone,
            "e_company_worktel": self.e_company_worktel,
            "e_bank": self.e_bank,
            "e_bank_company": self.e_bank_company,
            "e_bank_num": self.e_bank_num,
            "e_success_count": self.e_success_count,
            "e_success_price": self.e_success_price,
            "e_cum_count": self.e_cum_count,
            "e_eco_price_count": self.e_eco_price_count,
            "e_cum_price": self.e_cum_price,
            "e_eco_price": self.e_eco_price,
            "e_remarks": self.e_remarks,
            "e_price_type": self.e_price_type,
            "e_instructions": self.e_instructions,
            "e_first_social_count": self.e_first_social_count,
            "e_second_social_count": self.e_second_social_count
        }
        return dic


class CyPersonInfo(db.Model):
    __tablename__ = 'cyPerson_info'
    __bind_key__ = 'cyddjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    r_apply_num = db.Column(db.String(255), nullable=False)  # 申领编号，关联企业
    r_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    r_name = db.Column(db.String(255), nullable=False)  # 姓名
    r_sex = db.Column(db.String(255), nullable=False)  # 性别
    r_age = db.Column(db.String(255), nullable=False)  # 年龄
    r_provinces = db.Column(db.String(255), nullable=False)  # 是否省市
    r_company_name = db.Column(db.String(255), nullable=False)  # 单位名称
    r_contract_date = db.Column(db.String(255), nullable=False)  # 合同起止日期
    r_local_type = db.Column(db.String(255), nullable=False)  # 人员所在列表
    r_ID_type = db.Column(db.String(255), nullable=False)  # 证件类型
    r_passnum = db.Column(db.String(255), nullable=True)  # 通行证号码
    r_social_num = db.Column(db.String(255), nullable=False)  # 个人社保号
    r_contract_start_date = db.Column(db.String(255), nullable=False)  # 合同开始日期
    r_contract_end_date = db.Column(db.String(255), nullable=False)  # 合同结束日期
    r_instructions = db.Column(db.String(1000), nullable=True)  # 审核说明
    r_remarks = db.Column(db.String(255), nullable=True)  # 备注
    r_agent = db.Column(db.String(255), nullable=True)  # 经办人
    r_handling_date = db.Column(db.String(255), nullable=True)  # 经办日期
    r_handling_location = db.Column(db.String(255), nullable=True)  # 经办机构
    # 额外参数
    r_robot_result = db.Column(db.Boolean, nullable=True)  # 机器人预审结果
    r_detail = db.Column(db.String(1000), nullable=True)  # 预审详情
    # todo：区审核
    r_person_result = db.Column(db.Boolean, nullable=True)  # 区级人员审核结果
    r_person_remark = db.Column(db.String(255), nullable=True, server_default="")  # 区级人员审核说明
    r_identify_person = db.Column(db.String(255), nullable=True)  # 区级审核人
    r_person_detail = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 人员详情信息是否齐全
    # 状态
    r_social_state = db.Column(db.Boolean, nullable=True, server_default=text('False'))  # 人员社保信息获取状态(默认为False)
    r_final_list = db.Column(db.Integer, nullable=False,
                             server_default=text('0'))  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)
    # 街道审核
    r_street_result = db.Column(db.Boolean, nullable=True)  # 街道人员审核结果
    r_street_person = db.Column(db.String(255), nullable=True)  # 街道审核人
    r_street_remark = db.Column(db.String(255), nullable=False, server_default="")  # 街道审核说明

    # 时间
    r_create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    r_update_time = db.Column(TIMESTAMP, nullable=False)  # 更新时间

    def to_dict(self):
        dic = {
            "id": self.id,
            "r_apply_num": self.r_apply_num,
            "r_ID": self.r_ID,
            "r_name": self.r_name,
            "r_sex": self.r_sex,
            "r_age": self.r_age,
            "r_provinces": self.r_provinces,
            "r_company_name": self.r_company_name,
            "r_contract_date": self.r_contract_date,
            "r_instructions": self.r_instructions,
            "r_local_type": self.r_local_type,
            "r_ID_type": self.r_ID_type,
            "r_passnum": self.r_passnum,
            "r_social_num": self.r_social_num,
            "r_contract_start_date": self.r_contract_start_date,
            "r_contract_end_date": self.r_contract_end_date,
            "r_remarks": self.r_remarks,
            "r_agent": self.r_agent,
            "r_handling_date": self.r_handling_date,
            "r_handling_location": self.r_handling_location,
            "r_robot_result": 1 if self.r_robot_result else 0,
            "r_detail": self.r_detail,
            "person_result": 1 if self.r_person_result else 0,
            "person_remark": self.r_person_remark,
            "r_person_detail": self.r_person_detail
        }
        return dic


class CyXwCompanyInfo(db.Model):
    """
    小微企业信息
    """
    __tablename__ = "CyxwCompany_info"
    __bind_key__ = "cyddjybt"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    main_num = db.Column(db.String(255), nullable=False)  # 主体身份代码
    social_num = db.Column(db.String(255), nullable=False)  # 社会信用代码
    register_num = db.Column(db.String(255), nullable=False)  # 注册号
    company_name = db.Column(db.String(255), nullable=False)  # 企业名称
    main_type = db.Column(db.String(255), nullable=False)  # 市场主体类型
    setup_date = db.Column(db.String(255), nullable=False)  # 成立时间
    register_fund = db.Column(db.String(255), nullable=False)  # 注册资本
    register_location_num = db.Column(db.String(255), nullable=False)  # 登记机关
    register_location = db.Column(db.String(255), nullable=False)  # 登记机关（中文名称）
    belong_type = db.Column(db.String(255), nullable=False)  # 所属门类
    work_num = db.Column(db.String(255), nullable=False)  # 行业代码
    work_name = db.Column(db.String(255), nullable=False)  # 行业代码(中文名称)
    xw_type = db.Column(db.String(255), nullable=False)  # 小微企业分类
    xw_type_name = db.Column(db.String(255), nullable=False)  # 小微企业分类（中文名称）
    join_datetime = db.Column(db.String(255), nullable=False)  # 加入时间
    exit_datetime = db.Column(db.String(255), nullable=False)  # 退出时间
    exit_reason = db.Column(db.String(255), nullable=False)  # 退出原因
    exit_reasons = db.Column(db.String(255), nullable=False)  # 退出原因（中文名称）
    xw_state = db.Column(db.String(255), nullable=False)  # 小微企业状态
    xw_state_name = db.Column(db.String(255), nullable=False)  # 小微企业状态（中文名称）
    total_unit = db.Column(db.String(255), nullable=False)  # 数据汇总单位
    total_unit_date = db.Column(db.String(255), nullable=False)  # 数据汇总单位时间

    def to_dict(self):
        dic = {
            "id": self.id,
            "main_num": self.main_num,
            "social_num": self.social_num,
            "register_num": self.register_num,
            "company_name": self.company_name,
            "main_type": self.main_type,
            "setup_date": self.setup_date,
            "register_fund": self.register_fund,
            "register_location_num": self.register_location_num,
            "register_location": self.register_location,
            "belong_type": self.belong_type,
            "work_num": self.work_num,
            "work_name": self.work_name,
            "xw_type": self.xw_type,
            "xw_type_name": self.xw_type_name,
            "join_datetime": self.join_datetime,
            "exit_datetime": self.exit_datetime,
            "exit_reason": self.exit_reason,
            "exit_reasons": self.exit_reasons,
            "xw_state": self.xw_state,
            "xw_state_name": self.xw_state_name,
            "total_unit": self.total_unit,
            "total_unit_date": self.total_unit_date,
        }
        return dic


class CyRecordInfo(db.Model):
    """
    就业登记信息
    """
    __tablename__ = 'cyRecord_info'
    __bind_key__ = 'cyddjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    c_accept_batch = db.Column(db.String(255), nullable=False)  # 受理批次
    c_company_name = db.Column(db.String(255), nullable=False)  # 单位名称
    c_ID = db.Column(db.String(255), nullable=False)  # 公民身份证号码关联人员信息的证件号码
    c_name = db.Column(db.String(255), nullable=False)  # 姓名
    c_sex = db.Column(db.String(255), nullable=False)  # 性别
    c_birth = db.Column(db.String(255), nullable=False)  # 出生日期
    c_degree = db.Column(db.String(255), nullable=False)  # 文化程度
    c_population = db.Column(db.String(255), nullable=False)  # 户口性质
    c_location = db.Column(db.String(255), nullable=False)  # 户口所在地
    c_register_type = db.Column(db.String(255), nullable=False)  # 登记类别
    c_contract_start_date = db.Column(db.String(255), nullable=True)  # 合同始期
    c_contract_end_date = db.Column(db.String(255), nullable=True)  # 合同终期
    c_relieve_date = db.Column(db.String(255), nullable=True)  # 解除合同日期
    c_register_date = db.Column(db.String(255), nullable=False)  # 登记日期
    c_isapply = db.Column(db.String(255), nullable=False)  # 是否已申领就业创业证
    c_date_source = db.Column(db.String(255), nullable=False, server_default='-')  # 数据来源

    def to_dict(self):
        dic = {
            "id": self.id,
            "c_accept_batch": self.c_accept_batch,
            "c_company_name": self.c_company_name,
            "c_ID": self.c_ID,
            "c_name": self.c_name,
            "c_sex": self.c_sex,
            "c_birth": self.c_birth,
            "c_degree": self.c_degree,
            "c_population": self.c_population,
            "c_location": self.c_location,
            "c_register_type": self.c_register_type,
            "c_contract_start_date": self.c_contract_start_date,
            "c_contract_end_date": self.c_contract_end_date,
            "c_relieve_date": self.c_relieve_date,
            "c_register_date": self.c_register_date,
            "c_isapply": self.c_isapply,
            "c_date_source": self.c_date_source
        }
        return dic


class CySocialPayInfo(db.Model):
    """
    社保缴纳信息
    """
    __tablename__ = 'cySocialPay_info'
    __bind_key__ = "cyddjybt"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    s_ID = db.Column(db.String(255), nullable=False)  # 公民身份证号码 关联人员信息的证件号码
    s_pay_date = db.Column(db.String(255), nullable=False)  # 投保日期
    s_old_base = db.Column(db.String(255), nullable=False)  # 养老缴费基数
    s_medical_base = db.Column(db.String(255), nullable=True)  # 医疗缴费基数
    s_old_insur = db.Column(db.String(255), nullable=False)  # 个人养老保险
    s_unemploy_insur = db.Column(db.String(255), nullable=False)  # 个人失业保险
    s_injury_insur = db.Column(db.String(255), nullable=False)  # 个人工伤保险
    s_medical_insur = db.Column(db.String(255), nullable=False)  # 个人医疗保险
    s_c_old_insur = db.Column(db.String(255), nullable=False)  # 单位养老保险
    s_c_unemploy_insur = db.Column(db.String(255), nullable=False)  # 单位失业保险
    s_c_injury_insur = db.Column(db.String(255), nullable=False)  # 单位工伤保险
    s_c_medical_insur = db.Column(db.String(255), nullable=False)  # 单位医疗保险
    s_c_disease_insur = db.Column(db.String(255), nullable=False)  # 单位重大疾病保险
    s_c_birth_insur = db.Column(db.String(255), nullable=False)  # 单位生育保险
    s_social_num = db.Column(db.String(255), nullable=False)  # 个人社保号(社保)
    s_social_c_num = db.Column(db.String(255), nullable=False)  # 单位社保号（社保)
    s_social_c_name = db.Column(db.String(255), nullable=False)  # 单位名称(社保)
    s_social_credit_num = db.Column(db.String(255), nullable=False)  # 社会统一信用代码(社保)
    s_medical_num = db.Column(db.String(255), nullable=False)  # 个人社保号（医保)
    s_medical_c_num = db.Column(db.String(255), nullable=False)  # 单位社保号（医保)
    s_medical_c_name = db.Column(db.String(255), nullable=False)  # 单位名称(医保)
    s_medical_credit_num = db.Column(db.String(255), nullable=False)  # 社会统一信用代码(医保)

    def to_dict(self):
        dic = {
            "id": self.id,
            "s_ID": self.s_ID,
            "s_pay_date": self.s_pay_date,
            "s_old_base": self.s_old_base,
            "s_medical_base": self.s_medical_base,
            "s_old_insur": self.s_old_insur,
            "s_unemploy_insur": self.s_unemploy_insur,
            "s_injury_insur": self.s_injury_insur,
            "s_medical_insur": self.s_medical_insur,
            "s_c_old_insur": self.s_c_old_insur,
            "s_c_unemploy_insur": self.s_c_unemploy_insur,
            "s_c_injury_insur": self.s_c_injury_insur,
            "s_c_medical_insur": self.s_c_medical_insur,
            "s_c_disease_insur": self.s_c_disease_insur,
            "s_c_birth_insur": self.s_c_birth_insur,
            "s_social_num": self.s_social_num,
            "s_social_c_num": self.s_social_c_num,
            "s_social_c_name": self.s_social_c_name,
            "s_social_credit_num": self.s_social_credit_num,
            "s_medical_num": self.s_medical_num,
            "s_medical_c_num": self.s_medical_c_num,
            "s_medical_c_name": self.s_medical_c_name,
            "s_medical_credit_num": self.s_medical_credit_num,
        }
        return dic


class CyBusinessInfo(db.Model):
    """
    商事记录信息
    """
    __tablename__ = 'cyBusiness_info'
    __bind_key__ = 'cyddjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    b_register_num = db.Column(db.String(255), nullable=False)  # 商事注册号
    b_credit_num = db.Column(db.String(255), nullable=False)  # 统一社会信用代码
    b_company = db.Column(db.String(255), nullable=True)  # 单位名称
    b_charge_name = db.Column(db.String(255), nullable=False)  # 法定代表人
    b_ID = db.Column(db.String(255), nullable=False)  # 法人证件号码  关联人员信息的证件号码
    b_main_type = db.Column(db.String(255), nullable=True)  # 商事主体类型
    b_pro_type = db.Column(db.String(255), nullable=True)  # 主营项目类别
    b_date = db.Column(db.String(255), nullable=True)  # 成立时间
    b_state = db.Column(db.String(255), nullable=False)  # 状态
    b_relieve_date = db.Column(db.String(255), nullable=True, server_default='-')  # 状态

    def to_dict(self):
        dic = {
            "id": self.id,
            "b_register_num": self.b_register_num,
            "b_credit_num": self.b_credit_num,
            "b_company": self.b_company,
            "b_varcharge_name": self.b_charge_name,
            "b_varcharge_ID": self.b_ID,
            "b_main_type": self.b_main_type,
            "b_pro_type": self.b_pro_type,
            "b_date": self.b_date,
            "b_state": self.b_state,
            "b_relieve_date": self.b_relieve_date,
        }
        return dic


class CyAllowanceInfo(db.Model):
    """
    个人补贴享受情况
    """
    __tablename__ = 'cyAllowance_info'
    __bind_key__ = 'cyddjybt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  #
    a_apply_date = db.Column(db.String(255), nullable=False)  # 申报期
    a_apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    a_name = db.Column(db.String(255), nullable=False)  # 法定代表人
    a_ID = db.Column(db.String(255), nullable=False)  # 法人证件号码  关联人员信息的证件号码
    a_sex = db.Column(db.String(255), nullable=False)  # 性别
    a_age = db.Column(db.Integer, nullable=False)  # 年龄
    a_isCity = db.Column(db.String(255), nullable=False)  # 是否本市
    a_contract_date = db.Column(db.String(255), nullable=False)  # 合同起止日期
    a_company_name = db.Column(db.String(255), nullable=False)  # 企业名称
    a_register_num = db.Column(db.String(255), nullable=False)  # 统一社会信用代码
    a_setUp_date = db.Column(db.String(255), nullable=False)  # 创业成立时间
    a_belong = db.Column(db.String(255), nullable=False)  # 所属区街
    a_audit = db.Column(db.String(255), nullable=False)  # 操作人
    a_audit_state = db.Column(db.String(255), nullable=False)  # 审核状态
    a_approval_date = db.Column(db.String(255), nullable=False)  # 核准日期
    a_isDelete = db.Column(db.String(255), nullable=False)  # 是否有删除标识

    def to_dict(self):
        dic = {
            "id": self.id,
            "a_apply_date": self.a_apply_date,
            "a_apply_num": self.a_apply_num,
            "a_name": self.a_name,
            "a_ID": self.a_ID,
            "a_sex": self.a_sex,
            "a_age": self.a_age,
            "a_isCity": self.a_isCity,
            "a_contract_date": self.a_contract_date,
            "a_company_name": self.a_company_name,
            "a_register_num": self.a_register_num,
            "a_setUp_date": self.a_setUp_date,
            "a_belong": self.a_belong,
            "a_audit": self.a_audit,
            "a_audit_state": self.a_audit_state,
            "a_approval_date": self.a_approval_date,
            "a_isDelete": self.a_isDelete,
        }
        return dic


class CyBackRecord_info(db.Model):
    """回填回退记录信息"""
    __tablename__ = "cyBackRecord_info"
    __bind_key__ = "cyddjybt"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    br_apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    br_company = db.Column(db.String(255), nullable=False)  # 企业名称
    br_person_ID = db.Column(db.String(255), nullable=False, default="", server_default='')  # 人员证件号码
    br_person_name = db.Column(db.String(255), nullable=False, default="", server_default='')  # 人员名字
    br_fill_back = db.Column(db.Integer, nullable=False, server_default=text('0'))  # 操作名称0：无操作，1：回填，2：回退
    br_detail = db.Column(db.String(255), nullable=False, default="", server_default='无')  # 操作详情
    br_fillBackLink = db.Column(db.Integer, nullable=True)  # 回退步骤 0为区审核，1为待报批
    br_state = db.Column(db.String(255), nullable=False)  # 操作状态 等待 成功 失败
    br_identify_person = db.Column(db.String(255), nullable=True)  # 审核人名字
    br_cid = db.Column(db.Integer, nullable=True)  # 关联id 用于定位个人
    br_street_name = db.Column(db.String(255), nullable=True)  # 所属街道

    # 审核级别
    br_type = db.Column(db.Integer, nullable=True)  # 审核权限类型，（0：街道，1：区级）
    result = db.Column(db.Integer, nullable=True)  # 审核结果

    # 时间
    br_create_date = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    br_update_date = db.Column(TIMESTAMP, nullable=False)  # 更新时间


# todo:===============================一次性创业资助================================================
# todo:=============================================================================================

class YcxPersonInfo(db.Model):
    """人员信息表"""
    __tablename__ = 'ycxperson_info'
    __bind_key__ = 'ycxcyzz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    apply_time = db.Column(db.String(255), nullable=False)  # 申报期
    social_code = db.Column(db.String(255), nullable=False)  # 统一社会信用代码或注册号
    company = db.Column(db.String(255), nullable=False)  # 单位名称
    founding_date = db.Column(db.String(255), nullable=False)  # 创业成立日期
    company_type = db.Column(db.String(255), nullable=False)  # 初创企业类别
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    name = db.Column(db.String(255), nullable=False)  # 名字
    sex = db.Column(db.String(255), nullable=False)  # 性别
    age = db.Column(db.String(255), nullable=False)  # 年龄
    person_type = db.Column(db.String(255), nullable=False)  # 人员类别
    subsidy = db.Column(db.String(255), nullable=False)  # 补贴金额
    is_net = db.Column(db.String(255), nullable=False)  # 是否网办
    examine_status = db.Column(db.String(255), nullable=False)  # 审核状态
    examine_stated = db.Column(db.String(255), nullable=True)  # 审核说明
    card_type = db.Column(db.String(255), nullable=False)  # 证件类型
    pass_num = db.Column(db.String(255), nullable=True)  # 通行证号码
    birthday = db.Column(db.String(255), nullable=False)  # 出生日期
    jobsdiff_type = db.Column(db.String(255), nullable=False)  # 就业困难类别
    disabled_num = db.Column(db.String(255), nullable=True)  # 残疾人证书号码
    graduate_type = db.Column(db.String(255), nullable=False)  # 毕业生类别
    graduate_school = db.Column(db.String(255), nullable=True)  # 毕业院校
    graduate_date = db.Column(db.String(255), nullable=True)  # 毕业日期
    registered_office = db.Column(db.String(255), nullable=False)  # 企业注册地
    is_socialsecurity = db.Column(db.String(255), nullable=False)  # 是否发放到社保卡
    socialsecurity_num = db.Column(db.String(255), nullable=False)  # 社保卡号
    bank = db.Column(db.String(255), nullable=False)  # 开户银行
    account_name = db.Column(db.String(255), nullable=False)  # 开户名称
    bank_account = db.Column(db.String(255), nullable=False)  # 银行账号
    manager = db.Column(db.String(255), nullable=False)  # 经手人
    manager_phone = db.Column(db.String(255), nullable=False)  # 经手人联系电话
    company_phone = db.Column(db.String(255), nullable=False)  # 单位办公电话
    remark = db.Column(db.String(255), nullable=True)  # 备注
    capital_type = db.Column(db.String(255), nullable=False)  # 资金类别
    agent = db.Column(db.String(255), nullable=False)  # 经办人
    handling_date = db.Column(db.String(255), nullable=False)  # 经办日期
    handling_company = db.Column(db.String(255), nullable=False)  # 经办机构
    diploma_path = db.Column(db.String(2000), nullable=True)  # 毕业证附件路径
    # 额外参数
    get_data_state = db.Column(db.Boolean, nullable=False, server_default=text('False'))  # 数据抓取状态
    person_detail_info = db.Column(db.Boolean, nullable=False, server_default=text('False'))  # 数据抓取状态
    isaudit = db.Column(db.Boolean, nullable=False, server_default=text('False'))  # 是否审核完成
    auditor = db.Column(db.String(255), nullable=True)  # 审核人
    audit_date = db.Column(db.String(255), nullable=True)  # 审核时间
    robot_result = db.Column(db.Boolean, nullable=True)  # 机器人预审结果
    detail = db.Column(db.String(1000), nullable=True)  # 预审详情
    search_varcharge = db.Column(db.String(255), nullable=True)  # 法人名字结果
    person_result = db.Column(db.Boolean, nullable=True)  # 人工审核结果
    # 时间
    create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    update_time = db.Column(TIMESTAMP, nullable=False)  # 更新时间

    def to_dict(self):
        dic = {
            "id": self.id,
            "apply_num": self.apply_num,
            "apply_time": self.apply_time,
            "social_code": self.social_code,
            "company": self.company,
            "founding_date": self.founding_date,
            "company_type": self.company_type,
            "card_ID": self.card_ID,
            "name": self.name,
            "sex": self.sex,
            "age": self.age,
            "person_type": self.person_type,
            "subsidy": self.subsidy,
            "is_net": self.is_net,
            "examine_status": self.examine_status,
            "examine_stated": self.examine_stated,
            "card_type": self.card_type,
            "pass_num": self.pass_num,
            "birthday": self.birthday,
            "jobsdiff_type": self.jobsdiff_type,
            "disabled_num": self.disabled_num,
            "graduate_type": self.graduate_type,
            "graduate_school": self.graduate_school,
            "graduate_date": self.graduate_date,
            "registered_office": self.registered_office,
            "is_socialsecurity": self.is_socialsecurity,
            "socialsecurity_num": self.socialsecurity_num,
            "bank": self.bank,
            "account_name": self.account_name,
            "bank_account": self.bank_account,
            "manager": self.manager,
            "manager_phone": self.manager_phone,
            "company_phone": self.company_phone,
            "remark": self.remark,
            "capital_type": self.capital_type,
            "agent": self.agent,
            "handling_date": self.handling_date,
            "handling_company": self.handling_company,
            "diploma_path": self.diploma_path,
            "get_data_state": self.get_data_state,
            "person_detail_info": self.person_detail_info,
            "isaudit": self.isaudit,
            "auditor": self.auditor,
            "audit_date": self.audit_date,
            "robot_result": self.robot_result,
            "detail": self.detail,
            "search_varcharge": self.search_varcharge,
            "person_result": self.person_result,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }

        return dic


class YcxSocialSecurity(db.Model):
    """社保缴纳信息表"""
    __tablename__ = 'ycxsocial_security'
    __bind_key__ = 'ycxcyzz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    Insured_date = db.Column(db.String(255), nullable=False)  # 投保日期
    old_base = db.Column(db.String(255), nullable=False)  # 养老缴费基数
    medical_base = db.Column(db.String(255), nullable=False)  # 医疗缴费基数
    old_insur = db.Column(db.String(255), nullable=False)  # 个人养老保险
    unemploy_insur = db.Column(db.String(255), nullable=False)  # 个人失业保险
    injury_insur = db.Column(db.String(255), nullable=False)  # 个人工伤保险
    medical_insur = db.Column(db.String(255), nullable=False)  # 个人医疗保险
    c_old_insur = db.Column(db.String(255), nullable=False)  # 单位养老保险
    c_unemploy_insur = db.Column(db.String(255), nullable=False)  # 单位失业保险
    c_injury_insur = db.Column(db.String(255), nullable=False)  # 单位工伤保险
    c_medical_insur = db.Column(db.String(255), nullable=False)  # 单位医疗保险
    c_disease_insur = db.Column(db.String(255), nullable=False)  # 单位重大疾病
    c_birth_insur = db.Column(db.String(255), nullable=False)  # 单位生育保险
    social_num = db.Column(db.String(255), nullable=False)  # 社保个人社保号
    social_c_num = db.Column(db.String(255), nullable=False)  # 社保单位社保号
    social_c_name = db.Column(db.String(255), nullable=False)  # 社保单位名称
    social_credit_num = db.Column(db.String(255), nullable=False)  # 社保统一信用代码
    medical_num = db.Column(db.String(255), nullable=False)  # 医保个人社保号
    medical_c_num = db.Column(db.String(255), nullable=False)  # 医保单位社保号
    medical_c_name = db.Column(db.String(255), nullable=False)  # 医保单位名称
    medical_credit_num = db.Column(db.String(255), nullable=False)  # 医保统一信用代码

    def to_dict(self):
        dic = {
            "id": self.id,
            "card_ID": self.card_ID,
            "Insured_date": self.Insured_date,
            "old_base": self.old_base,
            "unemploy_insur": self.unemploy_insur,
            "injury_insur": self.injury_insur,
            "medical_insur": self.medical_insur,
            "c_old_insur": self.c_old_insur,
            "c_unemploy_insur": self.c_unemploy_insur,
            "c_injury_insur": self.c_injury_insur,
            "c_medical_insur": self.c_medical_insur,
            "c_disease_insur": self.c_disease_insur,
            "c_birth_insur": self.c_birth_insur,
            "social_num": self.social_num,
            "social_c_num": self.social_c_num,
            "social_c_name": self.social_c_name,
            "social_credit_num": self.social_credit_num,
            "medical_num": self.medical_num,
            "medical_c_name": self.medical_c_name,
            "medical_credit_num": self.medical_credit_num,
        }

        return dic


class YcxUnemployInfo(db.Model):
    """失业登记信息表"""
    __tablename__ = 'ycxunemploy_info'
    __bind_key__ = 'ycxcyzz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    e_serial_num = db.Column(db.String(255), nullable=False)  # 失业记录流水号
    e_employ_num = db.Column(db.String(255), nullable=False)  # 就业创业证号码
    e_ID = db.Column(db.String(255), nullable=False)  # 公民身份证号码
    e_name = db.Column(db.String(255), nullable=False)  # 姓名
    e_population = db.Column(db.String(255), nullable=False)  # 户口性质
    e_register_num = db.Column(db.String(255), nullable=False)  # 失业登记号
    e_register_type = db.Column(db.String(255), nullable=False)  # 登记类别
    e_start_date = db.Column(db.String(255), nullable=False)  # 失业有效始期
    e_end_date = db.Column(db.String(255), nullable=False)  # 失业有效终期
    e_register_date = db.Column(db.String(255), nullable=False)  # 登记日期

    def to_dict(self):
        dic = {
            "id": self.id,
            "e_serial_num": self.e_serial_num,
            "e_employ_num": self.e_employ_num,
            "e_ID": self.e_ID,
            "e_name": self.e_name,
            "e_population": self.e_population,
            "e_register_num": self.e_register_num,
            "e_register_type": self.e_register_type,
            "e_start_date": self.e_start_date,
            "e_end_date": self.e_end_date,
            "e_register_date": self.e_register_date
        }

        return dic


class YcxHardIdentifyInfo(db.Model):
    """困难认定信息表"""
    __tablename__ = 'ycxhardidentify_info'
    __bind_key__ = 'ycxcyzz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    h_name = db.Column(db.String(255), nullable=False)  # 姓名
    h_ID = db.Column(db.String(255), nullable=False)  # 公民身份证号码
    h_employ_type = db.Column(db.String(255), nullable=False)  # 就业困难人员类型
    h_apply_date = db.Column(db.String(255), nullable=False)  # 认定申请日期
    h_identify_date = db.Column(db.String(255), nullable=False)  # 审核认定日期
    h_exit_date = db.Column(db.String(255), nullable=False)  # 退出认定日期
    h_state = db.Column(db.String(255), nullable=False)  # 审核状态
    h_ID_state = db.Column(db.String(255), nullable=False)  # 身份认定状态
    h_identify_way = db.Column(db.String(255), nullable=False)  # 认定申请途径
    h_apply_location = db.Column(db.String(255), nullable=False)  # 认定申请行政区划

    def to_dict(self):
        dic = {
            "id": self.id,
            "h_name": self.h_name,
            "h_ID": self.h_ID,
            "h_employ_type": self.h_employ_type,
            "h_apply_date": self.h_apply_date,
            "h_identify_date": self.h_identify_date,
            "h_exit_date": self.h_exit_date,
            "h_state": self.h_state,
            "h_ID_state": self.h_ID_state,
            "h_identify_way": self.h_identify_way,
            "h_apply_location": self.h_apply_location
        }

        return dic


class YcxbackInfo(db.Model):
    """回填回退表"""
    __tablename__ = 'ycxback_info'
    __bind_key__ = 'ycxcyzz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    fill_back = db.Column(db.Integer, nullable=False)  # 回填还是回退
    fill_back_link = db.Column(db.Boolean, nullable=False)  # 回退环节
    state = db.Column(db.String(255), nullable=False)  # 回填状态
    detail = db.Column(db.String(255), nullable=True)  # 操作详情
    identify_person = db.Column(db.String(255), nullable=True)  # 办理人
    # 时间
    create_time = db.Column(db.DateTime, nullable=False, server_default=func.now())  # 创建时间
    update_time = db.Column(TIMESTAMP, nullable=False)  # 更新时间

    def to_dict(self):
        dic = {
            "id": self.id,
            "apply_num": self.apply_num,
            "card_ID": self.card_ID,
            "fill_back": self.fill_back,
            "fill_back_link": self.fill_back_link,
            "state": self.state,
            "detail": self.detail,
            "identify_person": self.identify_person,
            "create_time": self.create_time,
            "update_time": self.update_time
        }

        return dic


class YcxaduditInfo(db.Model):
    """审核记录表"""
    __tablename__ = 'ycxaudit_info'
    __bind_key__ = 'ycxcyzz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # id 自增
    apply_num = db.Column(db.String(255), nullable=False)  # 申领编号
    card_ID = db.Column(db.String(255), nullable=False)  # 证件号码
    result = db.Column(db.Boolean, nullable=True)  # 人工审核结果
    new_comment = db.Column(db.String(1000), nullable=True)  # 新增审核说明
    name = db.Column(db.String(255), nullable=True)  # 修改信息的审核人名称
    name_date = db.Column(TIMESTAMP, nullable=False)  # 修改时间

    def to_dict(self):
        dic = {
            "id": self.id,
            "apply_num": self.apply_num,
            "card_ID": self.card_ID,
            "result": self.result,
            "new_comment": self.new_comment,
            "name": self.name,
            "name_date": self.name_date
        }

        return dic


if __name__ == '__main__':
    # manager.run()
    db.create_all()
