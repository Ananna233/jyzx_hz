import ast
import datetime
import logging
import re

from app.models import *
from config import *


class ResMsg(object):
    """
    封装响应文本
    """

    def __init__(self, data=None, code=200):
        # 获取请求中语言选择,默认为中文

        self._data = data
        self._msg = ''
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


def getAccountAuthority(role):
    # 判断此账号为区级或者街道
    account_type = -1
    try:
        re_res = re.findall(".*?区(.*)", role)
        if len(re_res) > 0:
            if len(re_res[0]) > 0:
                # 街道账号
                account_type = 0
            else:
                # 区级账号
                account_type = 1
    except:
        account_type = 2  # 通用账号
    return account_type


# 接口6.新增人员回填记录
def insertPersonBackInfo(approval_type, approval_result, approval_person, br_cid, company_name, r_name, apply_num,
                         card_ID, street_name):
    # 再新增
    try:
        new_person_back_info = CyBackRecord_info()
        new_person_back_info.br_apply_num = apply_num
        new_person_back_info.br_company = company_name
        new_person_back_info.br_person_ID = card_ID
        new_person_back_info.br_person_name = r_name
        new_person_back_info.br_fill_back = 1
        new_person_back_info.br_state = "等待"
        new_person_back_info.br_identify_person = approval_person
        new_person_back_info.br_cid = br_cid
        new_person_back_info.br_street_name = street_name
        new_person_back_info.br_type = approval_type
        new_person_back_info.result = approval_result
        db.session.add(new_person_back_info)
        db.session.commit()
        return True
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()  # 回滚
        return False


# 接口6.修改人员审核信息
def updatePersonInfo(apply_num, card_ID, approval_type, approval_result, approval_person, approval_comment, final_list):
    # 先修改个人信息
    try:
        if approval_type == 0:  # 街道审核
            db.session.query(CyPersonInfo).filter(CyPersonInfo.r_apply_num == apply_num,
                                                  CyPersonInfo.r_ID == card_ID).update(
                {"r_street_result": approval_result, "r_street_person": approval_person,
                 "r_street_remark": approval_comment, "r_final_list": final_list}
            )
        elif approval_type == 1:  # 区级审核
            db.session.query(CyPersonInfo).filter(CyPersonInfo.r_apply_num == apply_num,
                                                  CyPersonInfo.r_ID == card_ID).update(
                {"r_person_result": approval_result, "r_identify_person": approval_person,
                 "r_person_remark": approval_comment, "r_final_list": final_list}
            )
        db.session.commit()
        return True
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()  # 回滚
        return False


# 接口6.添加企业回填记录
def insertCompanyBackInfo(approval_type, approval_person, apply_num, company_name, street_name, br_fill_back,
                          approval_result):
    try:
        new_company_back_info = CyBackRecord_info()
        new_company_back_info.br_apply_num = apply_num
        new_company_back_info.br_company = company_name
        new_company_back_info.br_person_ID = ""
        new_company_back_info.br_person_name = ""
        new_company_back_info.br_fill_back = br_fill_back
        new_company_back_info.br_detail = ""
        new_company_back_info.br_state = "等待"
        new_company_back_info.br_identify_person = approval_person
        new_company_back_info.br_street_name = street_name
        new_company_back_info.br_type = approval_type
        new_company_back_info.result = approval_result
        db.session.add(new_company_back_info)
        db.session.commit()
        return True
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()  # 回滚
        return False


class CyLogicalProcessing(object):
    def __init__(self, **kwargs):
        self.card_ID = kwargs.get('card_ID', None)  # 人员证件号码
        self.apply_num = kwargs.get('apply_num', None)  # 申领编号
        self.roleName = kwargs.get("roleName", None)  # 登录账号所在街道

        self.searchKey = kwargs.get("searchKey", {})  # 查询条件
        self.page = kwargs.get("page", {"pageNum": 1, "pageSize": 40})  # 页数

        self.auditor = kwargs.get("auditor", None)  # 审核人

        self.apply_num = kwargs.get("apply_num", None)  # 申领编号
        self.final_list = kwargs.get("final_list", None)  # 列表类型 1为成功列表，2为失败列表，0为待审核列表
        self.content = kwargs.get("content", None)  # 6. 审核结果

        self.cid = kwargs.get("cid", None)  # 11.企业回填表序号

    # 1.获取补贴申报个体列表
    def getItemObjectList(self):
        res = ResMsg()
        page_num = self.page.get("pageNum", 1)
        page_size = self.page.get("pageSize", 40)
        # 定义翻页参数
        page = {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": 0
        }
        # 筛选条件
        apply_season = self.searchKey.get("apply_season", None)  # 申领年季
        company_name = self.searchKey.get("company_name", None)  # 公司名称
        audit_state = self.searchKey.get("audit_state", None)  # 审核状态 1:审核通过 2：审核不通过 0：未审核
        auditor = self.searchKey.get("auditor", None)  # 审核人
        street_belong = self.searchKey.get("street_belong", None)  # 所属街道
        apply_num = self.searchKey.get("apply_num", None)  # 申领编号

        # 获取基础查询信息
        base_query = DBSessionQuery(apply_season=apply_season).getCompanyList()

        # 查询权限
        approved_type = getAccountAuthority(self.roleName)
        if approved_type not in [0, 1]:
            res.update(code=-1, msg="账号权限不正确，请使用街道账号或区账号登录！")
            return res.data
        if approved_type == 1:  # 区级
            if street_belong:
                base_query = base_query.filter(CyCompanyInfo.e_street_name == street_belong)
        elif approved_type == 0:
            base_query = base_query.filter(CyCompanyInfo.e_street_name == self.roleName)

        # 筛选
        if company_name and company_name != "" and company_name != "undefined":
            base_query = base_query.filter(CyCompanyInfo.e_company_name == company_name)

        if audit_state and audit_state != "" and audit_state != "undefined":  # 审核状态
            if approved_type == 0:  # 街道审核
                if audit_state == 0:  # 未审核
                    base_query = base_query.filter(CyCompanyInfo.e_street_person == None)
                elif audit_state == 1:  # 审核通过
                    base_query = base_query.filter(CyCompanyInfo.e_street_person != None,
                                                   CyCompanyInfo.e_street_result == 1)
                elif audit_state == 2:  # 审核不通过
                    base_query = base_query.filter(CyCompanyInfo.e_street_person != None,
                                                   CyCompanyInfo.e_street_result == 0)
            elif approved_type == 1:  # 区级审核
                if audit_state == 0:  # 未审核
                    base_query = base_query.filter(CyCompanyInfo.e_identify_person == None)
                elif audit_state == 1:  # 审核通过
                    base_query = base_query.filter(CyCompanyInfo.e_identify_person != None,
                                                   CyCompanyInfo.e_person_result == 1)
                elif audit_state == 2:  # 审核不通过
                    base_query = base_query.filter(CyCompanyInfo.e_identify_person != None,
                                                   CyCompanyInfo.e_person_result == 0)

        if auditor and auditor != "" and auditor != "undefined":
            if approved_type == 0:  # 街道审核
                base_query = base_query.filter(CyCompanyInfo.e_street_person == auditor)
            elif approved_type == 1:  # 区级审核
                base_query = base_query.filter(CyCompanyInfo.e_identify_person == auditor)

        if apply_num and apply_num != "" and apply_num != "undefined":
            base_query = base_query.filter(CyCompanyInfo.e_apply_num == apply_num)

        # 总数
        total = base_query.count()
        results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()

        fieldList = [
            "id", "e_apply_num", "e_declaration_period", "e_declaration_date", "e_quarter_add", "e_socialcredit_code",
            "e_company_name", "e_register_location", "e_establishment_date", "e_recruits_num", "e_company_type",
            "e_robot_result", "e_detail", "e_person_result", "e_identify_person", "e_street_name", "e_street_result",
            "e_street_person",
        ]

        dictList = DBSessionAction().getObjectListData(results, fieldList)
        # 标准化输出审核结果：
        for i in dictList:
            i["artificial_audit"] = i["e_person_result"]  # 区审核结果
            i["auditor"] = i["e_identify_person"]  # 区审核人
            i["street_result"] = i["e_street_result"]  # 街道审核结果
            i["street_person"] = i["e_street_person"]  # 街道审核人

        res.update(data={
            "page": {
                "pageNum": page["pageNum"],
                "pageSize": page["pageSize"],
                "total": total
            },
            "ItemCode": "cyddjybt",
            "ItemName": "创业带动就业补贴",
            "ItemType": 2,
            "data": dictList
        })
        return res.data

    # 2.获取申报时间列表
    def getApplyDate(self):
        res = ResMsg()
        # itemcode = self.itemcode  # 事项编号
        # 创业带动就业补贴
        today = datetime.datetime.today()  # 获取当前时间
        year = today.year
        month = today.month
        yearList = [year - 1, year]
        monthList = [12]
        for i in range(1, 13):
            if i % 2 == 0:
                monthList.append(i)
            else:
                monthList.append(i + 1)
        data = []
        for i in range(4):
            dic = {}
            if month <= 0:  # 月份<=0不是当前年度
                year = yearList[0]
            else:
                year = yearList[1]

            if monthList[month] < 9:  # 如果月份是9月前，补0
                dic['key'] = str(year * 10) + str(monthList[month])
            else:
                dic['key'] = str(year) + str(monthList[month])
            dic['name'] = '{}年{}月至{}年{}月'.format(year, monthList[month] - 1, year, monthList[month])
            data.append(dic)
            if monthList[month] == 2:  # 如果月份是2月，前一个受理期为当前月-3，避免bug
                month -= 3
            else:
                month -= 2
        if data == 'error' or data == "":
            res.update(msg='拉取办件详情信息失败', code=-1)
            return jsonify(reg.data)
        else:
            res.update(data=data)
            return res.data

    # 3.获取申报对象详情信息（单位信息）
    def getItemObjectDetail(self):
        res = ResMsg()
        data = DBSessionQuery(apply_num=self.apply_num).getCompanyInfo()
        filed_list = [
            "e_apply_num", "e_declaration_period", "e_declaration_date", "e_quarter_add", "e_socialcredit_code",
            "e_company_name", "e_register_location", "e_establishment_date", "e_recruits_num", "e_recruits_price",
            "e_online_processing", "e_company_social_security", "e_company_type", "e_legal_person", "e_ID", "e_manager",
            "e_manager_phone", "e_company_worktel", "e_bank", "e_bank_company", "e_bank_num", "e_success_count",
            "e_success_price", "e_failure_count", "e_cum_count", "e_eco_price_count", "e_cum_price", "e_eco_price",
            "e_remarks", "e_price_type", "e_first_social_count", "e_second_social_count", "e_is_xwCompany",
            "e_robot_result", "e_detail", "e_person_result", "e_instructions", "e_identify_person",
            "e_get_person_state", "e_addr", "e_street_name", "e_search_name", "e_search_established_time",
            "e_street_result", "e_street_person", "e_street_remark",
        ]

        dictList = DBSessionAction().getObjectInfoData(data, filed_list)
        # 标准化输出审核结果：
        dictList["artificial_audit"] = dictList["e_person_result"]  # 区审核结果
        dictList["auditor"] = dictList["e_identify_person"]  # 区审核人
        dictList["region_remark"] = dictList["e_instructions"]  # 区审核说明

        dictList["street_result"] = dictList["e_street_result"]  # 街道审核结果
        dictList["street_person"] = dictList["e_street_person"]  # 街道审核人
        dictList["street_remark"] = dictList["e_street_remark"]  # 街道审核说明

        res.update(data={
            "ItemCode": "cyddjybt",
            "ItemName": "创业带动就业补贴",
            "ItemType": 2,
            "data": dictList
        })
        return res.data

    # 4.获取申报对象人员列表
    def getObjectPersonList(self):
        res = ResMsg()
        page_num = self.page.get("pageNum", 1)
        page_size = self.page.get("pageSize", 10)
        # 定义翻页参数
        page = {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": 0
        }
        base_query = DBSessionQuery(apply_num=self.apply_num, final_list=self.final_list).getPersonList()
        total = base_query.count()
        results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()

        filed_list = ["id", "r_apply_num", "r_ID", "r_name", "r_sex", "r_age", "r_provinces", "r_contract_date",
                      "r_local_type", "r_instructions"]

        dictList = DBSessionAction().getObjectListData(results, filed_list)

        res.update(data={
            "page": {
                "pageNum": page["pageNum"],
                "pageSize": page["pageSize"],
                "total": total
            },
            "ItemCode": "cyddjybt",
            "ItemName": "创业带动就业补贴",
            "ItemType": 2,
            "data": dictList
        })
        return res.data

    # 5. 获取人员详细信息
    def getPersonDetailInfo(self):
        res = ResMsg()
        detailObj = {
            "ItemCode": "cyddjybt",
            "ItemName": "创业带动就业补贴",
            "ItemType": 2,
            "data": {
                "ID_list": [],  # 同企业人员列表
                "companyInfoData": {},  # 企业信息
                "personInfoData": {},  # 人员信息
                "allowanceInfoData": [],  # 个人补贴享受情况

                "recordInfoData": [],  # 就业登记
                "socialPayInfoData": [],  # 社保缴纳情况
                "xwCompanyInfoData": [],  # 小微企业信息
                "businessInfoData": [],  # 商事登记信息

                "companyPreditResult": {},  # 企业预审结果
                "personPreditResult": {}  # 个人预审结果
            }
        }
        try:
            person_info = DBSessionQuery(card_ID=self.card_ID, apply_num=self.apply_num).getPersonInfo()
            if person_info is None:
                res.update(msg="请求参数有误，获取人员信息失败！", code=-1)
                return res.data
            # personInfoData 人员详情信息
            person_info_filed_list = [
                "id", "r_apply_num", "r_ID", "r_name", "r_sex", "r_age", "r_provinces", "r_company_name",
                "r_contract_date", "r_local_type", "r_ID_type", "r_passnum", "r_social_num", "r_contract_start_date",
                "r_contract_end_date", "r_instructions", "r_remarks", "r_agent", "r_handling_date",
                "r_handling_location", "r_robot_result", "r_detail", "r_person_result", "r_person_remark",
                "r_identify_person", "r_person_detail", "r_social_state", "r_final_list", "r_street_result",
                "r_street_person", "r_street_remark",
            ]

            detailObj["data"]["personInfoData"] = DBSessionAction().getObjectInfoData(person_info,
                                                                                      person_info_filed_list)
            # 标准化输出审核结果：
            detailObj["data"]["personInfoData"]["auditor"] = detailObj["data"]["personInfoData"][
                "r_identify_person"]  # 区审核人
            detailObj["data"]["personInfoData"]["artificial_audit"] = detailObj["data"]["personInfoData"][
                "r_person_result"]  # 区审核结果
            detailObj["data"]["personInfoData"]["region_remark"] = detailObj["data"]["personInfoData"][
                "r_person_remark"]  # 区审核说明

            detailObj["data"]["personInfoData"]["street_person"] = detailObj["data"]["personInfoData"][
                "r_street_person"]  # 街道审核人
            detailObj["data"]["personInfoData"]["street_result"] = detailObj["data"]["personInfoData"][
                "r_street_result"]  # 街道审核结果
            detailObj["data"]["personInfoData"]["street_remark"] = detailObj["data"]["personInfoData"][
                "r_street_remark"]  # 街道审核说明

            # ID_list 同企业列表
            IDList = DBSessionQuery(apply_num=self.apply_num, final_list=person_info.r_final_list).getIDList()
            temp_list = [ID.r_ID for ID in IDList]
            detailObj["data"]["ID_list"] = temp_list

            # companyInfoData 企业信息
            company_info = DBSessionQuery(apply_num=self.apply_num).getCompanyInfo()
            if company_info:
                company_info_filed_list = [
                    "e_apply_num", "e_declaration_period", "e_declaration_date", "e_quarter_add", "e_socialcredit_code",
                    "e_company_name", "e_register_location", "e_establishment_date", "e_recruits_num",
                    "e_recruits_price", "e_online_processing", "e_company_social_security", "e_company_type",
                    "e_legal_person", "e_ID", "e_manager", "e_manager_phone", "e_company_worktel", "e_bank",
                    "e_bank_company", "e_bank_num", "e_success_count", "e_success_price", "e_failure_count",
                    "e_cum_count", "e_eco_price_count", "e_cum_price", "e_eco_price", "e_remarks", "e_price_type",
                    "e_first_social_count", "e_second_social_count", "e_is_xwCompany", "e_robot_result", "e_detail",
                    "e_person_result", "e_instructions", "e_identify_person", "e_get_person_state", "e_addr",
                    "e_street_name", "e_search_name", "e_search_established_time", "e_street_result", "e_street_person",
                    "e_street_remark",
                ]
                detailObj["data"]["companyInfoData"] = DBSessionAction().getObjectInfoData(company_info,
                                                                                           company_info_filed_list)
                # 标准化输出审核结果：
                detailObj["data"]["companyInfoData"]["auditor"] = detailObj["data"]["companyInfoData"][
                    "e_identify_person"]  # 区审核人
                detailObj["data"]["companyInfoData"]["artificial_audit"] = detailObj["data"]["companyInfoData"][
                    "e_person_result"]  # 区审核结果
                detailObj["data"]["companyInfoData"]["region_remark"] = detailObj["data"]["companyInfoData"][
                    "e_instructions"]  # 区审核说明

                detailObj["data"]["companyInfoData"]["street_person"] = detailObj["data"]["companyInfoData"][
                    "e_street_person"]  # 街道审核人
                detailObj["data"]["companyInfoData"]["street_result"] = detailObj["data"]["companyInfoData"][
                    "e_street_result"]  # 街道审核结果
                detailObj["data"]["companyInfoData"]["street_remark"] = detailObj["data"]["companyInfoData"][
                    "e_street_remark"]  # 街道审核说明

            # allowanceInfoData  享受补贴
            allowance_info = DBSessionQuery(card_ID=self.card_ID).getAllowanceInfo()
            allowance_info_filed_list = [
                "id", "a_apply_date", "a_apply_num", "a_name", "a_ID", "a_sex", "a_age", "a_isCity", "a_contract_date",
                "a_company_name", "a_register_num", "a_setUp_date", "a_belong", "a_audit", "a_audit_state",
                "a_approval_date", "a_isDelete",
            ]
            detailObj["data"]["allowanceInfoData"] = DBSessionAction().getObjectListData(allowance_info,
                                                                                         allowance_info_filed_list)
            # recordInfoData 就业登记
            record_info = DBSessionQuery(card_ID=self.card_ID).getRecordInfo()
            record_info_filed_list = ["id", "r_accept_batch", "r_company_name", "r_ID", "r_name", "r_sex", "r_birth",
                                      "r_degree", "r_population", "r_location", "r_register_type",
                                      "r_contract_start_date", "r_contract_end_date", "r_relieve_date",
                                      "r_register_date", "r_isapply", "r_date_source", ]
            detailObj["data"]["recordInfoData"] = DBSessionAction().getObjectListData(record_info,
                                                                                      record_info_filed_list)  # 转字典
            # socialPayInfoData 社保缴纳
            social_pay = DBSessionQuery(card_ID=self.card_ID).getSocialInfo()
            social_pay_filed_list = ["id", "s_ID", "s_pay_date", "s_old_base", "s_medical_base", "s_old_insur",
                                     "s_unemploy_insur", "s_injury_insur", "s_medical_insur", "s_c_old_insur",
                                     "s_c_unemploy_insur", "s_c_injury_insur", "s_c_medical_insur", "s_c_disease_insur",
                                     "s_c_birth_insur", "s_social_num", "s_social_c_num", "s_social_c_name",
                                     "s_social_credit_num", "s_medical_num", "s_medical_c_num", "s_medical_c_name",
                                     "s_medical_credit_num", ]

            detailObj["data"]["socialPayInfoData"] = DBSessionAction().getObjectListData(social_pay,
                                                                                         social_pay_filed_list)  # 转字典
            # xwCompanyInfoData 小微企业信息
            xw_company = DBSessionQuery(
                credit_num=detailObj["data"]["companyInfoData"]["e_socialcredit_code"]).getXwCompanyInfo()
            xw_company_filed_list = [
                "id", "main_num", "social_num", "register_num", "company_name", "main_type", "setup_date",
                "register_fund", "register_location_num", "register_location", "belong_type", "work_num", "work_name",
                "xw_type", "xw_type_name", "join_datetime", "exit_datetime", "exit_reason", "exit_reasons", "xw_state",
                "xw_state_name", "total_unit", "total_unit_date",
            ]
            detailObj["data"]["xwCompanyInfoData"] = DBSessionAction().getObjectListData(xw_company,
                                                                                         xw_company_filed_list)  # 转字典
            # businessInfoData 商事登记信息
            business_info = DBSessionQuery(card_ID=self.card_ID).getBuinessInfo()
            business_info_filed_list = [
                "id", "b_register_num", "b_credit_num", "b_company", "b_charge_name", "b_ID", "b_main_type",
                "b_pro_type", "b_date", "b_state", "b_relieve_date",
            ]
            detailObj["data"]["businessInfoData"] = DBSessionAction().getObjectListData(business_info,
                                                                                        business_info_filed_list)  # 转字典

            res.update(data=detailObj)
            return res.data
        except Exception as e:
            logging.error("getPersonDetailInfo接口异常:" + str(e))
            res.update(code=-1, msg="接口异常")
            return res.data

    # 6.提交人员审核结果请求
    def approvedPerson(self):
        res = ResMsg()

        # 检查审批内容
        if not self.apply_num or not self.card_ID or not self.roleName:
            res.update(code=-1, msg="传入参数有误，请核查!")
            return res.data

        # 检验账号权限等级
        approval_type = getAccountAuthority(self.roleName)  # 判断账号权限 0街道 1区级
        if approval_type not in [0, 1]:
            res.update(code=-1, msg="账号权限有误，请联系管理员！")
            return res.data

        # 审核参数
        approval_result = self.content.get("approval_result", None)
        approval_person = self.content.get("approval_person", None)
        approval_comment = self.content.get("approval_comment", None)
        if approval_result is None or not approval_person:
            res.update(code=-1, msg="传入审核参数有误，请核查信息")
            return res.data
        if int(approval_result) == 0 and not approval_comment:
            res.update(code=-1, msg="审核不通过必须添加审核说明！")
            return res.data

        # 获取公司信息
        company_info = DBSessionQuery(apply_num=self.apply_num).getCompanyInfo()
        # 根据身份证号，申领编号获取个人
        person_info = DBSessionQuery(card_ID=self.card_ID, apply_num=self.apply_num).getPersonInfo()

        if not person_info or not company_info:
            res.update(code=-1, msg="审核记录不存在，请检查输入参数是否正确！")
            return res.data

        # 权限判定
        if approval_type == 0:
            have_region_company_success_back = DBSessionQuery(apply_num=self.apply_num, br_state="成功",
                                                              br_type=1).getCompanyBackStateInfo()
            have_region_company_await_back = DBSessionQuery(apply_num=self.apply_num, br_state="等待",
                                                            br_type=1).getCompanyBackStateInfo()
            if have_region_company_success_back or have_region_company_await_back:
                res.update(code=-1, msg="区已审核，你无法再审核该人！")
                return res.data

        # 校验是否已有审核记录
        # todo:如果有【企业】审核回填成功
        have_success_company_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="成功",
                                                        br_type=approval_type).getCompanyBackStateInfo()
        if have_success_company_back_info:
            res.update(code=-1, msg="该企业已成功回填至PJ5系统，请回退后再进行审核!")
            return res.data

        # todo:如果已有【企业】审核等待
        # 审核结果对应列表位置
        if int(approval_result) == 0:  # 失败
            final_list = 2  # 失败列表
        elif int(approval_result) == 1:  # 成功
            final_list = 1  # 成功列表
        else:
            final_list = 0  # 预审列表
        have_await_company_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="等待",
                                                      br_type=approval_type).getCompanyBackStateInfo()
        if have_await_company_back_info:
            # 状态1：企业等待，人员等待==》修改
            have_await_person_back_info = DBSessionQuery(apply_num=self.apply_num, card_ID=self.card_ID, br_state="等待",
                                                         br_type=approval_type).getPersonBackStateInfo()
            if have_await_person_back_info:
                # 修改人员审核信息
                update_person_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=self.card_ID,
                                                             approval_type=approval_type,
                                                             approval_result=approval_result,
                                                             approval_person=approval_person,
                                                             approval_comment=approval_comment, final_list=final_list)
                if update_person_info_result is False:
                    res.update(code=-1, msg="修改人员审核信息失败，请尝试重新提交！")
                    return res.data
                res.update(code=200, msg="成功修改{}审核结果".format("街道" if approval_type == 0 else "区级"))
                return res.data

            # 状态2：企业等待，人员回填成功==》新增记录
            have_success_person_back_info = DBSessionQuery(apply_num=self.apply_num, card_ID=self.card_ID,
                                                           br_state="成功",
                                                           br_type=approval_type).getPersonBackStateInfo()
            if have_success_person_back_info:
                # 修改人员审核信息
                update_person_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=self.card_ID,
                                                             approval_type=approval_type,
                                                             approval_result=approval_result,
                                                             approval_person=approval_person,
                                                             approval_comment=approval_comment, final_list=final_list)
                if update_person_info_result is False:
                    res.update(code=-1, msg="修改人员审核信息失败，请尝试重新提交！")
                    return res.data
                # 添加人员回填信息
                insert_person_back_info_result = insertPersonBackInfo(approval_type=approval_type,
                                                                      approval_result=approval_result,
                                                                      approval_person=approval_person,
                                                                      br_cid=have_await_company_back_info.id,
                                                                      company_name=person_info.r_company_name,
                                                                      r_name=person_info.r_name,
                                                                      apply_num=self.apply_num, card_ID=self.card_ID,
                                                                      street_name=company_info.e_street_name)
                if insert_person_back_info_result is False:
                    res.update(code=-1, msg="添加人员回填信息失败，请尝试重新提交！")
                    return res.data
                res.update(code=200, msg="成功提交{}审核结果".format("街道" if approval_type == 0 else "区级"))
                return res.data

            # 状态3：企业等待，失败/无人员信息==》新增
            # 修改人员审核信息
            update_person_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=self.card_ID,
                                                         approval_type=approval_type,
                                                         approval_result=approval_result,
                                                         approval_person=approval_person,
                                                         approval_comment=approval_comment, final_list=final_list)
            if update_person_info_result is False:
                res.update(code=-1, msg="修改人员审核信息失败，请尝试重新提交！")
                return res.data
            # 添加人员回填信息
            insert_person_back_info_result = insertPersonBackInfo(approval_type=approval_type,
                                                                  approval_result=approval_result,
                                                                  approval_person=approval_person,
                                                                  br_cid=have_await_company_back_info.id,
                                                                  company_name=person_info.r_company_name,
                                                                  r_name=person_info.r_name,
                                                                  apply_num=self.apply_num, card_ID=self.card_ID,
                                                                  street_name=company_info.e_street_name)
            if insert_person_back_info_result is False:
                res.update(code=-1, msg="添加人员回填信息失败，请尝试重新提交！")
                return res.data
            res.update(code=200, msg="成功提交{}审核结果".format("街道" if approval_type == 0 else "区级"))
            return res.data

        # todo: 无企业审核/审核【失败】
        # 新增企业回填记录（br_fill_back：无操作）
        insert_company_back_info_result = insertCompanyBackInfo(approval_type=approval_type,
                                                                approval_person=approval_person,
                                                                apply_num=self.apply_num,
                                                                company_name=person_info.r_company_name,
                                                                street_name=company_info.e_street_name,
                                                                br_fill_back=0, approval_result=None)
        if insert_company_back_info_result is False:
            res.update(code=-1, msg="添加企业回填记录失败，请尝试重新提交!")
            return res.data
        # 再修改人员审核结果
        update_person_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=self.card_ID,
                                                     approval_type=approval_type,
                                                     approval_result=approval_result, approval_person=approval_person,
                                                     approval_comment=approval_comment, final_list=final_list)
        if update_person_info_result is False:
            res.update(code=-1, msg="修改人员审核信息失败，请尝试重新提交！")
            return res.data
        # 添加人员回填结果
        # 查询新添加的企业回填记录的id
        new_have_await_company_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="等待",
                                                          br_type=approval_type).getCompanyBackStateInfo()
        insert_person_back_info_result = insertPersonBackInfo(approval_type=approval_type,
                                                              approval_result=approval_result,
                                                              approval_person=approval_person,
                                                              br_cid=new_have_await_company_back_info.id,
                                                              company_name=person_info.r_company_name,
                                                              r_name=person_info.r_name,
                                                              apply_num=self.apply_num, card_ID=self.card_ID,
                                                              street_name=company_info.e_street_name)
        if insert_person_back_info_result is False:
            res.update(code=-1, msg="添加人员回填信息失败，请尝试重新提交！")
            return res.data
        res.update(code=200, msg="成功提交{}审核结果".format("街道" if approval_type == 0 else "区级"))
        return res.data

        #  后续添加

        # # todo:计算成功/失败人数and金额
        # # 计算成功人数
        # '''计算该公司成功人数'''
        # success_people = db.session.query(CyPersonInfo).filter(CyPersonInfo.r_apply_num == self.apply_num,
        #                                                        CyPersonInfo.r_final_list == 1)
        # company_info.e_success_count = success_people.count()
        # # '''计算成功金额'''
        # # success_fund = 0
        # # for p in success_people:
        # #     success_fund += p.p_society_total
        # # company_info.c_success_fund = success_fund
        # '''计算该公司失败人数'''
        # fail_people = db.session.query(PersonInfo).filter(PersonInfo.apply_num == self.apply_num,
        #                                                   PersonInfo.r_final_list == 0)
        # company_info.e_failure_count = fail_people.count()
        # # '''计算失败金额'''
        # # fail_fund = 0
        # # for p in fail_people:
        # #     fail_fund += p.p_society_total
        # # company_info.c_fail_fund = fail_fund
        # # 计算成功金额
        # # 计算失败人数
        # # 计算失败金额
        # db.session.commit()
        # res.update(code=200, msg='提交成功')
        # return res.data

    # 7.提交公司审核结果请求
    def approvedCompany(self):

        res = ResMsg()
        # 检查审批内容
        if not self.apply_num or not self.roleName:
            res.update(code=-1, msg="请求参数有误，请核查")
            return res.data
        # 获取审批内容
        approval_result = self.content.get("approval_result", None)  # 审批结果：1成功，0失败
        approval_person = self.content.get("approval_person", None)  # 审批人
        approval_comment = self.content.get("approval_comment", None)  # 审批详情
        approval_type = getAccountAuthority(self.roleName)  # 获取当前审核等级 街道0，区级1
        # 校验
        if approval_type != 0 and approval_type != 1:
            res.update(code=-1, msg="账号权限有误，请使用街道或区级账号进行审核")
            return res.data
        if approval_result != 0 and approval_result != 1:
            res.update(code=-1, msg="审核有误")
            return res.data
        if approval_person is None:
            res.update(code=-1, msg="审核参数有误，请核查！")
            return res.data
        if approval_result == 0 and not approval_comment:
            res.update(code=-1, msg="审核不通过必须添加审核说明！")
            return res.data
        # 获取企业基础信息
        company_info = DBSessionQuery(apply_num=self.apply_num).getCompanyInfo()
        # 街道/区审核权限判定
        if approval_type == 0:
            if company_info.e_identify_person:
                res.update(code=-1, msg="区已审核该企业，你无法再审核！")
                return res.data

        # todo:1.如果企业审核通过,并且有人员未审核
        if int(approval_result) == 1:
            # 如果有人员没有被审核，不允许审核通过企业
            have_not_approval = DBSessionQuery(apply_num=self.apply_num).getCompanyPersonInfo().filter(
                CyPersonInfo.r_final_list == "0").count()  # 统计所在列表为0（预审列表）的人数
            if have_not_approval != 0:
                res.update(code=-1, msg="1:还有人员在预审列表，请将所有人员审核，再提交企业审核结果")
                return res.data

        # todo:2.如果有已回填成功，需先回退
        have_success_company_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="成功",
                                                        br_type=approval_type).getCompanyBackStateInfo()
        if have_success_company_back_info:
            res.update(code=-1, msg="2:企业已回填至PJ5，请先回退再进行审核！")
            return res.data

        # todo:3.如果已有回填等待，校验所有人是否添加到回填；修改回填记录/company记录
        final_list = [2, 1, 0]
        have_await_company_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="等待",
                                                      br_type=approval_type).getCompanyBackStateInfo()
        if have_await_company_back_info:
            # 搜索企业下所有人员
            person_info_For_company = DBSessionQuery(apply_num=self.apply_num).getCompanyPersonInfo().all()
            if approval_type == 0:  # 街道审核
                for i in person_info_For_company:
                    if not i.r_street_person:  # 没有回填记录，按人员所在列表添加审核结果
                        # 先新增
                        person_insert_back_result = insertPersonBackInfo(approval_type=approval_type,
                                                                         approval_result=final_list[i.r_final_list],
                                                                         approval_person=approval_person,
                                                                         br_cid=have_await_company_back_info.id,
                                                                         company_name=i.r_company_name,
                                                                         r_name=i.r_name, apply_num=self.apply_num,
                                                                         card_ID=i.r_ID,
                                                                         street_name=company_info.e_street_name,
                                                                         )
                        # 再修改
                        person_update_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=i.r_ID,
                                                                     approval_type=approval_type,
                                                                     approval_result=final_list[i.r_final_list],
                                                                     approval_person=approval_person,
                                                                     approval_comment=i.r_street_remark,
                                                                     final_list=i.r_final_list)
                        if not person_insert_back_result and not person_update_info_result:
                            res.update(code=-1, msg="3:提交人员审核出现错误，请重新提交或联系管理员！")
                            return res.data
            elif approval_type == 1:  # 区级审核
                for i in person_info_For_company:
                    if not i.r_identify_person:  # 没有回填记录，按人员所在列表添加审核结果
                        # 先新增
                        person_insert_back_result = insertPersonBackInfo(approval_type=approval_type,
                                                                         approval_result=final_list[i.r_final_list],
                                                                         approval_person=approval_person,
                                                                         br_cid=have_await_company_back_info.id,
                                                                         company_name=i.r_company_name,
                                                                         r_name=i.r_name, apply_num=self.apply_num,
                                                                         card_ID=i.r_ID,
                                                                         street_name=company_info.e_street_name,
                                                                         )
                        # 再修改
                        person_update_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=i.r_ID,
                                                                     approval_type=approval_type,
                                                                     approval_result=final_list[i.r_final_list],
                                                                     approval_person=approval_person,
                                                                     approval_comment=i.r_street_remark,
                                                                     final_list=i.r_final_list)
                        if not person_insert_back_result and not person_update_info_result:
                            res.update(code=-1, msg="3:提交人员审核出现错误，请重新提交或联系管理员！")
                            return res.data
            # 修改企业记录
            # 修改企业表&回填表
            if approval_type == 0:  # 街道审核
                db.session.query(CyCompanyInfo).filter(CyCompanyInfo.e_apply_num == self.apply_num).update(
                    {"e_street_result": approval_result, "e_street_person": approval_person,
                     "e_street_remark": approval_comment})
                db.session.query(CyBackRecord_info).filter(CyBackRecord_info.br_apply_num == self.apply_num,
                                                           CyBackRecord_info.br_cid == None,
                                                           CyBackRecord_info.br_state == "等待",
                                                           CyBackRecord_info.br_type == 0,
                                                           CyBackRecord_info.br_fill_back != 2).update(
                    {"br_fill_back": 1, "br_identify_person": approval_person, "result": approval_result})
                db.session.commit()
            elif approval_type == 1:  # 区级审核
                db.session.query(CyCompanyInfo).filter(CyCompanyInfo.e_apply_num == self.apply_num).update(
                    {"e_person_result": approval_result, "e_identify_person": approval_person,
                     "e_instructions": approval_comment})
                db.session.query(CyBackRecord_info).filter(CyBackRecord_info.br_apply_num == self.apply_num,
                                                           CyBackRecord_info.br_cid == None,
                                                           CyBackRecord_info.br_state == "等待",
                                                           CyBackRecord_info.br_type == 1,
                                                           CyBackRecord_info.br_fill_back != 2).update(
                    {"br_fill_back": 1, "br_identify_person": approval_person, "result": approval_result})
                db.session.commit()
            res.update(code=200, msg="3:提交{}审核成功".format("街道" if approval_type == 0 else "区级"))
            return res.data

        # todo:4.如果没有企业回填记录/回填失败
        # 先添加企业回填、修改企业表
        if approval_type == 0:  # 街道回填
            db.session.query(CyCompanyInfo).filter(CyCompanyInfo.e_apply_num == self.apply_num).update(
                {"e_street_result": approval_result, "e_street_person": approval_person,
                 "e_street_remark": approval_comment})
            new_company_back_info = CyBackRecord_info()
            new_company_back_info.br_apply_num = self.apply_num
            new_company_back_info.br_company = company_info.e_company_name
            new_company_back_info.br_person_ID = ""
            new_company_back_info.br_person_name = ""
            new_company_back_info.br_fill_back = 1  # 回填
            new_company_back_info.br_detail = ""
            new_company_back_info.br_state = "等待"
            new_company_back_info.br_identify_person = approval_person
            new_company_back_info.br_cid = None
            new_company_back_info.br_street_name = company_info.e_street_name
            new_company_back_info.br_type = 0
            new_company_back_info.result = approval_result
            db.session.add(new_company_back_info)
            db.session.commit()
            # 查询刚提交的企业回填信息
            company_back_info = DBSessionQuery(apply_num=self.apply_num, br_type=0,
                                               br_state="等待").getCompanyBackStateInfo()
            # 查询该企业的所有人员
            person_info_For_company = DBSessionQuery(apply_num=self.apply_num).getCompanyPersonInfo().all()
            for i in person_info_For_company:
                if not i.r_street_person:  # 没有回填记录
                    # 先新增
                    person_insert_back_result = insertPersonBackInfo(approval_type=approval_type,
                                                                     approval_result=final_list[i.r_final_list],
                                                                     br_cid=company_back_info.id,
                                                                     company_name=company_info.e_company_name,
                                                                     r_name=i.r_name, apply_num=self.apply_num,
                                                                     card_ID=i.r_ID,
                                                                     street_name=company_info.e_street_name,
                                                                     approval_person=approval_person)
                    # 再修改
                    person_update_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=i.r_ID,
                                                                 approval_type=approval_type,
                                                                 approval_result=final_list[i.r_final_list],
                                                                 approval_person=approval_person,
                                                                 approval_comment=i.r_street_remark,
                                                                 final_list=i.r_final_list)
                    if not person_insert_back_result and not person_update_info_result:
                        res.update(code=-1, msg="4:提交人员审核出现错误，请重新提交或联系管理员！")
                        return res.data
            res.update(code=200, msg="4:提交街道审核成功!")
            return res.data
        elif approval_type == 1:  # 区级审核
            # 修改企业表
            db.session.query(CyCompanyInfo).filter(CyCompanyInfo.e_apply_num == self.apply_num).update(
                {"e_person_result": approval_result, "e_identify_person": approval_person,
                 "e_instructions": approval_comment})
            # 添加企业回填记录
            new_company_back_info = CyBackRecord_info()
            new_company_back_info.br_apply_num = self.apply_num
            new_company_back_info.br_company = company_info.e_company_name
            new_company_back_info.br_person_ID = ""
            new_company_back_info.br_person_name = ""
            new_company_back_info.br_fill_back = 1  # 回填
            new_company_back_info.br_detail = ""
            new_company_back_info.br_state = "等待"
            new_company_back_info.br_identify_person = approval_person
            new_company_back_info.br_cid = None
            new_company_back_info.br_street_name = company_info.e_street_name
            new_company_back_info.br_type = 1
            new_company_back_info.result = approval_result
            db.session.add(new_company_back_info)
            db.session.commit()
            # 查询刚提交的企业回填信息
            company_back_info = DBSessionQuery(apply_num=self.apply_num, br_type=1,
                                               br_state="等待").getCompanyBackStateInfo()
            # 查询该企业的所有人员
            person_info_For_company = DBSessionQuery(apply_num=self.apply_num).getCompanyPersonInfo().all()
            for i in person_info_For_company:
                if not i.r_identify_person:  # 没有回填记录
                    # 先新增
                    person_insert_back_result = insertPersonBackInfo(approval_type=approval_type,
                                                                     approval_result=final_list[i.r_final_list],
                                                                     br_cid=company_back_info.id,
                                                                     company_name=company_info.e_company_name,
                                                                     r_name=i.r_name, apply_num=self.apply_num,
                                                                     card_ID=i.r_ID,
                                                                     street_name=company_info.e_street_name,
                                                                     approval_person=approval_person)
                    # 再修改
                    person_update_info_result = updatePersonInfo(apply_num=self.apply_num, card_ID=i.r_ID,
                                                                 approval_type=approval_type,
                                                                 approval_result=final_list[i.r_final_list],
                                                                 approval_person=approval_person,
                                                                 approval_comment=i.r_street_remark,
                                                                 final_list=i.r_final_list)
                    if not person_insert_back_result and not person_update_info_result:
                        res.update(code=-1, msg="4:提交人员审核出现错误，请重新提交或联系管理员！")
                        return res.data
            res.update(code=200, msg="4:提交区级审核成功")
            return res.data

    # 8.企业回退
    def companyRollback(self):
        res = ResMsg()
        # 检验输入参数
        if not self.apply_num or not self.roleName or not self.auditor:
            res.update(code=-1, msg="输入参数有误，请核查")
            return res.data
        # 获取当前账号权限
        approval_type = getAccountAuthority(self.roleName)
        if approval_type != 0 and approval_type != 1:
            res.update(code=-1, msg="账号权限不正确，请使用街道账号/区账号！")
            return res.data
        # 获取企业基础信息
        company_info = DBSessionQuery(apply_num=self.apply_num).getCompanyInfo()
        if approval_type == 0:  # 街道审核
            if company_info.e_identify_person:
                res.update(code=-1, msg="区已审核，你无法回退操作，请联系区负责人")
                return res.data

        # todo:1.企业在等待回填
        have_company_await_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="等待",
                                                      br_type=approval_type).getCompanyBackStateInfo()
        if have_company_await_back_info:
            res.update(code=-1, msg="企业还未回填至PJ5，你无需回退，请继续审核！")
            return res.data

        # todo:2.企业回填成功
        have_company_success_back_info = DBSessionQuery(apply_num=self.apply_num, br_state="成功",
                                                        br_type=approval_type).getCompanyBackStateInfo()
        if have_company_success_back_info:
            # 修改企业表/人员表
            if approval_type == 0:  # 街道审核
                # 企业
                db.session.query(CyCompanyInfo).filter(CyCompanyInfo.e_apply_num == self.apply_num).update(
                    {"e_street_result": None, "e_street_person": None, "e_street_remark": None})
                # 人员
                db.session.query(CyPersonInfo).filter(CyPersonInfo.r_apply_num == self.apply_num).update(
                    {"r_street_result": None, "r_street_person": None, "r_street_remark": None})
            elif approval_type == 1:  # 区审核
                # 企业
                db.session.query(CyCompanyInfo).filter(CyCompanyInfo.e_apply_num == self.apply_num).update(
                    {"e_person_result": None, "e_identify_person": None, "e_instructions": None})
                # 人员
                db.session.query(CyPersonInfo).filter(CyPersonInfo.r_apply_num == self.apply_num).update(
                    {"r_person_result": None, "r_identify_person": None, "r_person_remark": None})
            # 修改回填表
            # 修改企业
            db.session.query(CyBackRecord_info).filter(CyBackRecord_info.br_apply_num == self.apply_num,
                                                       CyBackRecord_info.br_type == approval_type,
                                                       CyBackRecord_info.br_state == "成功",
                                                       CyBackRecord_info.br_fill_back == 1).update(
                {"br_fill_back": 2, "br_state": "等待", "br_detail": self.auditor + ":审核异常立即回退"})
            # 修改个人
            db.session.query(CyBackRecord_info).filter(CyBackRecord_info.br_apply_num == self.apply_num,
                                                       CyBackRecord_info.br_cid == have_company_success_back_info.id).update(
                {"br_fill_back": 2, "br_state": "等待", "br_detail": self.auditor + ":审核异常立即回退"})
            db.session.commit()
            res.update(code=200, msg="回退成功，请继续审核！")
            return res.data

        # todo:3.企业未审核或者审核失败
        res.update(code=200, msg="企业没有审核记录或回填失败，你无需回退，请继续审核！")
        return res.data

    # 10.企业/个人回填回退记录表
    def BackRecord(self):
        res = ResMsg()
        page_num = self.page.get("pageNum", 1)
        page_size = self.page.get("pageSize", 40)
        # 定义翻页参数
        page = {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": 0
        }
        # 筛选条件
        apply_num = self.searchKey.get("apply_num", None)  # 申领编号
        company_name = self.searchKey.get("company_name", None)  # 企业名称
        apply_season = self.searchKey.get("apply_season", None)  # 申领年季
        state = self.searchKey.get("state", None)  # 回填状态
        auditor = self.searchKey.get("auditor", None)  # 审核人
        street_belong = self.searchKey.get("street_belong", None)  # 所属街道

        # card_ID = self.searchKey.get("card_ID", None)  # 身份证号
        # student_name = self.searchKey.get("person_name", None)  # 学生名称
        # 查询基础信息
        base_query = DBSessionQuery(apply_season=apply_season).getCompanyBackInfoList()

        # 权限校验
        approval_type = getAccountAuthority(self.roleName)
        if approval_type != 0 and approval_type != 1:
            res.update(code=-1, msg="账号权限错误，请使用街道账号或区账号登录")
            return res.data
        if approval_type == 0:  # 街道审核
            base_query = base_query.filter(CyBackRecord_info.br_street_name == self.roleName)
        else:
            if street_belong:
                base_query = base_query.filter(CyBackRecord_info.br_street_name.like("%" + street_belong + "%"))
        # 查询条件筛选
        # 审核人
        if auditor:
            base_query = base_query.filter(CyBackRecord_info.br_identify_person == auditor)

        # 回填状态
        if state:
            base_query = base_query.filter(CyBackRecord_info.br_state == state)

        # 企业名
        if company_name:
            base_query = base_query.filter(CyBackRecord_info.br_company.like("%" + company_name + "%"))

        # 申领编号
        if apply_num:
            base_query = base_query.filter(CyBackRecord_info.br_apply_num == apply_num)

        total = base_query.count()  # 统计总数
        results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()
        filed_list = [
            "id", "br_apply_num", "br_company", "br_person_ID", "br_person_name", "br_fill_back", "br_detail",
            "br_fillBackLink", "br_state", "br_identify_person", "br_cid", "br_street_name", "br_type", "result",
        ]
        dictList = DBSessionAction().getObjectListData(results, filed_list)
        res.update(data={
            "page": {
                "pageNum": page["pageNum"],
                "pageSize": page["pageSize"],
                "total": total
            },
            "ItemCode": "cyddjybt",
            "ItemName": "cyddjybt",
            "ItemType": 2,
            "data": dictList
        })
        return res.data

    # 11.展示企业下cid的所有用户
    def personBackInfo(self):
        res = ResMsg()
        # 校验输入参数
        if not self.apply_num or not self.cid:
            res.update(code=-1, msg="传入参数有误，请检查！")
            return res.data
        # 获取信息
        base_query = DBSessionQuery(apply_num=self.apply_num, cid=self.cid).getPersonCidBackInfoList()

        # 转字典
        filed_list = [
            "id", "br_apply_num", "br_company", "br_person_ID", "br_person_name", "br_fill_back", "br_detail",
            "br_fillBackLink", "br_state", "br_identify_person", "br_cid", "br_street_name", "br_type", "result",
        ]
        dictList = DBSessionAction().getObjectListData(base_query, filed_list)
        res.update(code=200, data=dictList)
        return res.data

    # 12.自动审核续期人员
    # 暂不考虑


class DBSessionQuery(object):
    """
    数据库查询操作
    """

    def __init__(self, **kwargs):
        self.card_ID = kwargs.get('card_ID', None)  # 证件号码
        self.apply_num = kwargs.get('apply_num', None)  # 申领编号

        self.apply_season = kwargs.get("apply_season", None)  # 申领年季
        self.br_type = kwargs.get("br_type", None)  # 审核级别 0街道 1区级
        self.final_list = kwargs.get("final_list", None)  # 人员所在列表
        self.credit_num = kwargs.get("credit_num", None)  # 统一信用代码
        self.br_state = kwargs.get("br_state", None)  # 回填状态
        self.cid = kwargs.get("cid", None)  # 企业回填序号

    # 1.获取企业列表
    def getCompanyList(self):
        data = db.session.query(
            CyCompanyInfo.id,  # id 自增
            CyCompanyInfo.e_apply_num,  # 申领编号
            CyCompanyInfo.e_declaration_period,  # 申报期
            CyCompanyInfo.e_declaration_date,  # 申报日期
            CyCompanyInfo.e_quarter_add,  # 是否本季度新增
            CyCompanyInfo.e_socialcredit_code,  # 统一信用代码
            CyCompanyInfo.e_company_name,  # 单位名称
            CyCompanyInfo.e_register_location,  # 单位注册地
            CyCompanyInfo.e_establishment_date,  # 创业成立日期
            CyCompanyInfo.e_recruits_num,  # 本期招用人数
            CyCompanyInfo.e_company_type,  # 单位类型
            CyCompanyInfo.e_robot_result,  # 机器人预审结果
            CyCompanyInfo.e_detail,  # 预审详情
            CyCompanyInfo.e_person_result,  # 人员审核结果
            CyCompanyInfo.e_identify_person,  # 审核人
            CyCompanyInfo.e_street_name,  # 所属街道
            CyCompanyInfo.e_street_result,  # 街道人员审核结果 1通过 0不通过
            CyCompanyInfo.e_street_person,  # 街道审核人
        ).filter(
            CyCompanyInfo.e_apply_num.like("%" + self.apply_season + "%")
        )
        return data

    # 3&6.获取企业信息
    def getCompanyInfo(self):
        data = db.session.query(
            CyCompanyInfo.e_apply_num,  # 申领编号
            CyCompanyInfo.e_declaration_period,  # 申报期
            CyCompanyInfo.e_declaration_date,  # 申报日期
            CyCompanyInfo.e_quarter_add,  # 是否本季度新增
            CyCompanyInfo.e_socialcredit_code,  # 统一信用代码
            CyCompanyInfo.e_company_name,  # 单位名称
            CyCompanyInfo.e_register_location,  # 单位注册地
            CyCompanyInfo.e_establishment_date,  # 创业成立日期
            CyCompanyInfo.e_recruits_num,  # 本期招用人数
            CyCompanyInfo.e_recruits_price,  # 本期招用补贴金额
            CyCompanyInfo.e_online_processing,  # 是否网办
            CyCompanyInfo.e_company_social_security,  # 单位社保号
            CyCompanyInfo.e_company_type,  # 单位类型
            CyCompanyInfo.e_legal_person,  # 法定代表人
            CyCompanyInfo.e_ID,  # 证件号码
            CyCompanyInfo.e_manager,  # 经手人
            CyCompanyInfo.e_manager_phone,  # 经手人电话
            CyCompanyInfo.e_company_worktel,  # 单位办公电话
            CyCompanyInfo.e_bank,  # 开户银行
            CyCompanyInfo.e_bank_company,  # 开户名称
            CyCompanyInfo.e_bank_num,  # 银行账号
            CyCompanyInfo.e_success_count,  # 本期成功人数
            CyCompanyInfo.e_success_price,  # 本期成功补贴金额
            CyCompanyInfo.e_failure_count,  # 本期失败人数
            CyCompanyInfo.e_cum_count,  # 累计招用人数
            CyCompanyInfo.e_eco_price_count,  # 其中省资金招用人数
            CyCompanyInfo.e_cum_price,  # 累计招用补贴金额
            CyCompanyInfo.e_eco_price,  # 其中省资金招用补贴金额
            CyCompanyInfo.e_remarks,  # 备注
            CyCompanyInfo.e_price_type,  # 资金类别
            # 额外参数
            CyCompanyInfo.e_first_social_count,  # 企业第一个月参保人数
            CyCompanyInfo.e_second_social_count,  # 企业第二个月参保人数
            CyCompanyInfo.e_is_xwCompany,  # 是否小微企业
            CyCompanyInfo.e_robot_result,  # 机器人预审结果
            CyCompanyInfo.e_detail,  # 预审详情
            CyCompanyInfo.e_person_result,  # 区人员审核结果
            CyCompanyInfo.e_instructions,  # 区审核说明
            CyCompanyInfo.e_identify_person,  # 区审核人
            CyCompanyInfo.e_get_person_state,  # 抓取单位人员数据状态
            CyCompanyInfo.e_addr,  # 企业地址
            # 额外参数（海珠）
            CyCompanyInfo.e_street_name,  # 所属街道
            CyCompanyInfo.e_search_name,  # 信用中国查询名称
            CyCompanyInfo.e_search_established_time,  # 信用中国查询成立时间
            # todo:街道审核
            CyCompanyInfo.e_street_result,  # 街道人员审核结果 1通过 0不通过
            CyCompanyInfo.e_street_person,  # 街道审核人
            CyCompanyInfo.e_street_remark,  # 街道审核说明
        ).filter(
            CyCompanyInfo.e_apply_num == self.apply_num
        ).first()
        return data

    # 4. 获取不同类型人员列表
    def getPersonList(self):
        data = db.session.query(
            CyPersonInfo.id,  # id 自增
            CyPersonInfo.r_apply_num,  # 申领编号，关联企业
            CyPersonInfo.r_ID,  # 证件号码
            CyPersonInfo.r_name,  # 姓名
            CyPersonInfo.r_sex,  # 性别
            CyPersonInfo.r_age,  # 年龄
            CyPersonInfo.r_provinces,  # 是否省市
            CyPersonInfo.r_contract_date,  # 合同起止日期
            CyPersonInfo.r_local_type,  # 人员所在列表
            CyPersonInfo.r_instructions,  # 审核说明
        ).filter(CyPersonInfo.r_apply_num == self.apply_num,
                 CyPersonInfo.r_final_list == self.final_list
                 )
        return data

    # 5&6.获取人员详情信息
    def getPersonInfo(self):
        """根据申领编号和证件号码查询"""
        data = db.session.query(
            CyPersonInfo.id,  # id 自增
            CyPersonInfo.r_apply_num,  # 申领编号，关联企业
            CyPersonInfo.r_ID,  # 证件号码
            CyPersonInfo.r_name,  # 姓名
            CyPersonInfo.r_sex,  # 性别
            CyPersonInfo.r_age,  # 年龄
            CyPersonInfo.r_provinces,  # 是否省市
            CyPersonInfo.r_company_name,  # 单位名称
            CyPersonInfo.r_contract_date,  # 合同起止日期
            CyPersonInfo.r_local_type,  # 人员所在列表
            CyPersonInfo.r_ID_type,  # 证件类型
            CyPersonInfo.r_passnum,  # 通行证号码
            CyPersonInfo.r_social_num,  # 个人社保号
            CyPersonInfo.r_contract_start_date,  # 合同开始日期
            CyPersonInfo.r_contract_end_date,  # 合同结束日期
            CyPersonInfo.r_instructions,  # 审核说明
            CyPersonInfo.r_remarks,  # 备注
            CyPersonInfo.r_agent,  # 经办人
            CyPersonInfo.r_handling_date,  # 经办日期
            CyPersonInfo.r_handling_location,  # 经办机构
            # 额外参数
            CyPersonInfo.r_robot_result,  # 机器人预审结果
            CyPersonInfo.r_detail,  # 预审详情
            # todo：区审核
            CyPersonInfo.r_person_result,  # 区级人员审核结果
            CyPersonInfo.r_person_remark,  # 区级人员审核说明
            CyPersonInfo.r_identify_person,  # 区级审核人
            CyPersonInfo.r_person_detail,  # 人员详情信息是否齐全
            # 状态
            CyPersonInfo.r_social_state,  # 人员社保信息获取状态(默认为False)
            CyPersonInfo.r_final_list,  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)
            # 街道审核
            CyPersonInfo.r_street_result,  # 街道人员审核结果
            CyPersonInfo.r_street_person,  # 街道审核人
            CyPersonInfo.r_street_remark,  # 街道审核说明
        ).filter(
            CyPersonInfo.r_apply_num == self.apply_num,
            CyPersonInfo.r_ID == self.card_ID
        ).first()
        return data

    # 5.获取该企业下同一列表里的位置
    def getIDList(self):
        data = db.session.query(
            CyPersonInfo.r_ID
        ).filter(
            CyPersonInfo.r_apply_num == self.apply_num,
            CyPersonInfo.r_final_list == self.final_list
        ).all()
        return data

    # 5.获取个人补贴享受情况
    def getAllowanceInfo(self):
        data = db.session.query(
            CyAllowanceInfo.id,  #
            CyAllowanceInfo.a_apply_date,  # 申报期
            CyAllowanceInfo.a_apply_num,  # 申领编号
            CyAllowanceInfo.a_name,  # 法定代表人
            CyAllowanceInfo.a_ID,  # 法人证件号码  关联人员信息的证件号码
            CyAllowanceInfo.a_sex,  # 性别
            CyAllowanceInfo.a_age,  # 年龄
            CyAllowanceInfo.a_isCity,  # 是否本市
            CyAllowanceInfo.a_contract_date,  # 合同起止日期
            CyAllowanceInfo.a_company_name,  # 企业名称
            CyAllowanceInfo.a_register_num,  # 统一社会信用代码
            CyAllowanceInfo.a_setUp_date,  # 创业成立时间
            CyAllowanceInfo.a_belong,  # 所属区街
            CyAllowanceInfo.a_audit,  # 操作人
            CyAllowanceInfo.a_audit_state,  # 审核状态
            CyAllowanceInfo.a_approval_date,  # 核准日期
            CyAllowanceInfo.a_isDelete,  # 是否有删除标识
        ).filter(
            CyAllowanceInfo.a_ID == self.card_ID
        ).all()
        return data

    # 5.获取就业登记信息
    def getRecordInfo(self):
        data = db.session.query(
            RecordInfo.id,  #
            RecordInfo.r_accept_batch,  # 受理批次
            RecordInfo.r_company_name,  # 单位名称
            RecordInfo.r_ID,  # 公民身份证号码关联人员信息的证件号码
            RecordInfo.r_name,  # 姓名
            RecordInfo.r_sex,  # 性别
            RecordInfo.r_birth,  # 出生日期
            RecordInfo.r_degree,  # 文化程度
            RecordInfo.r_population,  # 户口性质
            RecordInfo.r_location,  # 户口所在地
            RecordInfo.r_register_type,  # 登记类别
            RecordInfo.r_contract_start_date,  # 合同始期
            RecordInfo.r_contract_end_date,  # 合同终期
            RecordInfo.r_relieve_date,  # 解除合同日期
            RecordInfo.r_register_date,  # 登记日期
            RecordInfo.r_isapply,  # 是否已申领就业创业证
            RecordInfo.r_date_source,  # 数据来源
        ).filter(
            RecordInfo.r_ID == self.card_ID
        ).all()
        return data

    # 5.获取小微企业信息
    def getXwCompanyInfo(self):
        data = db.session.query(
            XwCompanyInfo.id,  #
            XwCompanyInfo.main_num,  # 主体身份代码
            XwCompanyInfo.social_num,  # 社会信用代码
            XwCompanyInfo.register_num,  # 注册号
            XwCompanyInfo.company_name,  # 企业名称
            XwCompanyInfo.main_type,  # 市场主体类型
            XwCompanyInfo.setup_date,  # 成立时间
            XwCompanyInfo.register_fund,  # 注册资本
            XwCompanyInfo.register_location_num,  # 登记机关
            XwCompanyInfo.register_location,  # 登记机关（中文名称）
            XwCompanyInfo.belong_type,  # 所属门类
            XwCompanyInfo.work_num,  # 行业代码
            XwCompanyInfo.work_name,  # 行业代码(中文名称)
            XwCompanyInfo.xw_type,  # 小微企业分类
            XwCompanyInfo.xw_type_name,  # 小微企业分类（中文名称）
            XwCompanyInfo.join_datetime,  # 加入时间
            XwCompanyInfo.exit_datetime,  # 退出时间
            XwCompanyInfo.exit_reason,  # 退出原因
            XwCompanyInfo.exit_reasons,  # 退出原因（中文名称）
            XwCompanyInfo.xw_state,  # 小微企业状态
            XwCompanyInfo.xw_state_name,  # 小微企业状态（中文名称）
            XwCompanyInfo.total_unit,  # 数据汇总单位
            XwCompanyInfo.total_unit_date,  # 数据汇总单位时间
        ).filter(
            XwCompanyInfo.social_num == self.credit_num
        ).all()
        return data

    # 5.查询商事登记信息
    def getBuinessInfo(self):
        data = db.session.query(
            BusinessInfo.id,  #
            BusinessInfo.b_register_num,  # 商事注册号
            BusinessInfo.b_credit_num,  # 统一社会信用代码
            BusinessInfo.b_company,  # 单位名称
            BusinessInfo.b_charge_name,  # 法定代表人
            BusinessInfo.b_ID,  # 法人证件号码  关联人员信息的证件号码
            BusinessInfo.b_main_type,  # 商事主体类型
            BusinessInfo.b_pro_type,  # 主营项目类别
            BusinessInfo.b_date,  # 成立时间
            BusinessInfo.b_state,  # 状态
            BusinessInfo.b_relieve_date,  # 状态
        ).filter(
            BusinessInfo.b_ID == self.card_ID
        ).all()
        return data

    # 5.获取社保缴纳信息
    def getSocialInfo(self):
        data = db.session.query(
            SocialPayInfo.id,  #
            SocialPayInfo.s_ID,  # 公民身份证号码 关联人员信息的证件号码
            SocialPayInfo.s_pay_date,  # 投保日期
            SocialPayInfo.s_old_base,  # 养老缴费基数
            SocialPayInfo.s_medical_base,  # 医疗缴费基数
            SocialPayInfo.s_old_insur,  # 个人养老保险
            SocialPayInfo.s_unemploy_insur,  # 个人失业保险
            SocialPayInfo.s_injury_insur,  # 个人工伤保险
            SocialPayInfo.s_medical_insur,  # 个人医疗保险
            SocialPayInfo.s_c_old_insur,  # 单位养老保险
            SocialPayInfo.s_c_unemploy_insur,  # 单位失业保险
            SocialPayInfo.s_c_injury_insur,  # 单位工伤保险
            SocialPayInfo.s_c_medical_insur,  # 单位医疗保险
            SocialPayInfo.s_c_disease_insur,  # 单位重大疾病保险
            SocialPayInfo.s_c_birth_insur,  # 单位生育保险
            SocialPayInfo.s_social_num,  # 个人社保号(社保)
            SocialPayInfo.s_social_c_num,  # 单位社保号（社保)
            SocialPayInfo.s_social_c_name,  # 单位名称(社保)
            SocialPayInfo.s_social_credit_num,  # 社会统一信用代码(社保)
            SocialPayInfo.s_medical_num,  # 个人社保号医保)
            SocialPayInfo.s_medical_c_num,  # 单位社保号医保)
            SocialPayInfo.s_medical_c_name,  # 单位名称(医保)
            SocialPayInfo.s_medical_credit_num,  # 社会统一信用代码(医保)
        ).filter(
            SocialPayInfo.s_ID == self.card_ID
        ).all()
        return data

    # 6.获取个人审核结果
    def getPersonBackStateInfo(self):
        data = db.session.query(
            CyBackRecord_info.id,  #
            CyBackRecord_info.br_apply_num,  # 申领编号
            CyBackRecord_info.br_company,  # 企业名称
            CyBackRecord_info.br_person_ID,  # 人员证件号码
            CyBackRecord_info.br_person_name,  # 人员名字
            CyBackRecord_info.br_fill_back,  # 操作名称0：无操作，1：回填，2：回退
            CyBackRecord_info.br_detail,  # 操作详情
            CyBackRecord_info.br_fillBackLink,  # 回退步骤 0为区审核，1为待报批
            CyBackRecord_info.br_state,  # 操作状态
            CyBackRecord_info.br_identify_person,  # 审核人名字
            CyBackRecord_info.br_cid,  # 关联id 用于定位个人
            CyBackRecord_info.br_street_name,  # 所属街道
            CyBackRecord_info.br_type,  # 审核等级 0街道  1区级
            CyBackRecord_info.result,  # 审核结果
        ).filter(CyBackRecord_info.br_apply_num == self.apply_num,
                 CyBackRecord_info.br_person_ID == self.card_ID,
                 CyBackRecord_info.br_state == self.br_state,
                 CyBackRecord_info.br_type == self.br_type,
                 CyBackRecord_info.br_fill_back != 2,
                 ).first()
        return data

    # 6&7&8.获取企业审核结果
    def getCompanyBackStateInfo(self):
        data = db.session.query(
            CyBackRecord_info.id,  #
            CyBackRecord_info.br_apply_num,  # 申领编号
            CyBackRecord_info.br_company,  # 企业名称
            CyBackRecord_info.br_person_ID,  # 人员证件号码
            CyBackRecord_info.br_person_name,  # 人员名字
            CyBackRecord_info.br_fill_back,  # 操作名称0：无操作，1：回填，2：回退
            CyBackRecord_info.br_detail,  # 操作详情
            CyBackRecord_info.br_fillBackLink,  # 回退步骤 0为区审核，1为待报批
            CyBackRecord_info.br_state,  # 操作状态
            CyBackRecord_info.br_identify_person,  # 审核人名字
            CyBackRecord_info.br_cid,  # 关联id 用于定位个人
            CyBackRecord_info.br_street_name,  # 所属街道
            CyBackRecord_info.br_type,  # 审核等级 0街道  1区级
            CyBackRecord_info.result,  # 审核结果
        ).filter(CyBackRecord_info.br_apply_num == self.apply_num,
                 CyBackRecord_info.br_person_ID == '',
                 CyBackRecord_info.br_state == self.br_state,
                 CyBackRecord_info.br_type == self.br_type,
                 CyBackRecord_info.br_fill_back != 2,  # 不是回退
                 ).first()
        return data

    # 7.获取某企业下所有用户
    def getCompanyPersonInfo(self):
        data = db.session.query(
            CyPersonInfo.id,  # id 自增
            CyPersonInfo.r_apply_num,  # 申领编号，关联企业
            CyPersonInfo.r_ID,  # 证件号码
            CyPersonInfo.r_name,  # 姓名
            CyPersonInfo.r_sex,  # 性别
            CyPersonInfo.r_age,  # 年龄
            CyPersonInfo.r_provinces,  # 是否省市
            CyPersonInfo.r_company_name,  # 单位名称
            CyPersonInfo.r_contract_date,  # 合同起止日期
            CyPersonInfo.r_local_type,  # 人员所在列表
            CyPersonInfo.r_ID_type,  # 证件类型
            CyPersonInfo.r_passnum,  # 通行证号码
            CyPersonInfo.r_social_num,  # 个人社保号
            CyPersonInfo.r_contract_start_date,  # 合同开始日期
            CyPersonInfo.r_contract_end_date,  # 合同结束日期
            CyPersonInfo.r_instructions,  # 审核说明
            CyPersonInfo.r_remarks,  # 备注
            CyPersonInfo.r_agent,  # 经办人
            CyPersonInfo.r_handling_date,  # 经办日期
            CyPersonInfo.r_handling_location,  # 经办机构
            # 额外参数
            CyPersonInfo.r_robot_result,  # 机器人预审结果
            CyPersonInfo.r_detail,  # 预审详情
            # todo：区审核
            CyPersonInfo.r_person_result,  # 区级人员审核结果
            CyPersonInfo.r_person_remark,  # 区级人员审核说明
            CyPersonInfo.r_identify_person,  # 区级审核人
            CyPersonInfo.r_person_detail,  # 人员详情信息是否齐全
            # 状态
            CyPersonInfo.r_social_state,  # 人员社保信息获取状态(默认为False)
            CyPersonInfo.r_final_list,  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)
            # 街道审核
            CyPersonInfo.r_street_result,  # 街道人员审核结果
            CyPersonInfo.r_street_person,  # 街道审核人
            CyPersonInfo.r_street_remark,  # 街道审核说明
            # 时间
            CyPersonInfo.r_create_time,  # 创建时间
            CyPersonInfo.r_update_time,  # 更新时间
        ).filter(
            CyPersonInfo.r_apply_num == self.apply_num
        )
        return data

    # 10.获取企业回填记录表
    def getCompanyBackInfoList(self):
        data = db.session.query(
            CyBackRecord_info.id,
            CyBackRecord_info.br_apply_num,  # 申领编号
            CyBackRecord_info.br_company,  # 企业名称
            CyBackRecord_info.br_person_ID,  # 人员证件号码
            CyBackRecord_info.br_person_name,  # 人员名字
            CyBackRecord_info.br_fill_back,  # 操作名称0：无操作，1：回填，2：回退
            CyBackRecord_info.br_detail,  # 操作详情
            CyBackRecord_info.br_fillBackLink,  # 回退步骤 0为区审核，1为待报批
            CyBackRecord_info.br_state,  # 操作状态 等待 成功 失败
            CyBackRecord_info.br_identify_person,  # 审核人名字
            CyBackRecord_info.br_cid,  # 关联id 用于定位个人
            CyBackRecord_info.br_street_name,  # 所属街道
            CyBackRecord_info.br_type,  # 审核权限类型，（0：街道，1：区级）
            CyBackRecord_info.result,  # 审核结果
        ).filter(
            CyBackRecord_info.br_apply_num.like("%" + self.apply_season + "%"),
            CyBackRecord_info.br_cid == None
        )
        return data

    # 11.获取企业cid下所有人员信息列表
    def getPersonCidBackInfoList(self):
        data = db.session.query(
            CyBackRecord_info.id,
            CyBackRecord_info.br_apply_num,  # 申领编号
            CyBackRecord_info.br_company,  # 企业名称
            CyBackRecord_info.br_person_ID,  # 人员证件号码
            CyBackRecord_info.br_person_name,  # 人员名字
            CyBackRecord_info.br_fill_back,  # 操作名称0：无操作，1：回填，2：回退
            CyBackRecord_info.br_detail,  # 操作详情
            CyBackRecord_info.br_fillBackLink,  # 回退步骤 0为区审核，1为待报批
            CyBackRecord_info.br_state,  # 操作状态 等待 成功 失败
            CyBackRecord_info.br_identify_person,  # 审核人名字
            CyBackRecord_info.br_cid,  # 关联id 用于定位个人
            CyBackRecord_info.br_street_name,  # 所属街道
            CyBackRecord_info.br_type,  # 审核权限类型，（0：街道，1：区级）
            CyBackRecord_info.result,  # 审核结果
        ).filter(
            CyBackRecord_info.br_apply_num == self.apply_num,
            CyBackRecord_info.br_cid == self.cid
        ).all()
        return data


class DBSessionAction(object):
    """
    数据库操作，
    增删改
    """

    def __init__(self):
        pass

    @staticmethod
    def changeObjectInfoData(changeObject, changeData, addCommit=False, isCommit=True):
        """
        params:
            person:  db查询后的对象
            changeData: 修改的数据键值对
            键为对象的属性，值为修改的值
                {
                    "p_verify_comment":"xxx"
                }
            addCommit:是否添加
            isCommit:是否提交
        """
        isSuccess = True
        try:
            for key in changeData.keys():
                changeObject.__setattr__(key, changeData[key])
            if addCommit:
                db.session.add(changeObject)
            if isCommit:
                db.session.commit()
        except Exception as e:
            logging.error(e)
            isSuccess = False
            db.session.rollback()
        return isSuccess

    @staticmethod
    def getObjectInfoData(dataObj, data):
        """
        params:
            dataObject:
                db查询后的对象
            data:
                查询的字段列表
        返回字典
        """
        dic = {}
        for d in data:
            dic[d] = dataObj.__getattribute__(d)

        return dic

    def getObjectListData(self, dataList, data):
        """
        [
            {
            "id":1,
            "name":"xxx"
            }
        ]
        """
        dic_list = []
        for d in dataList:
            dic = self.getObjectInfoData(d, data)
            dic_list.append(dic)
        return dic_list

    @staticmethod
    def zipDoubleList(list1, list2):
        """
        组合成字典
        list1为字段
        list2为值
        """
        dic = {}
        for key, value in zip(list1, list2):
            dic[key] = value
        return dic
