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


class GxbysLogicalProcessing(object):
    def __init__(self, **kwargs):
        self.card_ID = kwargs.get("card_ID", None)  # 毕业生证件号码
        self.apply_num = kwargs.get("apply_num", None)  # 申领编号
        self.searchKey = kwargs.get("searchKey", {})  # 查询条件
        self.apply_season = kwargs.get("apply_season", None)  # 申报年季

        self.roleName = kwargs.get("roleName", None)  # 账号所属街道
        self.page = kwargs.get("page", {"pageNum": 1, "pageSize": 40})  # 页数
        self.content = kwargs.get("content", None)  # 审批结果
        self.auditor = kwargs.get("auditor", None)  # 审核人

    # 1.获取补贴申报个体列表
    def getItemObjectList(self):
        reg = ResMsg()
        page_num = self.page.get("pageNum", 1)
        page_size = self.page.get("pageSize", 10)
        # 定义翻页参数
        page = {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": 0
        }
        # 筛选条件
        company_name = self.searchKey.get("company_name", None)  # 企业名称
        audit_state = self.searchKey.get("audit_state", None)  # 审核状态 1:审核通过 2：审核不通过 0：未审核
        auditor = self.searchKey.get("auditor", None)  # 审核人
        street_belong = self.searchKey.get("street_belong", None)  # 所属街道
        apply_num = self.searchKey.get("apply_num", None)  # 申领编号
        card_ID = self.searchKey.get("card_ID", None)  # 身份证号
        student_name = self.searchKey.get("person_name", None)  # 学生名称
        apply_season = self.searchKey.get("apply_season", None)  # 申领年季
        final_list = self.searchKey.get("final_list", -1)  # 所处列表
        # 获取基础查询信息
        base_query = DBSessionQuery(apply_season=apply_season).getStudentInfoList()
        # 筛选

        # 获取审核权限
        approval_type = getAccountAuthority(self.roleName)

        # 按权限获取内容
        if self.roleName == "海珠区":
            if street_belong:
                base_query = base_query.filter(StudentInfo.company_address.like("%{}%".format(street_belong)))
        else:
            base_query = base_query.filter(
                StudentInfo.company_address.like("%{}%".format(self.roleName)))  # 如果是街道，按街道筛选返回

        if company_name:
            base_query = base_query.filter(StudentInfo.company_name.like("%{}%".format(company_name)))

        # 审核状态
        if audit_state is not None:
            if approval_type == 0:  # 街道
                if audit_state == 0:  # 未审核
                    base_query = base_query.filter(StudentInfo.street_person == None)
                elif audit_state == 1:  # 审核通过
                    base_query = base_query.filter(StudentInfo.street_person != None, StudentInfo.street_result == 1)
                elif audit_state == 2:  # 审核不通过
                    base_query = base_query.filter(StudentInfo.street_person != None, StudentInfo.street_result == 0)
            elif approval_type == 1:  # 区级
                if audit_state == 0:  # 未审核
                    base_query = base_query.filter(StudentInfo.auditor == None)
                elif audit_state == 1:  # 审核通过
                    base_query = base_query.filter(StudentInfo.auditor != None, StudentInfo.artificial_audit == 1)
                elif audit_state == 2:  # 审核不通过
                    base_query = base_query.filter(StudentInfo.auditor != None, StudentInfo.artificial_audit == 0)
        # 审核人
        if auditor:
            if approval_type == 0:  # 街道
                base_query = base_query.filter(StudentInfo.auditor == auditor)
            elif approval_type == 1:  # 区级
                base_query = base_query.filter(StudentInfo.street_person == auditor)

        if apply_num:
            base_query = base_query.filter(StudentInfo.apply_num == apply_num)
        if card_ID:
            base_query = base_query.filter(StudentInfo.card_ID == card_ID)
        if student_name:
            base_query = base_query.filter(StudentInfo.name == student_name)
        if final_list != -1:
            base_query = base_query.filter(StudentInfo.final_list == final_list)

        total = base_query.count()  # 统计总数
        results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()

        fieldList = [
            "id", "apply_season", "apply_num", "isnet", "name", "card_ID", "sex", "age", "student_type", "company_name",
            "company_address", "employment_type", "contract_time", "subsidies", "audit_status", "document_type",
            "graduation_time", "graduate_school", "agent", "agent_date", "agent_institution", "robot_result", "explain",
            "artificial_audit", "auditor", "final_list", "employment_type", "street_result", "street_person",
            "credit_num"
        ]
        dictList = DBSessionAction().getObjectListData(results, fieldList)
        reg.update(data={
            "page": {
                "pageNum": page["pageNum"],
                "pageSize": page["pageSize"],
                "total": total
            },
            "ItemCode": "bysjcjybt",
            "ItemName": "高校毕业生就业补贴",
            "ItemType": 1,
            "data": dictList
        })
        return reg.data

    # 2.获取申报时间列表
    def getApplyDate(self):
        """
        2.获取申报时间列表
        """
        reg = ResMsg()

        now_date = datetime.date.today()
        year = now_date.year
        month = now_date.month
        data = []
        if 1 <= month <= 3:
            data = ["%s-1" % (year - 1), "%s-2" % (year - 1), "%s-3" % (year - 1), "%s-4" % (year - 1)]
        elif 4 <= month <= 6:
            data = ["%s-2" % (year - 1), "%s-3" % (year - 1), "%s-4" % (year - 1), "%s-1" % (year)]
        elif 7 <= month <= 9:
            data = ["%s-3" % (year - 1), "%s-4" % (year - 1), "%s-1" % (year), "%s-2" % (year)]
        elif 10 <= month <= 12:
            data = ["%s-4" % (year - 1), "%s-1" % (year), "%s-2" % (year), "%s-3" % (year)]
        reg.update(data=data)
        return reg.data

    # 5.获取人员详细信息（个人信息）
    def getPersonDetail(self):
        res = ResMsg()
        detailObj = {
            "ItemCode": "cyddjybt",
            "ItemName": "毕业生基层就业补贴",
            "ItemType": 1,
            "data": {
                "ID_list": [],  # 获取同一列表下
                "personInfoData": {},  # 人员详情信息
                "allowanceInfoData": [],  # 个人补贴享受情况
                "recordInfoData": [],  # 就业登记情况
                "socialPayInfoData": [],  # 社保缴纳情况
                "xwCompanyInfoData": [],  # 小薇企业信息
                "businessInfoData": [],  # 商事登记列表
                "personPreditResult": {},  # 人员预审详情
                "degreeInfoList": [],  # 学历信息

                "ID_list_count": "",  # 获取同列表，同街道人数
                "file_path_list": [],  # 文件路径列表
                "screen_path_list": [],  # 截图路径
                "companyPreditResult": [],  # 企业预审详情

            }
        }
        # 获取人员详情信息
        student_base_query = DBSessionQuery(apply_season=self.apply_num[12:-1],
                                            card_ID=self.card_ID).getStudentDetailInfo()

        filed_list = [
            "id", "apply_num", "apply_season", "isnet", "name", "card_ID", "sex", "age", "student_type", "company_name",
            "credit_num", "employment_type", "contract_time", "subsidies", "audit_status", "audit_instructions",
            "company_contact", "company_phone", "claimant_phone", "company_address", "document_type", "contract_start",
            "contract_end", "social_security_ID", "graduation_time", "registration_time", "is_social_card",
            "social_cardID", "bank", "account_name", "passID", "graduate_school", "qualified_time", "bank_account",
            "remark", "diploma_path", "agent", "agent_date", "agent_institution", "get_data_state", "robot_result",
            "explain", "artificial_audit", "isaudit", "auditor", "audit_date", "is_ent", "is_summary", "company_type",
            "extra_social_count", "social_security_state", "employment_state", "ent_state", "graduate_state",
            "xwCompany_state", "is_sendEmail", "outputFile", "create_datetime", "update_datetime", "screen_path",
            "company_addr", "final_list", "region_remark", "street_result", "street_person", "street_remark",
        ]

        if not student_base_query:
            res.update(code=-1, msg="请求参数有误")
            return res.data

        try:
            # 人员详情信息
            detailObj["data"]["personInfoData"] = DBSessionAction().getObjectInfoData(student_base_query,
                                                                                      filed_list)  # 转字典
            # 同街道、同列表人员card_ID
            ID_list = DBSessionQuery(final_list=detailObj["data"]["personInfoData"]["final_list"],
                                     street_belong=detailObj["data"]["personInfoData"]["company_address"],
                                     card_ID=self.card_ID).getIDList()
            detailObj["data"]["ID_list_count"] = ID_list.count()
            detailObj["data"]["ID_list"] = ID_list.first()

            # 查询社保缴纳情况
            social_pay = DBSessionQuery(card_ID=self.card_ID).getSocialInfo()
            social_pay_filed_list = ["id", "s_ID", "s_pay_date", "s_old_base", "s_medical_base", "s_old_insur",
                                     "s_unemploy_insur", "s_injury_insur", "s_medical_insur", "s_c_old_insur",
                                     "s_c_unemploy_insur", "s_c_injury_insur", "s_c_medical_insur", "s_c_disease_insur",
                                     "s_c_birth_insur", "s_social_num", "s_social_c_num", "s_social_c_name",
                                     "s_social_credit_num", "s_medical_num", "s_medical_c_num", "s_medical_c_name",
                                     "s_medical_credit_num", ]

            detailObj["data"]["socialPayInfoData"] = DBSessionAction().getObjectListData(social_pay,
                                                                                         social_pay_filed_list)  # 转字典

            # 查询就业登记信息
            # record_info = DBSessionQuery(card_ID=self.card_ID).getRecordInfo()
            # record_info_filed_list = ["id", "r_accept_batch", "r_company_name", "r_ID", "r_name", "r_sex", "r_birth",
            #                           "r_degree", "r_population", "r_location", "r_register_type",
            #                           "r_contract_start_date", "r_contract_end_date", "r_relieve_date",
            #                           "r_register_date", "r_isapply", "r_date_source", ]
            # detailObj["data"]["recordInfoData"] = DBSessionAction().getObjectListData(record_info,
            #                                                                           record_info_filed_list)  # 转字典

            # 查询个人补贴享受情况
            allowance_info = DBSessionQuery(card_ID=self.card_ID).getAllowanceInfo()
            allowance_info_filed_list = [
                "id", "z_reason", "z_name", "z_sex", "z_age", "z_ID", "z_login_num", "z_free_num", "z_person_type",
                "z_hard_type", "z_contract_date", "z_authority_count", "z_old_insur", "z_unemploy_insur",
                "z_injury_insur", "z_birth_insur", "z_medical_insur", "z_social_insur", "z_postion_insur",
                "z_allow_count", "z_help_type", "z_state", "z_author", "z_isRegister", "z_company_name",
                "z_social_fund_type", "z_position_fund_type", "z_refund_mark", "z_approved_date", "z_total",
            ]
            detailObj["data"]["allowanceInfoData"] = DBSessionAction().getObjectListData(allowance_info,
                                                                                         allowance_info_filed_list)  # 转字典

            # 查询小微企业信息
            xw_company = DBSessionQuery(credit_num=detailObj["data"]["personInfoData"]["credit_num"]).getXwCompanyInfo()
            xw_company_filed_list = [
                "id", "main_num", "social_num", "register_num", "company_name", "main_type", "setup_date",
                "register_fund", "register_location_num", "register_location", "belong_type", "work_num", "work_name",
                "xw_type", "xw_type_name", "join_datetime", "exit_datetime", "exit_reason", "exit_reasons", "xw_state",
                "xw_state_name", "total_unit", "total_unit_date",
            ]
            detailObj["data"]["xwCompanyInfoData"] = DBSessionAction().getObjectListData(xw_company,
                                                                                         xw_company_filed_list)  # 转字典

            # 查询商事登记信息
            business_info = DBSessionQuery(card_ID=self.card_ID).getBuinessInfo()
            business_info_filed_list = [
                "id", "b_register_num", "b_credit_num", "b_company", "b_charge_name", "b_ID", "b_main_type",
                "b_pro_type", "b_date", "b_state", "b_relieve_date",
            ]
            detailObj["data"]["businessInfoData"] = DBSessionAction().getObjectListData(business_info,
                                                                                        business_info_filed_list)  # 转字典

            # 查询学历信息
            degree_info = DBSessionQuery(card_ID=self.card_ID).getDegreeInfo()
            degree_info_filed_list = [
                "id", "card_ID", "name", "identifyCode", "graduate_school", "graduate_subject", "graduation",
                "admission_date", "graduate_date", "study_type", "graduate_num",
            ]
            detailObj["data"]["degreeInfoList"] = DBSessionAction().getObjectListData(degree_info,
                                                                                      degree_info_filed_list)  # 转字典

            # 获取个人预审详情信息
            # detailObj["data"]["personPreditResult"] = detailObj["data"]["personInfoData"]["explain"]

            # 附件、截图列表
            pre_url = "http://{}/bysbt".format(SERVER_HOST1)  # 附件路径
            screen_url = "http://{}/bysbtScreen/".format(SERVER_HOST1)  # 截图路径
            file_list = detailObj["data"]["personInfoData"]["diploma_path"]
            screen_list = detailObj["data"]["personInfoData"]["screen_path"]
            if screen_list != "":
                detailObj["data"]["screen_path_list"].append(screen_url + screen_list)
            try:
                file_list = eval(file_list)
                file_list = ast.literal_eval(file_list)
                for i in file_list:
                    url = pre_url + i
                    detailObj["data"]["file_path_list"].append(url)
            except Exception as e:
                logging.error("没有附件" + str(e))

            # 返回
            res.update(data=detailObj)
            return res.data
        except Exception as e:
            logging.error("getPersonDetailInfo接口异常:" + str(e))
            res.update(code=-1, msg="接口异常")
            return res.data

    # 6.提交人员审核结果请求
    def approvedPerson(self):
        res = ResMsg()
        if not self.card_ID or not self.apply_num:
            res.update(code=-1, msg="传入人员参数有误，请核查信息")
            return res.data
        approval_result = self.content.get("approval_result", None)
        approval_person = self.content.get("approval_person", None)
        approval_comment = self.content.get("approval_comment", None)

        if approval_result is None or not approval_person:
            res.update(code=-1, msg="传入审核参数有误，请核查信息")
            return res.data
        approval_type = getAccountAuthority(self.roleName)  # 判断账号权限 0街道 1区级

        # 查询学生个人基本信息
        student_info = DBSessionQuery(apply_season=self.apply_num[12:-1],
                                      card_ID=self.card_ID).getStudentDetailInfo()
        # 筛选 当前权限等级的记录
        if not student_info:
            res.update(code=-1, msg="系统有误，无法查询到该人信息！")
            return res.data
        if approval_type == 0:  # 街道
            if student_info.auditor:
                res.update(code=-1, msg="区已审核，你无法再审核该人！")
                return res.data

        # 校验：审核不通过需要审核说明
        if approval_result == 0:  # 审核不通过
            if approval_comment is None or approval_comment == "" or not approval_comment:
                res.update(code=-1, msg="审核不通过必须添加审核说明！")
                return res.data
        # 查询是否有回填记录
        # 如果有已有审核成功
        have_success_back_info = DBSessionQuery(apply_num=self.apply_num, card_ID=self.card_ID, br_type=approval_type,
                                                state="成功").getBackStateInfo()
        if have_success_back_info:
            res.update(code=-1, msg="该人已成功回填至PJ5系统，请回退后再进行审核!")
            return res.data

        # 如果有已有审核等待
        have_await_back_info = DBSessionQuery(apply_num=self.apply_num, card_ID=self.card_ID, br_type=approval_type,
                                              state="等待").getBackStateInfo()

        # 审核结果对应列表位置
        if int(approval_result) == 0:  # 失败
            final_list = 2  # 失败列表
        elif int(approval_result) == 1:  # 成功
            final_list = 1  # 成功列表
        else:
            final_list = 0  # 预审列表

        if have_await_back_info:
            if approval_type == 0:  # 街道审核
                db.session.query(StudentInfo).filter(StudentInfo.apply_num == self.apply_num,
                                                     StudentInfo.card_ID == self.card_ID).update(
                    {"street_person": approval_person, "street_result": approval_result,
                     "street_remark": approval_comment, "final_list": final_list})
                # 新增回填表显示审核结果
                db.session.query(BysBackInfo).filter(BysBackInfo.apply_num == self.apply_num,
                                                     BysBackInfo.card_ID == self.card_ID,
                                                     BysBackInfo.br_type == 0).update(
                    {"result": approval_result})
                db.session.commit()
                res.update(code=200, msg="成功提交街道审核结果!")
                return res.data
            elif approval_type == 1:  # 区审核
                db.session.query(StudentInfo).filter(StudentInfo.apply_num == self.apply_num,
                                                     StudentInfo.card_ID == self.card_ID).update(
                    {"auditor": approval_person, "artificial_audit": approval_result,
                     "region_remark": approval_comment, "final_list": final_list})
                # 新增回填表显示审核结果
                db.session.query(BysBackInfo).filter(BysBackInfo.apply_num == self.apply_num,
                                                     BysBackInfo.card_ID == self.card_ID,
                                                     BysBackInfo.br_type == 1).update(
                    {"result": approval_result})
                db.session.commit()
                res.update(code=200, msg="成功提交区级审核结果!")
                return res.data
            else:
                res.update(code=-1, msg="非街道审核/区审核，无法提交审核结果!")
                return res.data

        # 如果有已有审核失败/未审核
        # 新增回填表BysBackInfo,修改student_info
        # 先新增
        new_bys_back_info = BysBackInfo()
        new_bys_back_info.apply_num = self.apply_num
        new_bys_back_info.card_ID = self.card_ID
        new_bys_back_info.fill_back = 1  # 回填

        new_bys_back_info.state = "等待"
        new_bys_back_info.identify_person = approval_person
        new_bys_back_info.br_type = approval_type
        new_bys_back_info.br_street_name = student_info.company_address
        new_bys_back_info.name = student_info.name
        new_bys_back_info.company_name = student_info.company_name
        new_bys_back_info.result = approval_result
        db.session.add(new_bys_back_info)
        db.session.commit()
        # 再修改
        if approval_type == 0:  # 街道审核
            db.session.query(StudentInfo).filter(StudentInfo.apply_num == self.apply_num,
                                                 StudentInfo.card_ID == self.card_ID).update(
                {"street_person": approval_person, "street_result": approval_result,
                 "street_remark": approval_comment, "final_list": final_list})
            db.session.commit()
            res.update(code=200, msg="成功提交街道审核结果!")
            return res.data
        elif approval_type == 1:  # 区审核
            db.session.query(StudentInfo).filter(StudentInfo.apply_num == self.apply_num,
                                                 StudentInfo.card_ID == self.card_ID).update(
                {"auditor": approval_person, "artificial_audit": approval_result,
                 "region_remark": approval_comment, "final_list": final_list})
            db.session.commit()
            res.update(code=200, msg="成功提交区级审核结果!")
            return res.data
        else:
            res.update(code=-1, msg="非街道审核/区审核，无法提交审核结果!")
            return res.data

    # 9.个人回退
    def personRollback(self):
        res = ResMsg()
        # 检验输入参数apply_num=apply_num, auditor=auditor, roleName=roleName,card_ID=card_ID
        if not self.apply_num or not self.auditor or not self.roleName or not self.card_ID:
            res.update(code=-1, msg="输入参数有误(为空)，请核查！")
            return res.data
        # 获取当前账号权限
        approved_type = getAccountAuthority(self.roleName)
        # 查询人员基本信息
        person_detail_info = DBSessionQuery(apply_season=self.apply_num[12:-1],
                                            card_ID=self.card_ID).getStudentDetailInfo()
        if approved_type == 0:
            if person_detail_info.auditor:
                res.update(code=-1, msg="区已审核，你无法回退！")
                return res.data

        # 查询回填表信息
        back_info = DBSessionQuery(apply_num=self.apply_num, card_ID=self.card_ID, state="成功",
                                   br_type=approved_type).getBackStateInfo()

        # 存在已回填信息
        if back_info:
            if approved_type == 0:  # 街道
                # 先修改回填表
                db.session.query(BysBackInfo).filter(BysBackInfo.apply_num == self.apply_num,
                                                     BysBackInfo.card_ID == self.card_ID, BysBackInfo.state == "成功",
                                                     BysBackInfo.br_type == 0).update(
                    {"state": "等待", "detail": self.auditor + ":审核异常立即回退", "fill_back": 2})

                # 再修改学生信息
                db.session.query(StudentInfo).filter(StudentInfo.apply_num == self.apply_num,
                                                     StudentInfo.card_ID == self.card_ID).update(
                    {"street_result": None, "street_person": None,
                     "street_remark": None, "final_list": 0})

                db.session.commit()
            elif approved_type == 1:  # 区级
                # 先修改回填表
                db.session.query(BysBackInfo).filter(BysBackInfo.apply_num == self.apply_num,
                                                     BysBackInfo.card_ID == self.card_ID, BysBackInfo.state == "成功",
                                                     BysBackInfo.br_type == 1).update(
                    {"state": "等待", "detail": self.auditor + ":审核异常立即回退", "fill_back": 2})

                # 再修改学生信息
                db.session.query(StudentInfo).filter(StudentInfo.apply_num == self.apply_num,
                                                     StudentInfo.card_ID == self.card_ID).update(
                    {"artificial_audit": None, "auditor": None,
                     "region_remark": None, "final_list": 0})

                db.session.commit()
            res.update(code=200, msg="回退成功！")
            return res.data
        else:
            res.update(code=-1, msg="该人员未回填或回填失败，您无需回退，即可审核！")
            return res.data

    # 10.企业/个人回填回退记录
    def BackRecord(self):
        reg = ResMsg()
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
        if apply_season is None:
            year = datetime.date.today().year
            month = datetime.date.today().month
            if month in [1, 2, 3]:
                apply_season = str(year) + "-1"
            elif month in [4, 5, 6]:
                apply_season = str(year) + "-2"
            elif month in [7, 8, 9]:
                apply_season = str(year) + "-3"
            else:
                apply_season = str(year) + "-4"

        state = self.searchKey.get("state", None)  # 回填状态
        auditor = self.searchKey.get("auditor", None)  # 审核人
        street_belong = self.searchKey.get("street_belong", None)  # 所属街道

        apply_num = self.searchKey.get("apply_num", None)  # 申领编号
        card_ID = self.searchKey.get("card_ID", None)  # 身份证号
        student_name = self.searchKey.get("person_name", None)  # 学生名称
        company_name = self.searchKey.get("company_name", None)  # 企业名称

        # 获取基础查询信息
        base_query = DBSessionQuery(apply_season=apply_season).getBackInfoList()

        # 查询权限
        approved_type = getAccountAuthority(self.roleName)
        if approved_type == 1:  # 区级
            if street_belong:
                base_query = base_query.filter(BysBackInfo.br_street_name == street_belong)
        elif approved_type == 0:
            base_query = base_query.filter(BysBackInfo.br_street_name == self.roleName)

        # 查询条件筛选
        # 审核人
        if auditor:
            base_query = base_query.filter(BysBackInfo.identify_person == auditor)
        # 审核状态
        if state is not None:
            base_query = base_query.filter(BysBackInfo.state == state)
        # 申领编号
        if apply_num:
            base_query = base_query.filter(BysBackInfo.apply_num == apply_num)
        # 身份证号
        if card_ID:
            base_query = base_query.filter(BysBackInfo.card_ID == card_ID)
        # 学生名字
        if student_name:
            base_query = base_query.filter(BysBackInfo.name.like("%" + student_name + "%"))
        if company_name:
            base_query = base_query.filter(BysBackInfo.company_name.like("%" + company_name + "%"))

        total = base_query.count()  # 统计总数
        results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()

        fieldList = [
            "id", "apply_num", "card_ID", "fill_back", "fill_back_link", "state", "detail", "identify_person",
            "create_date", "update_date", "br_type", "br_street_name", "name", "company_name", "result"
        ]
        dictList = DBSessionAction().getObjectListData(results, fieldList)
        reg.update(data={
            "page": {
                "pageNum": page["pageNum"],
                "pageSize": page["pageSize"],
                "total": total
            },
            "ItemCode": "bysjcjybt",
            "ItemName": "高校毕业生就业补贴",
            "ItemType": 1,
            "data": dictList
        })
        return reg.data


class DBSessionQuery(object):
    """
    数据库查询操作
    """

    def __init__(self, **kwargs):
        self.card_ID = kwargs.get("card_ID", None)  # 毕业生证件号码
        self.apply_num = kwargs.get("apply_num", None)  # 申领编号
        self.apply_season = kwargs.get("apply_season", None)  # 申报年季
        self.roleName = kwargs.get("roleName", None)  # 账号所属街道

        self.street_belong = kwargs.get("street_belong", None)  # 所属街道
        self.final_list = kwargs.get("final_list", None)  # 人员所处列表
        self.credit_num = kwargs.get("credit_num", None)  # 企业社会信用代码

        self.br_type = kwargs.get("br_type", None)  # 回填等级
        self.state = kwargs.get("state", None)  # 回填状态：成功，失败，等待

    def getStudentInfoList(self):
        data = db.session.query(
            StudentInfo.id,  #
            StudentInfo.apply_season,  # 申报年季
            StudentInfo.apply_num,  # 申领编号
            StudentInfo.isnet,  # 是否网办
            StudentInfo.name,  # 姓名
            StudentInfo.card_ID,  # 证件号码
            StudentInfo.sex,  # 性别
            StudentInfo.age,  # 年龄
            StudentInfo.student_type,  # 毕业生类别
            StudentInfo.company_name,  # 单位名称
            StudentInfo.company_address,  # 公司所在街道
            StudentInfo.employment_type,  # 就业类型
            StudentInfo.contract_time,  # 合同起止日期
            StudentInfo.subsidies,  # 补贴金额
            StudentInfo.audit_status,  # 审核状态
            StudentInfo.document_type,  # 证件类型
            StudentInfo.graduation_time,  # 毕业时间
            StudentInfo.graduate_school,  # 毕业院校
            StudentInfo.agent,  # 经办人
            StudentInfo.agent_date,  # 经办时间
            StudentInfo.agent_institution,  # 经办机构
            StudentInfo.robot_result,  # 机器人预审结果
            StudentInfo.explain,  # 机器人预审说明
            StudentInfo.artificial_audit,  # 区人工审核结果
            StudentInfo.auditor,  # 区审核人
            StudentInfo.final_list,  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)
            StudentInfo.employment_type,  # 企业类型
            StudentInfo.street_result,  # 街道审核结果
            StudentInfo.street_person,  # 街道审核人
            StudentInfo.credit_num,  # 统一信用代码
        ).filter(
            StudentInfo.apply_season == self.apply_season,
        )
        return data

    # 获取详情信息
    def getStudentDetailInfo(self):
        data = db.session.query(
            StudentInfo.id,  #
            StudentInfo.apply_num,  # 申领编号
            StudentInfo.apply_season,  # 申办年季
            StudentInfo.isnet,  # 是否网办
            StudentInfo.name,  # 姓名
            StudentInfo.card_ID,  # 证件号码
            StudentInfo.sex,  # 性别
            StudentInfo.age,  # 年龄
            StudentInfo.student_type,  # 毕业生类别
            StudentInfo.company_name,  # 单位名称
            StudentInfo.credit_num,  # 统一社会信用代码
            StudentInfo.employment_type,  # 就业类型
            StudentInfo.contract_time,  # 合同起止日期
            StudentInfo.subsidies,  # 补贴金额
            StudentInfo.audit_status,  # 审核状态
            StudentInfo.audit_instructions,  # 审核说明
            StudentInfo.company_contact,  # 单位里联系人
            StudentInfo.company_phone,  # 单位联系电话
            StudentInfo.claimant_phone,  # 申领人联系电话
            StudentInfo.company_address,  # 单位所属地
            StudentInfo.document_type,  # 证件类型
            StudentInfo.contract_start,  # 合同开始日期
            StudentInfo.contract_end,  # 合同结束日期
            StudentInfo.social_security_ID,  # 个人社保号
            StudentInfo.graduation_time,  # 毕业时间
            StudentInfo.registration_time,  # 报到时间
            StudentInfo.is_social_card,  # 是否发放到社保卡
            StudentInfo.social_cardID,  # 社保卡号
            StudentInfo.bank,  # 开户银行
            StudentInfo.account_name,  # 开户名称
            StudentInfo.passID,  # 通行证号码
            StudentInfo.graduate_school,  # 毕业院校
            StudentInfo.qualified_time,  # 考核合格时间
            StudentInfo.bank_account,  # 银行账号
            StudentInfo.remark,  # 备注
            StudentInfo.diploma_path,  # 毕业证附件路径
            StudentInfo.agent,  # 经办人
            StudentInfo.agent_date,  # 经办时间
            StudentInfo.agent_institution,  # 经办机构
            StudentInfo.get_data_state,  # 数据抓取状态
            StudentInfo.robot_result,  # 机器人预审结果
            StudentInfo.explain,  # 预审说明
            StudentInfo.artificial_audit,  # 人工审核结果
            StudentInfo.isaudit,  # 是否审核完成
            StudentInfo.auditor,  # 审核人
            StudentInfo.audit_date,  # 审核时间
            StudentInfo.is_ent,  # 是否创业或高管
            StudentInfo.is_summary,  # 是否区汇总
            StudentInfo.company_type,  # 企业类型
            StudentInfo.extra_social_count,  # 企业参保人数
            StudentInfo.social_security_state,  # 社保抓取状态
            StudentInfo.employment_state,  # 就业登记抓取状态
            StudentInfo.ent_state,  # 商事登记信息抓取状态
            StudentInfo.graduate_state,  # 毕业生信息抓取状态
            StudentInfo.xwCompany_state,  # 小微企业信息抓取状态
            StudentInfo.is_sendEmail,  # 是否发送短信
            StudentInfo.outputFile,  # 是否导出过表格
            StudentInfo.create_datetime,  # 创建时间
            StudentInfo.update_datetime,  # 更新时间
            StudentInfo.screen_path,  # 截屏路径
            StudentInfo.company_addr,  # 企业地址等信息
            StudentInfo.final_list,  # 申报人员在审批系统上的位置(0：预审列表，1：成功列表，2：失败列表)
            StudentInfo.region_remark,  # 区级审核说明
            StudentInfo.street_result,  # 街道人员审核结果
            StudentInfo.street_person,  # 街道审核人
            StudentInfo.street_remark,  # 街道审核说明
        ).filter(StudentInfo.apply_season == self.apply_season,
                 StudentInfo.card_ID == self.card_ID
                 ).first()

        return data

    # 5.获取相同街道、列表人员id,申领编号apply_num
    def getIDList(self):
        data = db.session.query(
            StudentInfo.apply_num,
            StudentInfo.card_ID
        ).filter(
            StudentInfo.final_list == self.final_list,
            StudentInfo.company_address == self.street_belong,
            StudentInfo.card_ID != self.card_ID
        )
        return data

    # 获取就业登记信息
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

    # 获取个人补贴享受情况
    def getAllowanceInfo(self):
        data = db.session.query(
            AllowanceInfo.id,
            AllowanceInfo.z_reason,
            AllowanceInfo.z_name,
            AllowanceInfo.z_sex,
            AllowanceInfo.z_age,
            AllowanceInfo.z_ID,
            AllowanceInfo.z_login_num,
            AllowanceInfo.z_free_num,
            AllowanceInfo.z_person_type,
            AllowanceInfo.z_hard_type,
            AllowanceInfo.z_contract_date,
            AllowanceInfo.z_authority_count,
            AllowanceInfo.z_old_insur,
            AllowanceInfo.z_unemploy_insur,
            AllowanceInfo.z_injury_insur,
            AllowanceInfo.z_birth_insur,
            AllowanceInfo.z_medical_insur,
            AllowanceInfo.z_social_insur,
            AllowanceInfo.z_postion_insur,
            AllowanceInfo.z_allow_count,
            AllowanceInfo.z_help_type,
            AllowanceInfo.z_state,
            AllowanceInfo.z_author,
            AllowanceInfo.z_isRegister,
            AllowanceInfo.z_company_name,
            AllowanceInfo.z_social_fund_type,
            AllowanceInfo.z_position_fund_type,
            AllowanceInfo.z_refund_mark,
            AllowanceInfo.z_approved_date,
            AllowanceInfo.z_total,
        ).filter(
            AllowanceInfo.z_ID == self.card_ID
        ).all()
        return data

    # 获取社保缴纳信息
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

    # 获取小微企业信息
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

    # 获取学历信息
    def getDegreeInfo(self):
        data = db.session.query(
            DegreeInfo.id,  #
            DegreeInfo.card_ID,  # 证件号码
            DegreeInfo.name,  # 姓名
            DegreeInfo.identifyCode,  # 请求标识码
            DegreeInfo.graduate_school,  # 毕业学校名称
            DegreeInfo.graduate_subject,  # 专业名称
            DegreeInfo.graduation,  # 层次
            DegreeInfo.admission_date,  # 入学时间
            DegreeInfo.graduate_date,  # 毕业时间
            DegreeInfo.study_type,  # 学习形式
            DegreeInfo.graduate_num,  # 学历证书编号
        ).filter(
            DegreeInfo.card_ID == self.card_ID
        ).all()
        return data

    # 查询商事登记信息
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

    # 6.查询个人回填信息
    def getBackInfo(self):
        data = db.session.query(
            BysBackInfo.id,  #
            BysBackInfo.apply_num,  # 申领编号
            BysBackInfo.card_ID,  # 证件号码
            BysBackInfo.fill_back,  # 回填还是回退
            BysBackInfo.fill_back_link,  # 回退环节
            BysBackInfo.state,  # 回填回退状态
            BysBackInfo.detail,  # 详情，操作失败原因
            BysBackInfo.identify_person,  # 办理人
            BysBackInfo.create_date,  # 创建时间
            BysBackInfo.update_date,  # 更新时间
            BysBackInfo.br_type,  # 审核权限类型，（0：街道，1：区级）
            BysBackInfo.br_street_name,  # 所属街道
            BysBackInfo.name,  # 人名
            BysBackInfo.company_name,  # 企业名
            BysBackInfo.result,  # 审核结果
        ).filter(
            BysBackInfo.apply_num == self.apply_num,
            BysBackInfo.card_ID == self.card_ID,
            BysBackInfo.br_type == self.br_type,
        )
        return data

    # 6&10.查询回填状态信息
    def getBackStateInfo(self):
        data = db.session.query(
            BysBackInfo.id,  #
            BysBackInfo.apply_num,  # 申领编号
            BysBackInfo.card_ID,  # 证件号码
            BysBackInfo.fill_back,  # 回填还是回退
            BysBackInfo.fill_back_link,  # 回退环节
            BysBackInfo.state,  # 回填回退状态
            BysBackInfo.detail,  # 详情，操作失败原因
            BysBackInfo.identify_person,  # 办理人
            BysBackInfo.create_date,  # 创建时间
            BysBackInfo.update_date,  # 更新时间
            BysBackInfo.br_type,  # 审核权限类型，（0：街道，1：区级）
            BysBackInfo.br_street_name,  # 所属街道
            BysBackInfo.name,  # 人名
            BysBackInfo.company_name,  # 企业名
            BysBackInfo.result,  # 审核结果
        ).filter(
            BysBackInfo.apply_num == self.apply_num,
            BysBackInfo.card_ID == self.card_ID,
            BysBackInfo.br_type == self.br_type,
            BysBackInfo.state == self.state,
            BysBackInfo.fill_back == 1,
        ).first()
        return data

    # 10.获取回填表列表信息
    def getBackInfoList(self):
        data = db.session.query(
            BysBackInfo.id,  #
            BysBackInfo.apply_num,  # 申领编号
            BysBackInfo.card_ID,  # 证件号码
            BysBackInfo.fill_back,  # 操作名称0：无操作，1：回填，2：回退
            BysBackInfo.fill_back_link,  # 回退环节
            BysBackInfo.state,  # 回填回退状态
            BysBackInfo.detail,  # 详情，操作失败原因
            BysBackInfo.identify_person,  # 办理人
            BysBackInfo.create_date,  # 创建时间
            BysBackInfo.update_date,  # 更新时间
            BysBackInfo.br_type,  # 审核权限类型，（0：街道，1：区级）
            BysBackInfo.br_street_name,  # 所属街道
            BysBackInfo.name,  # 人名
            BysBackInfo.company_name,  # 企业名
            BysBackInfo.result,  # 审核结果
        ).filter(
            BysBackInfo.apply_num.like('%' + self.apply_season + '%')
        )
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
