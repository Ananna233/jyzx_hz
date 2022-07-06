import datetime
import decimal
import uuid
import re
import config
import pymysql
from flask.json import JSONEncoder as BaseJSONEncoder
from sqlalchemy import and_, or_, tuple_, func, extract, within_group
from app.models import db, CompanyInfo, PersonInfo, DetailPayInfo, UnemployInfo, HardIdentifyInfo, RecordInfo, \
    SocialPayInfo, FieldMapping, BusinessInfo, UpdateRecordInfo, Back_record_info
import flask_sqlalchemy
# from app.static.verb import text_message, pre_rgister_agent, birth_letter, province, holidays_list, workdays_list, country_major, foreign_come_major, foreign_come, condition
from sqlalchemy import case
from dateutil.relativedelta import relativedelta
import logging
import requests
import urllib3
import time
urllib3.disable_warnings()



class JSONEncoder(BaseJSONEncoder):

    def default(self, o):
        """
        如有其他的需求可直接在下面添加
        :param o:
        :return:
        """
        if isinstance(o, datetime.datetime):
            # 格式化时间
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, datetime.date):
            # 格式化日期
            return o.strftime('%Y-%m-%d')
        if isinstance(o, decimal.Decimal):
            # 格式化高精度数字
            return str(o)
        if isinstance(o, uuid.UUID):
            # 格式化uuid
            return str(o)
        if isinstance(o, bytes):
            # 格式化字节数据
            return o.decode("utf-8")
        return super(JSONEncoder, self).default(o)


class ResMsg(object):
    """
    封装响应文本
    """

    def __init__(self, data=None, code=0):
        # 获取请求中语言选择,默认为中文

        self._data = data
        self._msg = '成功'
        self._code = code

    def update(self, code=None, data=None, msg=None):
        """
        更新默认响应文本
        :param code:响应编码
        :param data: 响应数据
        :param msg: 响应消息
        :return:
        """
        if code is not None:
            self._code = code
        if data is not None:
            self._data = data
        if msg is not None:
            self._msg = msg

    def add_field(self, name=None, value=None):
        """
        在响应文本中加入新的字段，方便使用
        :param name: 变量名
        :param value: 变量值
        :return:
        """
        if name is not None and value is not None:
            self.__dict__[name] = value

    @property
    def data(self):
        """
        输出响应文本内容
        :return:
        """
        body = self.__dict__
        body["data"] = body.pop("_data")
        body["msg"] = body.pop("_msg")
        body["code"] = body.pop("_code")
        return body


class ToolFunc:
    def __init__(self, **kwargs):
        self.bus_id = kwargs.get('bus_id', None)
        self.inst_id = kwargs.get('inst_id', None)
        self.mapping = db.session.query(FieldMapping.sql_key, FieldMapping.sql_zh).all()
        self.fields = dict(self.mapping)

    @staticmethod
    def static_fields():
        mapping = db.session.query(FieldMapping.sql_key, FieldMapping.sql_zh).all()
        fields = dict(mapping)
        return fields

    def mapping_field(self, fields, results, status_data: dict = None):
        data = list()
        if results:
            for idx, item in enumerate(results):
                temp = self.mapping_base(fields, item, status_data[idx] if status_data else None)
                data.append(temp)
        return data

    @staticmethod
    def mapping_base(fields, data, status_data: dict = None):
        temp = list()
        if data:
            for key in data.keys():
                # 字段映射匹配
                temp_dict = {"en_name": key, "zh_name": fields.get(key), "value": getattr(data, key)}
                if status_data:
                    temp_dict["value_status"] = getattr(status_data, str(key) + '_status', None)
                temp.append(temp_dict)
        return temp

    # def get_pre_check_rst(self):
    #     """根据bus_id 和inst_id 获取该人的预审结果 并综合所有预审结果给出最终判断（暂用于列表页字段体现）[公司/个人/随迁]"""
    #     fields = self.static_fields()
    #     db_session_q = DBSessionQuery(bus_id=self.bus_id, inst_id=self.inst_id)
    #
    #     # 查询公司和个人信息
    #     user_company_result = db_session_q.designated_user_company_query()
    #     user_company_data = self.mapping_base(fields=fields, data=user_company_result)
    #     the_user_company_data, user_msg = get_info_check(user_company_data, self.bus_id,
    #                                                      self.inst_id, origin=user_company_result)
    #
    #     # 查询随迁家属
    #     user_accompany_result = db_session_q.designated_user_accompany_query()
    #     user_accompany_data = self.mapping_field(fields=fields, results=user_accompany_result)
    #
    #     # 随迁家属验证
    #     the_user_accompany_data, accompany_msg = get_accompany_check(user_accompany_data, self.bus_id, self.inst_id,
    #                                                                  origin=user_accompany_result)
    #     # 附件
    #     user_attach_result = db_session_q.designated_user_attach_query()
    #     user_attach_data = self.mapping_field(fields=fields, results=user_attach_result)
    #
    #     check_accompany = check_company = check_attach = True
    #     if the_user_company_data:
    #         for item in the_user_company_data:
    #             if item.get('result', None) is not None and item.get('en_name', None) not in ['ui_talent_category',
    #                                                                                           'ui_school']:
    #                 check_company = False
    #     if the_user_accompany_data:
    #         for one_accompany in the_user_accompany_data:
    #             for item in one_accompany:
    #                 if item.get('result', None) is not None and item.get('en_name', None) != 'uac_accompany_birthday':
    #                     check_company = False
    #     if user_attach_data:
    #         for one_attach in user_attach_data:
    #             for item in one_attach:
    #                 if item.get('result', None) is not None:
    #                     check_attach = False
    #
    #     final_check = "不通过" if False in [check_accompany, check_attach, check_company] else "通过"
    #     return final_check


class DBSessionQuery:
    """
    整合各类查询
    """

    def __init__(self, **kwargs):
        self.apply_num = kwargs.get("apply_num", None)  # 公司申领编号
        self.list_type = kwargs.get("list_type", None)  # 列表类型
        self.id = kwargs.get("id", None)  # 人员id
        self.company_name = kwargs.get('company_name', None)  # 公司名字

    def get_tb_date(self):
        """获取投保日期"""
        year = self.apply_num[-7:-3]
        season = self.apply_num[-2]
        ls = []
        if season == '1':
            ls = [str(year) + '01', str(year) + '02', str(year) + '03']
        elif season == '2':
            ls = [str(year) + '04', str(year) + '05', str(year) + '06']
        elif season == '3':
            ls = [str(year) + '07', str(year) + '08', str(year) + '09']
        elif season == '4':
            ls = [str(year) + '10', str(year) + '11', str(year) + '12']
        # ls.append('')
        return ls

    @staticmethod
    def get_company_list_query():
        """
        返回公司列表

        """
        company_list = db.session.query(
            CompanyInfo.c_apply_season,
            CompanyInfo.c_isnet,
            CompanyInfo.c_isprovince,
            CompanyInfo.c_isseason,
            CompanyInfo.c_season_add_count,
            CompanyInfo.c_apply_num,
            CompanyInfo.c_name,
            CompanyInfo.c_hard_employ_count,
            CompanyInfo.c_graduate_count,
            CompanyInfo.c_army_count,
            CompanyInfo.c_affect_person_count,
            CompanyInfo.c_poor_count,
            CompanyInfo.c_total,
            CompanyInfo.c_old_insur,
            CompanyInfo.c_unemploy_insur,
            CompanyInfo.c_injury_insur,
            CompanyInfo.c_birth_insur,
            CompanyInfo.c_medical_insur,
            CompanyInfo.c_social_total,
            CompanyInfo.c_general_post_subsidy,
            CompanyInfo.c_person_result,
            CompanyInfo.c_identify_person,
            CompanyInfo.c_get_person_state,
            CompanyInfo.isIdentify,
            CompanyInfo.c_extra_social_count,
            CompanyInfo.c_street_author,
            CompanyInfo.c_street_belong,
            CompanyInfo.c_register_num,
            CompanyInfo.c_detail,
        ).filter().order_by(CompanyInfo.isIdentify.desc()).order_by(CompanyInfo.c_audit_order.desc())

        return company_list

    def get_company_info(self):
        """
        公司基本信息字段
        """
        company_info = db.session.query(

            CompanyInfo.c_register_num,
            CompanyInfo.c_name,
            CompanyInfo.c_apply_num,
            CompanyInfo.c_social_num,
            CompanyInfo.c_size,
            CompanyInfo.c_apply_season,
            CompanyInfo.c_bank,
            CompanyInfo.c_account, CompanyInfo.c_bank_card,
            CompanyInfo.c_charge_ID, CompanyInfo.c_charge_name,
            CompanyInfo.c_contact_name, CompanyInfo.c_contact_phone,
            CompanyInfo.c_apply_count, CompanyInfo.c_hard_employ_count,
            CompanyInfo.c_graduate_count, CompanyInfo.c_army_count,
            CompanyInfo.c_affect_person_count, CompanyInfo.c_old_insur,
            CompanyInfo.c_unemploy_insur, CompanyInfo.c_injury_insur,
            CompanyInfo.c_birth_insur, CompanyInfo.c_medical_insur,
            CompanyInfo.c_social_total, CompanyInfo.c_general_post_subsidy,
            CompanyInfo.c_poor_count, CompanyInfo.c_special_fund_count,
            CompanyInfo.c_unemploy_fund_count, CompanyInfo.c_net_office,
            CompanyInfo.c_special_fund, CompanyInfo.c_unemploy_fund,
            CompanyInfo.c_success_count, CompanyInfo.c_success_fund,
            CompanyInfo.c_fail_count, CompanyInfo.c_fail_fund,
            CompanyInfo.c_identify_comment, CompanyInfo.c_robot_result,
            CompanyInfo.c_explain, CompanyInfo.c_detail,
            CompanyInfo.c_search_location, CompanyInfo.c_search_charge,
            CompanyInfo.c_get_person_state,
            CompanyInfo.c_street_author,
            CompanyInfo.c_street_belong
        ).filter(CompanyInfo.c_apply_num == self.apply_num).order_by(CompanyInfo.c_create_time)
        return company_info

    def get_approval_list(self):
        """
        获取待审核列表
        """
        person_list = db.session.query(
            PersonInfo.p_ID,
            PersonInfo.p_list_place,
            PersonInfo.p_name,
            PersonInfo.p_sex,
            PersonInfo.p_age,
            PersonInfo.p_type,
            PersonInfo.p_contract_start_date,
            PersonInfo.p_contract_end_date, PersonInfo.p_old_insur,
            PersonInfo.p_injury_insur, PersonInfo.p_unemploy_insur,
            PersonInfo.p_medical_insur, PersonInfo.p_birth_insur,
            PersonInfo.p_society_total, PersonInfo.p_normal_fund,
            PersonInfo.p_apply_month, PersonInfo.p_iscarry,
            PersonInfo.p_detail_info,
            PersonInfo.p_file_path,
            PersonInfo.p_social_company_identical,
            PersonInfo.p_final_list,
            PersonInfo.p_street_result,
            PersonInfo.p_person_result
        ).filter(PersonInfo.p_c_apply_num == self.apply_num, PersonInfo.p_person_result == self.list_type)
        return person_list

    def get_person_info(self):
        """
        获取人员信息
        """
        person_info = db.session.query(
            PersonInfo.p_type,
            PersonInfo.p_ID_type,
            PersonInfo.p_ID,
            PersonInfo.p_pass_num,
            PersonInfo.p_name,
            PersonInfo.p_sex,
            PersonInfo.p_age, PersonInfo.p_social_num,
            PersonInfo.p_contract_start_date, PersonInfo.p_contract_end_date,
            PersonInfo.p_hard_type, PersonInfo.p_disabled_num,
            PersonInfo.p_isgraduate, PersonInfo.p_graduate_type,
            PersonInfo.p_graduate_school, PersonInfo.p_graduate_date,
            PersonInfo.p_pass_date, PersonInfo.p_isprovince,
            PersonInfo.p_old_insur, PersonInfo.p_unemploy_insur,
            PersonInfo.p_injury_insur, PersonInfo.p_birth_insur,
            PersonInfo.p_medical_insur, PersonInfo.p_normal_fund,
            PersonInfo.p_help_type, PersonInfo.p_reamark,
            # 预审结果
            PersonInfo.p_robot_result, PersonInfo.p_explain,
            PersonInfo.p_local_area, PersonInfo.p_verify_explain,
            # 六个日期
            PersonInfo.p_start_unemploy_date, PersonInfo.p_end_unemploy_date,
            PersonInfo.p_hard_identify_date, PersonInfo.p_start_contract_date,
            PersonInfo.p_end_contract_date, PersonInfo.p_contract_register_date,
            PersonInfo.p_file_path,
            PersonInfo.p_social_company_identical
        ).filter(PersonInfo.p_c_apply_num == self.apply_num, PersonInfo.p_ID == self.id)
        return person_info

    def get_company_predit(self):
        """
        企业预审结果
        """
        company_predit = db.session.query(
            CompanyInfo.c_robot_result, CompanyInfo.c_detail
        ).filter(CompanyInfo.c_apply_num == self.apply_num).first()
        return company_predit

    def get_person_predit(self):
        """人员预审结果"""
        person_predit = db.session.query(
            PersonInfo.p_robot_result, PersonInfo.p_detail
        ).filter(PersonInfo.p_c_apply_num == self.apply_num, PersonInfo.p_ID == self.id).first()
        return person_predit

    def get_detailPay_info(self):
        """
        查询具体月份补贴金额信息
        """
        detailPay_info = db.session.query(
            DetailPayInfo.d_pay_month,
            DetailPayInfo.d_old_insur,
            DetailPayInfo.d_injury_insur,
            DetailPayInfo.d_unemploy_insur,
            DetailPayInfo.d_birth_insur,
            DetailPayInfo.d_medical_insur,
            DetailPayInfo.d_normal_fund,
            DetailPayInfo.is_checked,
            DetailPayInfo.id,

        ).filter(DetailPayInfo.d_ID == self.id,
                 DetailPayInfo.d_apply_num == self.apply_num)
        return detailPay_info

    def get_unemploy_info(self):
        """
        查询失业登记信息
        """
        unemploy_info = db.session.query(
            UnemployInfo.e_serial_num,
            UnemployInfo.e_employ_num,
            UnemployInfo.e_ID,
            UnemployInfo.e_name,
            UnemployInfo.e_population,
            UnemployInfo.e_register_num,
            UnemployInfo.e_register_type,
            UnemployInfo.e_start_date,
            UnemployInfo.e_end_date,
            UnemployInfo.e_register_date,
            UnemployInfo.e_exist_forward,
        ).filter(UnemployInfo.e_ID == self.id)
        return unemploy_info

    def get_hardIdentify_info(self):
        """
        查询困难认定信息
        """
        hardIdentify_info = db.session.query(
            HardIdentifyInfo.h_name,
            HardIdentifyInfo.h_ID,
            HardIdentifyInfo.h_employ_type,
            HardIdentifyInfo.h_apply_date,
            HardIdentifyInfo.h_identify_date,
            HardIdentifyInfo.h_exit_date,
            HardIdentifyInfo.h_state,
            HardIdentifyInfo.h_identify_way,
            HardIdentifyInfo.h_apply_location,

        ).filter(HardIdentifyInfo.h_ID == self.id)
        return hardIdentify_info

    def get_record_info(self):
        """
        查询就业登记信息
        """
        record_info = db.session.query(
            RecordInfo.r_accept_batch,
            RecordInfo.r_company_name,
            RecordInfo.r_ID,
            RecordInfo.r_name,
            RecordInfo.r_sex,
            RecordInfo.r_birth,
            RecordInfo.r_degree,
            RecordInfo.r_population,
            RecordInfo.r_location,
            RecordInfo.r_register_type,
            RecordInfo.r_contract_start_date,
            RecordInfo.r_contract_end_date,
            RecordInfo.r_register_date,
            RecordInfo.r_isapply,
            RecordInfo.r_date_source,

        ).filter(RecordInfo.r_ID == self.id)
        return record_info

    def get_socialPay_info(self):
        """
        查询社保缴纳信息
        """
        socialPay_info = db.session.query(
            SocialPayInfo.s_pay_date,
            SocialPayInfo.s_old_base,
            SocialPayInfo.s_medical_base,
            SocialPayInfo.s_old_insur,
            SocialPayInfo.s_unemploy_insur,
            SocialPayInfo.s_injury_insur,
            SocialPayInfo.s_medical_insur,
            SocialPayInfo.s_c_old_insur,
            SocialPayInfo.s_c_unemploy_insur,
            SocialPayInfo.s_c_injury_insur,
            SocialPayInfo.s_c_medical_insur,
            SocialPayInfo.s_c_disease_insur,
            SocialPayInfo.s_c_birth_insur,
            SocialPayInfo.s_social_num,
            SocialPayInfo.s_social_c_num,
            SocialPayInfo.s_social_c_name,
            SocialPayInfo.s_social_credit_num,
            SocialPayInfo.s_medical_num,
            SocialPayInfo.s_medical_c_num,
            SocialPayInfo.s_medical_c_name,
            SocialPayInfo.s_medical_credit_num,
        ).filter(SocialPayInfo.s_ID == self.id).order_by(SocialPayInfo.s_pay_date.desc())
        return socialPay_info

    def get_business_info(self):
        """
        查询商事记录信息
        """
        business_info = db.session.query(
            BusinessInfo.b_register_num,
            BusinessInfo.b_credit_num,
            BusinessInfo.b_company,
            BusinessInfo.b_charge_name,
            BusinessInfo.b_ID,
            BusinessInfo.b_main_type,
            BusinessInfo.b_pro_type,
            BusinessInfo.b_date,
            BusinessInfo.b_state,
            BusinessInfo.b_relieve_date,
        ).filter(BusinessInfo.b_ID == self.id)
        return business_info

    def get_update_record_info(self):
        """
        查询审核记录信息
        """
        record_info = db.session.query(
            UpdateRecordInfo.u_update_date,
            UpdateRecordInfo.u_result,
            UpdateRecordInfo.u_new_comment,
            UpdateRecordInfo.u_name,

        ).filter(UpdateRecordInfo.u_ID == self.id)
        return record_info

    def get_back_record_info(self):
        """查询回填回退信息"""
        back_info = db.session.query(
            Back_record_info.id,
            Back_record_info.br_apply_season,
            Back_record_info.br_apply_num,
            Back_record_info.br_company,
            Back_record_info.br_fill_back,
            Back_record_info.br_state,
            Back_record_info.br_detail,
            Back_record_info.br_identify_person,
            Back_record_info.br_cid,
            Back_record_info.br_create_date,
            Back_record_info.br_update_date
        ).filter().order_by(Back_record_info.br_create_date.desc())
        return back_info

    def getDownLoadExcelData(self):
        """获取导出报表的数据"""
        company_obj = db.session.query(CompanyInfo.c_search_location,
                                       CompanyInfo.c_name,
                                       CompanyInfo.c_apply_num,
                                       CompanyInfo.c_identify_person,
                                       CompanyInfo.c_apply_season,
                                       CompanyInfo.c_register_num).filter(CompanyInfo.c_person_result != None)
        return company_obj


class RecatchData(object):
    """重新抓取部分信息"""
    def __init__(self,card_ID):
        self.card_ID = card_ID
        self.mysql_db = None
        mysql_db = pymysql.connect(host="127.0.0.1", user=config.USERNAME, password=config.PASSWORD, db="lcy",
                                   port=3306)
        cursor = mysql_db.cursor()
        # SQL 查询语句
        sql = "SELECT value from variable_mgt WHERE name='Cookie';"
        # 执行SQL语句
        cursor.execute(sql)
        # 获取所有工商信息，取最后一条数据
        self.Cookie = cursor.fetchone()[0]
        mysql_db.close()

    def insertSql(self, fieldList, arrayList, table,cursor):
        """入库
        :params FieldList 字段列表
        :params ArrayList 数据二维数组
        :params table 表名
        """
        val_list = []
        for arr in arrayList:
            val_list.append(str(tuple(arr)))
        sql = f"INSERT INTO {table}({','.join(fieldList)}) VALUES {','.join(val_list)};"
        logging.error(sql)
        result = cursor.execute(sql)
        return result

    def connectMysql(self):
        self.mysql_db = pymysql.connect(host="127.0.0.1", user=config.USERNAME, password=config.PASSWORD, db=config.DATABASE,
                                   port=3306)
        cursor = self.mysql_db.cursor()
        return cursor


    def getExitForward(self,link_param):
        """获取失业登记的注销去向 """
        url2 = "https://jypx.gzsi.gzhrlss:9500/gdld_gz/action/" + link_param
        url_list = url2.split("?")
        url = url_list[0] + "?ActionType=sygl_bdsydjgl_syxxcx_tcsyxxcx_s&" + url_list[1]

        payload = {}
        headers = {
            'Host': 'jypx.gzsi.gzhrlss:9500',
            'Referer': 'https://jypx.gzsi.gzhrlss:9500/gdld_gz/action/MainAction?ActionType=sygl_bdsydjgl_syxxcx_q',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E)',
            'Cookie': self.Cookie
        }

        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        tree = etree.HTML(response.text)
        zxqx = tree.xpath(
            "//table[@id='sygl_common_sydj_bdtcxx_edit']//td[contains(text(),'注销去向')]/following-sibling::td[1]/span/text()")
        if len(zxqx) == 0:
            exitForward = ""
        else:
            exitForward = zxqx[0]
        return exitForward

    def getUnemploymentInfo(self):
        """重新获取失业登记信息 001"""
        url = f"https://jypx.gzsi.gzhrlss:9500/gdld_gz/action/MainAction?ActionType=sygl_bdsydjgl_syxxcx_q&AAC002={self.card_ID}&check=Y&tableValidateStr=null"
        payload = {}
        headers = {
            'Cookie': self.Cookie,
            'Referer': 'https://jypx.gzsi.gzhrlss:9500/gdld_gz/action/MainAction?ActionType=sygl_bdsydjgl_syxxcx_q',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Host': 'jypx.gzsi.gzhrlss:9500'
        }

        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        tree = etree.HTML(response.text)
        table_list = tree.xpath("//table[@id='sygl_bdsydjgl_syxxcx_list']//tbody/tr")
        unemploy_list = []
        for tr in table_list:
            td_list = tr.xpath("./td/text()")
            for i in td_list:
                index = td_list.index(i)
                if i == " ":
                    td_list[index] = tr.xpath("./td//text()")[index + 2].strip()
                    if index == 2:
                        link_param1 = tree.xpath(f"//table[@id='sygl_bdsydjgl_syxxcx_list']//tr/td/a[contains(text(),'{tr.xpath('./td//text()')[index + 2].strip()}')]/@href")[0]
                        exitForward = self.getExitForward(link_param1)
                        td_list[1] = exitForward
                        time.sleep(1)
                else:
                    td_list[index] = i.strip()
            if len(td_list) >= 2:
                unemploy_list.append(td_list[1:])

        scursor = self.connectMysql()

        # todo:没有本地失业登记信息
        if len(unemploy_list) == 0:

            pass
        else:
            # 入库
            feildList = ["e_exist_forward","e_serial_num","e_ID","e_name","e_population","e_register_num","e_register_type","e_start_date","e_end_date","e_register_date"]
            result = self.insertSql(fieldList=feildList, arrayList=unemploy_list, table="unemploy_info", cursor=scursor)
            logging.error(f"入库结果：{result}")
        if self.mysql_db:
            self.mysql_db.close()
