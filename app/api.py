import datetime
import datetime
import hashlib
import json
import logging
import numpy as np
import os
import pandas as pd
import re
import requests
import xlsxwriter as xw
from concurrent.futures import ThreadPoolExecutor  # 异步处理耗时计算
from flask import Blueprint, jsonify, request, send_file, Response, make_response, send_from_directory, redirect
from flask import Flask
from flask import send_file
from io import StringIO
from sqlalchemy import and_, null, or_
from sqlalchemy import or_
from urllib import parse

from app.models import *
from app.utils import ResMsg, DBSessionQuery, DBSessionAction
from app.utils import ToolFunc
from config import *
from constants import *

bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(5)  # 处理耗时任务


def mapping_base(fields, data, status_data: dict = None):
    temp = list()
    if data:
        for key in data.keys():
            # 字段映射匹配
            # temp.append({"en_name": key, "zh_name": fields.get(key), "value": getattr(data, key)})
            temp_dict = {"en_name": key, "zh_name": fields.get(key), "value": getattr(data, key)}
            if status_data:
                temp_dict["value_status"] = getattr(status_data, str(key) + '_status', None)
            temp.append(temp_dict)
    return temp


def mapping_field(fields, results, status_data: dict = None):
    data = list()
    if results:
        for idx, item in enumerate(results):
            temp = mapping_base(fields, item, status_data[idx] if status_data else None)
            data.append(temp)
    return data


def get_apply_season():
    today = datetime.date.today()
    year = today.year
    month = today.month
    season = ''
    if month in [1, 2, 3]:
        season = str(year - 1) + '-' + '4'
    elif month in [4, 5, 6]:
        season = str(year) + '-' + '1'
    elif month in [7, 8, 9]:
        season = str(year) + '-' + '2'
    elif month in [10, 11, 12]:
        season = str(year) + '-' + '3'
    return season


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


def calculateCompanyPersonType(apply_num):
    """计算各类人员的总人数"""
    try:
        company = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()
        hard_employ_count = PersonInfo.query.filter(PersonInfo.p_c_apply_num == apply_num,
                                                    PersonInfo.p_type == '就业困难人员').count()
        graduate_count = PersonInfo.query.filter(PersonInfo.p_c_apply_num == apply_num,
                                                 PersonInfo.p_type == '高校等毕业生').count()
        army_count = PersonInfo.query.filter(PersonInfo.p_c_apply_num == apply_num,
                                             PersonInfo.p_type == '随军家属').count()

        company.c_hard_employ_count = hard_employ_count
        company.c_graduate_count = graduate_count
        company.c_army_count = army_count
        db.session.commit()
    except Exception as e:
        logging.error("计算错误:" + str(e))
        db.session.rollback()


@bp.route('/api/v1/companyList', methods=["POST"])
def get_company_list():
    """
    获取公司列表
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    page = obj.get('page', dict())
    page_num = int(page.get("pageNum", 1))
    page_size = int(page.get("pageSize", 10))
    # 申报年季
    apply_season = obj.get("apply_season", None)
    # 公司名称
    company_name = obj.get("company_name", None)
    # 审核状态
    person_result = obj.get('c_person_result', None)
    identify_person = obj.get('c_identify_person', None)
    # 街道筛选
    street_belong = obj.get('c_street_belong', None)
    # 用户权限
    roleName = obj.get('roleName', None)

    # logging.error(roleName)

    # 定义翻页参数
    page = {
        "pageNum": page_num,
        "pageSize": page_size,
        "total": 0,
    }

    res.add_field(name="page", value=page)
    account_type = getAccountAuthority(roleName)
    if account_type == 0:
        pass
    elif account_type == 1:
        pass
    else:
        res.update(code=-1, msg="请用街道账号或者区级账号登录")
        return jsonify(res.data)

    # 判断页数是否为非法字段
    if not page_num >= 1 or not page_size >= 0:
        res.update(code=-1, msg='字段非法')
        return jsonify(res.data)
    if not apply_season:
        apply_season = get_apply_season()
    # 查询字段匹配内容
    fields = ToolFunc().static_fields()

    base_query = DBSessionQuery.get_company_list_query()
    # 申领季度
    if apply_season:
        base_query = base_query.filter(CompanyInfo.c_apply_season == apply_season)

    # 公司名称
    if company_name:
        base_query = base_query.filter(CompanyInfo.c_name.like('%' + company_name.strip() + '%'))
    # 审核状态
    if person_result == 0:
        if account_type == 0:
            base_query = base_query.filter(CompanyInfo.c_street_result == None)
        else:
            base_query = base_query.filter(CompanyInfo.c_person_result == None)
    elif person_result == 1:
        if account_type == 0:
            base_query = base_query.filter(CompanyInfo.c_street_result == True)
        else:
            base_query = base_query.filter(CompanyInfo.c_person_result == True)
    elif person_result == 2:
        if account_type == 0:
            base_query = base_query.filter(CompanyInfo.c_street_result == False)
        else:
            base_query = base_query.filter(CompanyInfo.c_person_result == False)

    # 审核人
    if identify_person != None:
        base_query = base_query.filter(CompanyInfo.c_identify_person == identify_person)

    # 权限限制  2022-03-04新增
    if roleName:
        base_query = base_query.filter(CompanyInfo.c_street_belong.like('%' + roleName + '%'))

    # 街道筛选  2022-02-25海珠新增
    if street_belong is not None and roleName == '海珠区':
        base_query = base_query.filter(CompanyInfo.c_street_belong.like('%' + street_belong.strip() + '%'))

    # 总数
    total = base_query.count()
    results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()

    data = mapping_field(fields=fields, results=results)
    for i in data:
        '''计算各类人员数量'''
        # 申领编号
        apply_num = i[5]['value']
        executor.submit(calculateCompanyPersonType, apply_num)
        try:
            i[28]['value'] = ''.join(eval(i[28]['value']))
        except:
            i[28]['value'] = '企业未预审'
    page["total"] = total
    res.update(data={
        'data': data,
    })
    return jsonify(res.data)


def calculatePersonTotal(db_session_q, apply_num):
    try:
        # 计算并保存人员补贴总金额
        success_total_fund = 0
        fail_total_fund = 0
        success_total_count = 0
        fail_total_count = 0
        month_list = db_session_q.get_tb_date()
        person_info = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num).all()
        for person in person_info:
            # detail_pay_list = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == person.p_ID,
            #                                                          DetailPayInfo.d_apply_num == person.p_c_apply_num,
            #                                                          DetailPayInfo.d_pay_month.in_(month_list)).all()
            # society_total = 0
            # normal_fund = 0
            # old_insur = 0
            # injury_insur = 0
            # unemploy_insur = 0
            # medical_insur = 0
            # birth_insur = 0
            # if len(detail_pay_list) != 0:
            #     for pay in detail_pay_list:
            #         society_total += pay.d_old_insur + pay.d_injury_insur + pay.d_unemploy_insur + pay.d_birth_insur + pay.d_medical_insur + pay.d_normal_fund
            #         normal_fund += pay.d_normal_fund
            #         old_insur += pay.d_old_insur
            #         injury_insur += pay.d_injury_insur
            #         unemploy_insur += pay.d_unemploy_insur
            #         birth_insur += pay.d_birth_insur
            #         medical_insur += pay.d_medical_insur
            #     person.p_old_insur = old_insur
            #     person.p_injury_insur = injury_insur
            #     person.p_unemploy_insur = unemploy_insur
            #     person.p_medical_insur = medical_insur
            #     person.p_birth_insur = birth_insur
            #     person.p_society_total = society_total
            #     person.p_normal_fund = normal_fund
            if person.p_final_list == 1:
                success_total_fund += person.p_society_total
                success_total_count += 1
            elif person.p_final_list == 2:
                fail_total_fund += person.p_society_total
                fail_total_count += 1
        db.session.commit()
        # 查询公司信息和个人信息
        company = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()
        company.c_fail_fund = fail_total_fund
        company.c_fail_count = fail_total_count
        company.c_success_count = success_total_count
        company.c_success_fund = success_total_fund
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()


@bp.route('/api/v1/companyInfo', methods=["GET"])
def get_company_info():
    """
    获取公司详细信息
    :return:
    """
    res = ResMsg()
    # 公司申领编号
    apply_num = request.args.get('apply_num', None)

    if not apply_num:
        res.update(code=-1, msg='字段非法')
        return jsonify(res.data)

    # 查询字段匹配内容
    fields = ToolFunc().static_fields()

    data = {
        # "uiState": -1,
        # "userCompanyData": [],
        # "userAccompanyData": [],
        # "userAttachData": [],
        # "userApprovalProcessData": [],
        # "userHistoryBusinessData": [],
        "companyInfoData": [],
        "apply_num": apply_num
    }

    db_session_q = DBSessionQuery(apply_num=apply_num)

    try:
        executor.submit(calculatePersonTotal, db_session_q, apply_num)

        company_results = db_session_q.get_company_info()
        results = mapping_field(fields=fields, results=company_results)
        data["companyInfoData"] = results
        res.update(data=data)
    except Exception as e:
        logging.error(e)
        db.session.rollback()

    return jsonify(res.data)


@bp.route("/api/v1/calPersonCount", methods=["POST"])
def calPersonCount():
    """计算三个列表人数"""
    reg = ResMsg()
    obj = request.get_json(force=True)
    apply_num = obj.get("apply_num", None)
    if apply_num is None:
        reg.update(msg="查询列表人数失败", code=-1)
        return reg
    data = {"successListCount": db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num,
                                                                    PersonInfo.p_final_list == 1).count(),
            "failListCount": db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num,
                                                                 PersonInfo.p_final_list == 2).count(),
            "preditListCount": db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num,
                                                                   PersonInfo.p_final_list == 0).count()}
    reg.update(data=data)
    return jsonify(reg.data)


@bp.route('/api/v1/approvedList', methods=["POST"])
def get_approval_list():
    """
    获取待审核列表
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    apply_num = obj.get('apply_num', None)  # 申报公司编号
    list_type = obj.get('list_type', None)  # 列表类型：1成功列表 2失败列表 0待审核列表
    page = obj.get('page', dict())
    page_num = int(page.get("pageNum", 1))
    page_size = int(page.get("pageSize", 10))

    # 定义翻页参数
    page = {
        "pageNum": page_num,
        "pageSize": page_size,
        "total": 0,
    }

    res.add_field(name="page", value=page)

    # 判断页数是否为非法字段
    if not apply_num or not list_type or not page_num >= 1 or not page_size >= 0:
        res.update(code=-1, msg='字段非法')
        return jsonify(res.data)
    # 查询字段匹配内容
    fields = ToolFunc().static_fields()
    db_session_q = DBSessionQuery(apply_num=apply_num, list_type=list_type)
    base_query = db_session_q.get_approval_list()

    # 总数
    total = base_query.count()
    results = base_query.slice((page_num - 1) * page_size, page_num * page_size).all()

    data = mapping_field(fields=fields, results=results)

    page["total"] = total
    res.update(data={
        'data': data,
    })
    return jsonify(res.data)


@bp.route('/api/v1/personInfo', methods=["GET"])
def get_person_info():
    """
    获取人员详细信息
    return:
    """
    res = ResMsg()
    # 公司申领编号
    apply_num = request.args.get('apply_num', None)
    id = request.args.get('id', None)
    now_list = request.args.get('now_list', None)
    if not apply_num or not id:
        res.update(code=-1, msg='字段非法')
        return jsonify(res.data)

    # 查询字段匹配内容
    fields = ToolFunc().static_fields()
    data = {
        "companyInfoData": [],  # 公司详情
        "personInfoData": [],  # 人员详情
        "detailPayInfoData": [],  # 具体月份补贴金额信息
        "unemployInfoData": [],  # 失业登记信息
        "hardIdentifyInfoData": [],  # 困难认定信息
        "recordInfoData": [],  # 就业登记信息
        "socialPayInfoData": [],  # 社保缴纳信息
        "businessInfoData": [],  # 商事记录信息
        "degreeInfoData": [],
        "allowanceInfoData": [],
        'CompanyPreditResult': {},  # 企业预审结果
        'PersonPreditResult': {},  # 人员预审结果
        'unemploy_start': None,  # 失业开始日期
        'ID_list': [],
        "xwCompany_list": [],  # 小微企业列表
        'unemploy_end': None,  # 失业结束日期
        'hard_identify_date': None,  # 困难认定日期
        'start_contract_date': None,  # 合同开始日期
        'end_contract_date': None,  # 合同结束日期
        'contract_register_date': None,  # 合同登记日期
        "apply_num": apply_num,
        "company_location": None,  # 企业地址
        "company_person": None,  # 企业法人
        "id": id,
        "file_path_list": [],
        "predit_count": 0
    }
    action = DBSessionAction()
    try:
        db_session_q = DBSessionQuery(apply_num=apply_num, id=id)
        person_list = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num).all()
        person = None
        for p in person_list:
            if p.p_ID == id:
                person = p
            if p.p_final_list == 0 and p.p_ID != id:
                data["predit_count"] += 1
            # 所在人员列表ID
            if now_list and now_list != 'undefined':
                if now_list == '2' and p.p_final_list == 2:
                    data['ID_list'].append(p.p_ID)
                elif now_list == '0' and p.p_final_list == 0:
                    data['ID_list'].append(p.p_ID)
                elif now_list == '1' and p.p_final_list == 1:
                    data['ID_list'].append(p.p_ID)

        # 查询公司信息
        company = db_session_q.get_company_info().first()
        if company is None:
            res.update(code=-1, msg="没有企业信息")
            return jsonify(res.data)
        company_name = company.c_name
        register_num = company.c_register_num

        # 小微企业信息
        if person.p_type == "高校等毕业生":
            xw_list = db.session.query(XwCompanyInfo).filter(XwCompanyInfo.social_num == register_num).all()
            xwCompany_list = []
            for xw in xw_list:
                xwCompany_list.append(xw.to_dict())
            data["xwCompany_list"] = xwCompany_list
        # 企业地址
        data['company_location'] = company.c_search_location
        data['company_person'] = company.c_search_charge

        company_field_list = ["c_register_num", "c_name", "c_apply_num", "c_social_num", "c_size", "c_apply_season",
                              "c_bank", "c_bank_card", "c_charge_name", "c_contact_phone", "c_hard_employ_count",
                              "c_army_count", "c_old_insur", "c_injury_insur", "c_medical_insur",
                              "c_general_post_subsidy", "c_special_fund_count", "c_net_office", "c_unemploy_fund",
                              "c_success_fund", "c_fail_fund", "c_robot_result", "c_detail", "c_search_charge",
                              "c_get_person_state", "c_street_author", "c_street_belong", "c_street_comment", "c_total",
                              "id"]
        data["companyInfoData"] = action.getObjectInfoData(company, company_field_list)

        # 查询个人补贴享受信息
        allowance_list = db.session.query(Allowance_info).filter(Allowance_info.z_ID == id).all()
        for allow in allowance_list:
            data["allowanceInfoData"].append(allow.to_dict())
        # 获取访问IP
        # addr = request.environ.get('HTTP_X_FORWARDED_FOR', None)  # 捕捉访问IP
        addr = SERVER_HOST1  # todo:调试
        if "192.168" in addr:
            pre_url = f"http://{SERVER_HOST2}/zygbt/"
        else:
            pre_url = f"http://{SERVER_HOST1}/zygbt/"

        try:
            file_path_list = eval(person.p_file_path)
            for file in file_path_list:
                path = file.split("/")
                url2 = parse.quote(path[2], encoding='utf-8')
                url = pre_url + path[1] + "/" + url2
                data["file_path_list"].append(url)
        except Exception as e:
            logging.error("没有附件" + str(e))

        person_field_list = ["p_type", "p_ID_type", "p_ID", "p_pass_num", "p_name", "p_sex", "p_social_num",
                             "p_contract_end_date", "p_disabled_num", "p_graduate_type", "p_graduate_date",
                             "p_isprovince", "p_unemploy_insur", "p_birth_insur", "p_normal_fund", "p_reamark",  # 预审结果
                             "p_explain", "p_verify_explain",  # 六个日期
                             "p_end_unemploy_date", "p_start_contract_date", "p_contract_register_date", "p_file_path",
                             "p_social_company_identical", "p_identify_comment", "p_street_comment"]
        data["personInfoData"] = action.getObjectInfoData(person, person_field_list)

        # 获取六个日期
        start_unemploy_date = person.p_start_unemploy_date
        end_unemploy_date = person.p_end_unemploy_date
        hard_identify_date = person.p_hard_identify_date
        start_contract_date = person.p_start_contract_date
        end_contract_date = person.p_end_contract_date
        contract_register_date = person.p_contract_register_date
        # 查询具体月份补贴金额信息
        detailPay_results = db_session_q.get_detailPay_info()
        detail_pay_field_list = [
            "d_pay_month", "d_old_insur", "d_injury_insur",
            "d_unemploy_insur", "d_birth_insur", "d_medical_insur",
            "d_normal_fund", "is_checked", "id"
        ]
        data["detailPayInfoData"] = action.getObjectListData(detailPay_results.all(), detail_pay_field_list)

        try:
            # 查询学历信息
            if person.p_type == "高校等毕业生":
                degree_info = db.session.query(Degree_Info).filter(Degree_Info.card_ID == id).all()
                degree_list = []
                for degree in degree_info:
                    degree_list.append(degree.to_dict())
                data["degreeInfoData"] = degree_list
        except Exception as e:
            logging.error("错误日志：" + str(e))

        # 查询失业登记信息
        unemploy_results = db_session_q.get_unemploy_info()

        end_time = ''
        unemploy_end = ''
        # 失业有效始期

        first_start = True  # 是否第一次新办
        first_end = True  # 是否第一次退出
        for unemploy in unemploy_results:
            if unemploy.e_register_type == '新办' and first_start == True:
                data['unemploy_start'] = unemploy.e_register_date
                end_time = unemploy.e_end_date
                first_start = False
            # 失业有效终期
            if unemploy.e_register_type == '退出' and first_end == True:
                unemploy_end = unemploy.e_register_date
                first_end = False
        if unemploy_end == '' and first_start == False:
            unemploy_end = end_time
        data['unemploy_end'] = unemploy_end
        if start_unemploy_date != '-':
            data['unemploy_start'] = start_unemploy_date
        if end_unemploy_date != '-':
            data['unemploy_end'] = end_unemploy_date

        unemploy_field_list = [
            "e_serial_num", "e_employ_num", "e_ID", "e_name", "e_population", "e_register_num", "e_register_type",
            "e_start_date", "e_end_date", "e_register_date", "e_exist_forward"
        ]

        data["unemployInfoData"] = action.getObjectListData(unemploy_results.all(), unemploy_field_list)

        # 查询困难认定信息
        hardIdentify_results = db_session_q.get_hardIdentify_info()
        if hardIdentify_results.all() != []:
            data['hard_identify_date'] = hardIdentify_results[0].h_identify_date
        if hard_identify_date != '-':
            data['hard_identify_date'] = hard_identify_date
        hardIdentify_field_list = ["h_name", "h_ID", "h_employ_type", "h_apply_date", "h_identify_date", "h_exit_date",
                                   "h_state", "h_identify_way", "h_apply_location"]
        data["hardIdentifyInfoData"] = action.getObjectListData(hardIdentify_results.all(), hardIdentify_field_list)

        # 查询就业登记信息
        record_results = db_session_q.get_record_info()
        for req in record_results.all():
            # 去掉空格
            if req.r_company_name.strip() == company_name.strip():
                data['start_contract_date'] = req.r_contract_start_date.strip()
                if req.r_contract_end_date.strip() == '-':
                    data['end_contract_date'] = None
                else:
                    data['end_contract_date'] = req.r_contract_end_date.strip()
                data['contract_register_date'] = req.r_register_date.strip()
                break
        if start_contract_date != '-':
            data['start_contract_date'] = start_contract_date
        if end_contract_date != '-':
            data['end_contract_date'] = end_contract_date
        if contract_register_date != '-':
            data['contract_register_date'] = contract_register_date
        record_field_list = [
            "r_accept_batch", "r_company_name", "r_ID", "r_name", "r_sex", "r_birth", "r_degree", "r_population",
            "r_location", "r_register_type", "r_contract_start_date", "r_contract_end_date", "r_register_date",
            "r_isapply", "r_date_source"
        ]
        data["recordInfoData"] = action.getObjectListData(record_results.all(), record_field_list)

        # 查询社保缴纳信息
        socialPay_results = db_session_q.get_socialPay_info()
        socialPay_field_list = [
            "s_pay_date", "s_old_base", "s_medical_base", "s_old_insur", "s_unemploy_insur", "s_injury_insur",
            "s_medical_insur", "s_c_old_insur", "s_c_unemploy_insur", "s_c_injury_insur", "s_c_medical_insur",
            "s_c_disease_insur", "s_c_birth_insur", "s_social_num", "s_social_c_name", "s_social_credit_num",
            "s_medical_num", "s_medical_c_num", "s_medical_c_name", "s_medical_credit_num"
        ]
        data["socialPayInfoData"] = action.getObjectListData(socialPay_results.all(), socialPay_field_list)

        # # 查询商事记录信息
        business_results = db_session_q.get_business_info()
        business_field_list = ["b_register_num", "b_credit_num", "b_company", "b_charge_name", "b_ID", "b_main_type",
                               "b_pro_type", "b_date", "b_state", "b_relieve_date"]
        data["businessInfoData"] = action.getObjectListData(business_results.all(), business_field_list)

        # 企业预审结果
        c_detail = eval(company.c_detail)
        company_detail = {}
        company_detail['success'] = c_detail.get('通过原因', [])
        company_detail['fail'] = c_detail.get('不通过原因', [])
        data['CompanyPreditResult'] = {
            'c_robot_result': company.c_robot_result,
            'c_detail': json.dumps(company_detail)
        }
        # 人员预审结果
        p_detail = eval(person.p_detail)
        person_detail = {
            'success': p_detail.get('通过原因', []),
            'fail': p_detail.get('不通过原因', [])
        }

        data['PersonPreditResult'] = {
            'p_robot_result': person.p_robot_result,
            'p_detail': json.dumps(person_detail)
        }
    except Exception as e:
        logging.error("个人详情页面：{}".format(str(e)))

    res.update(data=data)

    return jsonify(res.data)


@bp.route('/api/v1/approvedPersonInfo', methods=["POST"])
def approved_person_info():
    """
    提交审批人申领金额修改信息
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    apply_num = obj.get('apply_num', None)
    id = obj.get('id', None)

    # 审批内容
    contents = obj.get('content', [])
    if not apply_num or not id or not contents:
        res.update(code=-1, data='字段非法')
        return jsonify(res.data)

    person_info = db.session.query(PersonInfo).filter(PersonInfo.p_ID == id,
                                                      PersonInfo.p_c_apply_num == apply_num).first()  # 匹配审批的人
    if not person_info:
        res.update(code=-1, msg='该条记录不存在')
        return jsonify(res.data)
    old_insur_total = 0
    injury_insur_total = 0
    unemploy_insur_total = 0
    birth_insur_total = 0
    medical_insur_total = 0
    normal_fund_total = 0
    try:
        # 遍历多条具体补贴月份金额
        for content in contents:
            pay_month = content.get("pay_month", None)
            old_insur = content.get("old_insur", None)
            injury_insur = content.get("injury_insur", None)
            unemploy_insur = content.get("unemploy_insur", None)
            birth_insur = content.get("birth_insur", None)
            medical_insur = content.get("medical_insur", None)
            normal_fund = float(content.get("normal_fund", None))
            is_checked = content.get("is_checked", None)
            if old_insur is None or injury_insur is None or unemploy_insur is None or birth_insur is None or medical_insur is None or normal_fund is None:
                res.update(code=-1, msg='审批人申领金额字段出错')
                logger.error('审批人申领金额字段出错：{}-{}'.format(apply_num, id))
                return jsonify(res.data)
            # 查看是否有该月份
            detail_pay_info = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == id,
                                                                     DetailPayInfo.d_apply_num == apply_num,
                                                                     DetailPayInfo.d_pay_month == pay_month).first()
            if not detail_pay_info:
                nullDetail_info = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == id,
                                                                         DetailPayInfo.d_apply_num == apply_num,
                                                                         DetailPayInfo.d_pay_month == None).first()

                if nullDetail_info:
                    # pay_info = DetailPayInfo()
                    nullDetail_info.d_pay_month = pay_month
                    nullDetail_info.d_old_insur = old_insur
                    nullDetail_info.d_injury_insur = injury_insur
                    nullDetail_info.d_unemploy_insur = unemploy_insur
                    nullDetail_info.d_birth_insur = birth_insur
                    nullDetail_info.d_medical_insur = medical_insur
                    nullDetail_info.d_normal_fund = normal_fund
                    nullDetail_info.is_checked = is_checked
                    person_info.p_medical_check = False  # 重新抓取
                    # db.session.add(pay_info)
                    db.session.commit()
                else:
                    pay_info = DetailPayInfo()
                    pay_info.d_apply_num = apply_num
                    pay_info.d_ID = id
                    pay_info.d_pay_month = pay_month
                    pay_info.d_old_insur = old_insur
                    pay_info.d_injury_insur = injury_insur
                    pay_info.d_unemploy_insur = unemploy_insur
                    pay_info.d_birth_insur = birth_insur
                    pay_info.d_medical_insur = medical_insur
                    pay_info.d_normal_fund = normal_fund
                    pay_info.is_checked = is_checked
                    person_info.p_medical_check = False  # 人员重新抓取医保数据
                    db.session.add(pay_info)
                    db.session.commit()

                # return jsonify(res.data)
            detail_pay_info = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == id,
                                                                     DetailPayInfo.d_apply_num == apply_num,
                                                                     DetailPayInfo.d_pay_month == pay_month).first()
            old_insur_total += old_insur
            injury_insur_total += injury_insur
            unemploy_insur_total += unemploy_insur
            birth_insur_total += birth_insur
            medical_insur_total += medical_insur
            normal_fund_total += normal_fund
            try:
                detail_pay_info.d_old_insur = old_insur
                detail_pay_info.d_injury_insur = injury_insur
                detail_pay_info.d_unemploy_insur = unemploy_insur
                detail_pay_info.d_birth_insur = birth_insur
                detail_pay_info.d_medical_insur = medical_insur
                detail_pay_info.d_normal_fund = normal_fund
                detail_pay_info.is_checked = is_checked
                db.session.commit()
            except Exception as e:
                logger.exception(e)
                db.session.rollback()
                logger.error('数据存储失败：{}-{}'.format(apply_num, id))
                res.update(code=-1, msg='审批人具体月份补贴金额信息提交失败')
                return jsonify(res.data)
    except Exception as e:
        logging.error("approvedPersonInfo:" + str(e))
        res.update(code=-1, msg='接口出现问题')
        return jsonify(res.data)

    try:
        person_info.p_old_insur = old_insur_total
        person_info.p_injury_insur = injury_insur_total
        person_info.p_unemploy_insur = unemploy_insur_total
        person_info.p_birth_insur = birth_insur_total
        person_info.p_medical_insur = medical_insur_total
        person_info.p_normal_fund = normal_fund_total
        person_info.p_society_total = old_insur_total + injury_insur_total + unemploy_insur_total + birth_insur_total + medical_insur_total
        db.session.add(person_info)
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        db.session.rollback()
        logger.error('数据存储失败：{}-{}'.format(apply_num, id))
        res.update(code=-1, msg='审批人申领金额提交失败')
        return jsonify(res.data)
    return jsonify(res.data)


@bp.route('/api/v1/approvedPerson', methods=["POST"])
def approved_person():
    """
    提交审批内容
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    apply_num = obj.get('apply_num', None)
    id = obj.get('id', None)
    roleName = obj.get("roleName", None)

    account_type = getAccountAuthority(roleName)
    if account_type == 0:
        pass
    elif account_type == 1:
        pass
    else:
        res.update(code=-1, msg="请用街道账号或者区级账号登录")
        return jsonify(res.data)
    # 审批内容
    content = obj.get('content', None)
    if not apply_num or not id or not content:
        res.update(code=-1, data='字段非法')
        return jsonify(res.data)

    company_info = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()  # 匹配公司信息，更新状态
    # 审核未完成，未回填，查出有问题，后端解决，
    # 查询是否数据有问题
    recatch_record = db.session.query(RecatchDataInfo).filter(RecatchDataInfo.apply_num == apply_num,
                                                              RecatchDataInfo.state == False).first()
    if recatch_record:
        res.update(msg='企业数据有异常，请审核下一家企业', code=-1)
        return jsonify(res.data)
    # 查询当前人是否在预处理列表
    person_info = db.session.query(PersonInfo).filter(PersonInfo.p_ID == id,
                                                      PersonInfo.p_c_apply_num == apply_num).first()  # 匹配审批的人

    verify_explain = person_info.p_verify_explain
    if not person_info:
        res.update(code=-1, msg='该条记录不存在')
        return jsonify(res.data)
    approval_result = content.get("approval_result", None)
    approval_person = content.get("approval_person", None)
    approval_comment = content.get("approval_comment", None)
    approval_area = content.get("approval_area", None)
    approval_time = content.get("approval_time", None)
    if approval_result == None or not approval_person:
        res.update(code=-1, msg='审核结果字段出错')
        logger.error('审核结果字段出错：{}-{}'.format(apply_num, id))
        return jsonify(res.data)
    if approval_result and "不允许" in verify_explain:
        res.update(code=-1, msg="不允许审核通过")
        return jsonify(res.data)
    if not approval_result and not approval_comment:
        res.update(code=-1, msg="审核不通过需要添加原因")
        return jsonify(res.data)

    # 人员审核
    if account_type == 0:
        if person_info.p_person_result is not None:
            res.update(code=-1, msg="区级人员已审核，无权限审核")
            return jsonify(res.data)
        # 街道
        person_info.p_street_result = approval_result
        person_info.p_street_author = approval_person
        person_info.p_street_comment = approval_comment
    else:
        # if person_info.p_street_result is None:
        #     res.update(code=-1, msg="街道还未审核该申报人员")
        #     return jsonify(res.data)
        person_info.p_person_result = approval_result
        person_info.p_identify_person = approval_person
        person_info.p_identify_comment = approval_comment
    person_info.p_identify_date = approval_time
    person_info.p_final_list = 1 if int(approval_result) == 1 else 2

    # 如果补贴金额都为0不可以审核通过
    detail_info = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_apply_num == apply_num,
                                                         DetailPayInfo.d_ID == id,
                                                         DetailPayInfo.is_checked == True).all()

    fail_month_list = []
    fund_doubt = False
    for detail in detail_info:
        total = 0
        total += float(detail.d_old_insur)
        total += float(detail.d_injury_insur)
        total += float(detail.d_birth_insur)
        total += float(detail.d_unemploy_insur)
        total += float(detail.d_medical_insur)
        if float(detail.d_old_insur) == 0 or float(detail.d_medical_insur) == 0:
            fund_doubt = True

        if total == 0 and int(approval_result) == 1:
            fail_month_list.append(detail.d_pay_month)

    if int(approval_result) == 1 and (len(fail_month_list) != 0 or len(detail_info) == 0 or fund_doubt is True):
        res.update(code=-1, msg=f"{'、'.join(fail_month_list)}补贴金额为0，不能审核通过")
        return jsonify(res.data)
    record_info = UpdateRecordInfo()
    # todo:查看企业是否需要有回填记录
    back_exist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
                                                           Back_record_info.br_state == '等待',
                                                           Back_record_info.br_person_ID == '',
                                                           Back_record_info.br_type == account_type,
                                                           or_(Back_record_info.br_fill_back == 0,
                                                               Back_record_info.br_fill_back == 1)
                                                           ).all()
    # todo:防止重复审核同一个人
    person_back_exist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
                                                                  Back_record_info.br_person_ID == person_info.p_ID,
                                                                  Back_record_info.br_type == account_type,
                                                                  Back_record_info.br_state == '等待').all()
    try:
        # 如果有该企业的回填记录
        if back_exist != []:
            if person_back_exist == []:
                # todo:添加回填回退记录
                back = db.session.query(Back_record_info).filter(Back_record_info.br_state == '等待',
                                                                 Back_record_info.br_apply_num == apply_num,
                                                                 Back_record_info.br_person_ID == '',
                                                                 Back_record_info.br_type == account_type,
                                                                 or_(Back_record_info.br_fill_back == 0,
                                                                     Back_record_info.br_fill_back == 1)
                                                                 ).first()
                back_record_info = Back_record_info()
                back_record_info.br_apply_num = apply_num
                back_record_info.br_company = company_info.c_name
                back_record_info.br_apply_season = company_info.c_apply_season
                back_record_info.br_person_ID = person_info.p_ID
                back_record_info.br_person_name = person_info.p_name
                back_record_info.br_fill_back = 1
                back_record_info.br_state = '等待'
                back_record_info.br_type = account_type
                back_record_info.br_identify_person = approval_person
                back_record_info.br_cid = back.id
                db.session.add(back_record_info)
        else:
            # todo:添加企业回填记录
            back_company_info = Back_record_info()
            back_company_info.br_apply_num = apply_num
            back_company_info.br_company = company_info.c_name
            back_company_info.br_apply_season = company_info.c_apply_season
            back_company_info.br_fill_back = 0
            back_company_info.br_state = '等待'
            back_company_info.br_type = account_type
            back_company_info.br_identify_person = approval_person
            db.session.add(back_company_info)
            db.session.commit()

            # todo:添加个人回填回退记录
            if person_back_exist == []:
                back = db.session.query(Back_record_info).filter(Back_record_info.br_state == '等待',
                                                                 Back_record_info.br_apply_num == apply_num,
                                                                 Back_record_info.br_type == account_type,
                                                                 Back_record_info.br_person_ID == '').first()
                back_record_info = Back_record_info()
                back_record_info.br_apply_num = apply_num
                back_record_info.br_company = company_info.c_name
                back_record_info.br_apply_season = company_info.c_apply_season
                back_record_info.br_person_ID = person_info.p_ID
                back_record_info.br_person_name = person_info.p_name
                back_record_info.br_fill_back = 1
                back_record_info.br_state = '等待'
                back_record_info.br_type = account_type
                back_record_info.br_identify_person = approval_person
                back_record_info.br_cid = back.id
                db.session.add(back_record_info)
                db.session.commit()
            else:
                res.update(code=-1, msg='该人员已审核')
                return jsonify(res.data)

        # 添加审核记录
        record_info.u_ID = id
        record_info.u_result = approval_result
        record_info.u_new_comment = approval_comment
        record_info.u_name = approval_person
        db.session.add(record_info)

        '''计算该公司成功人数'''
        success_people = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num,
                                                             PersonInfo.p_final_list == 1)
        company_info.c_success_count = success_people.count()
        '''计算成功金额'''
        success_fund = 0
        for p in success_people:
            success_fund += p.p_society_total
        company_info.c_success_fund = success_fund
        '''计算该公司失败人数'''
        fail_people = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num,
                                                          PersonInfo.p_final_list == 0)
        company_info.c_fail_count = fail_people.count()
        '''计算失败金额'''
        fail_fund = 0
        for p in fail_people:
            fail_fund += p.p_society_total
        company_info.c_fail_fund = fail_fund
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        db.session.rollback()
        logger.error('数据存储失败：{}-{}'.format(apply_num, id))
        res.update(code=-1, msg='公司审核数据提交失败')

    return jsonify(res.data)


@bp.route('/api/v1/approvedCompany', methods=["POST"])
def approved_company():
    """
    提交审批公司内容
    :return:
    """
    res = ResMsg()
    obj = request.get_json(force=True)
    apply_num = obj.get('apply_num', None)  # 列表类型
    roleName = obj.get("roleName", None)

    account_type = getAccountAuthority(roleName)
    if account_type == 0:
        pass
    elif account_type == 1:
        pass
    else:
        res.update(code=-1, msg="请用街道账号或者区级账号登录")
        return jsonify(res.data)
    # 审批内容
    content = obj.get('content', None)
    if not apply_num or not content:
        res.update(code=-1, data='字段非法')
        return jsonify(res.data)

    # 查询当前公司是否已审核
    is_exist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num.in_(apply_num),
                                                         Back_record_info.br_fill_back == 1,
                                                         Back_record_info.br_state == '等待',
                                                         Back_record_info.br_person_ID == '',
                                                         Back_record_info.br_type == account_type,
                                                         Back_record_info.br_person_name == '').all()
    if is_exist != []:
        res.update(code=-1, msg='该企业或其中一家企业已审核，请勿重复提交')
        return jsonify(res.data)

    approval_result = content.get("approval_result", None)
    approval_person = content.get("approval_person", None)
    approval_comment = content.get("approval_comment", None)

    if approval_result == None or not approval_person:
        res.update(code=-1, msg='审核结果字段出错')
        logger.error('审核结果字段出错：{}-{}'.format(apply_num, id))
        return jsonify(res.data)
    apply_num = tuple(apply_num)
    # 多个企业同时审核
    company_info = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num.in_(apply_num)).all()  # 匹配公司信息，更新状态

    try:
        for company in company_info:
            recatch_record = db.session.query(RecatchDataInfo).filter(RecatchDataInfo.apply_num == company.c_apply_num,
                                                                      RecatchDataInfo.state == False).first()
            if recatch_record:
                res.update(msg='企业数据有异常，请审核下一家企业', code=-1)
                return jsonify(res.data)
            # 校验是否有人员在预审列表
            have_unreviewed_person = db.session.query(PersonInfo).filter(
                PersonInfo.p_c_apply_num == company.c_apply_num).all()
            for i in have_unreviewed_person:
                if int(i.p_final_list) == 0:  # 在预审列表
                    res.update(code=-1, msg="还有人员在预审列表,企业不可审核")
                    return jsonify(res.data)
            if account_type == 0:
                if company.c_person_result is not None:
                    res.update(code=-1, msg="区级人员已审核该企业")
                    return jsonify(res.data)
                company.c_street_result = approval_result
                company.c_street_author = approval_person
                company.c_street_comment = approval_comment
            else:
                # if company.c_street_result is None:
                #     res.update(code=-1, msg="街道还未审核该企业")
                #     return jsonify(res.data)
                company.c_person_result = approval_result
                company.c_identify_person = approval_person
                company.c_identify_comment = approval_comment
            # todo:查询是否有该企业的回填记录
            back_company = db.session.query(Back_record_info).filter(
                Back_record_info.br_apply_num == company.c_apply_num,
                Back_record_info.br_type == account_type,
                Back_record_info.br_fill_back == 0).all()
            a_num = company.c_apply_num
            a_season = company.c_apply_season
            name = company.c_name
            if back_company == []:
                # 没有该记录
                back_info = Back_record_info()
                back_info.br_apply_season = a_season
                back_info.br_apply_num = a_num
                back_info.br_company = name
                back_info.br_fill_back = 1
                back_info.br_state = '等待'
                back_info.br_type = account_type
                back_info.br_identify_person = approval_person
                db.session.add(back_info)
                db.session.commit()

            else:
                # 修改回填回退记录
                back_info = back_company[0]
                back_info.br_apply_season = a_season
                back_info.br_apply_num = a_num
                back_info.br_company = name
                back_info.br_fill_back = 1
                back_info.br_state = '等待'
                back_info.br_type = account_type
                back_info.br_identify_person = approval_person
                db.session.add(back_info)
                db.session.commit()
            company_back_info = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == a_num,
                                                                          Back_record_info.br_person_ID == "",
                                                                          Back_record_info.br_state == "等待",
                                                                          Back_record_info.br_type == account_type,
                                                                          Back_record_info.br_fill_back == 1).first()
            # 添加已经审核过的人
            person_list = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == a_num).all()
            final_list_result = [2, 1, 0]
            if person_list:
                for person in person_list:
                    # 添加回填记录
                    ID = person.p_ID
                    cid = company_back_info.id
                    isExist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == a_num,
                                                                        Back_record_info.br_person_ID == ID,
                                                                        Back_record_info.br_state == "等待",
                                                                        Back_record_info.br_fill_back == 1,
                                                                        Back_record_info.br_type == account_type,
                                                                        Back_record_info.br_cid == cid).first()
                    if isExist:
                        continue
                    else:
                        person_back = Back_record_info()
                        person_back.br_apply_season = a_season
                        person_back.br_apply_num = a_num
                        person_back.br_company = company_back_info.br_company
                        person_back.br_person_ID = person.p_ID
                        person_back.br_person_name = person.p_name
                        person_back.br_fill_back = 1
                        person_back.br_state = "等待"
                        person_back.br_type = account_type
                        person_back.br_cid = int(cid)
                        person_back.br_identify_person = approval_person
                        db.session.add(person_back)
                    # 添加审核记录
                    if account_type == 0:  # 街道审核
                        if person.p_street_result is None:
                            db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == a_num,
                                                                PersonInfo.p_ID == ID).update(
                                {"p_street_author": approval_person, "p_street_result": final_list_result[person.p_final_list],
                                 "p_street_comment": approval_comment})
                    elif account_type == 1:  # 区级审核
                        if person.p_person_result is None:
                            db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == a_num,
                                                                PersonInfo.p_ID == ID).update(
                                {"p_identify_person": approval_person, "p_person_result": final_list_result[person.p_final_list],
                                 "p_identify_comment": person.p_street_comment})
                    db.session.commit()
                db.session.commit()

        db.session.commit()
    except Exception as e:
        logger.exception(e)
        db.session.rollback()
        logger.error('数据存储失败：{}-{}'.format(apply_num, id))
        res.update(code=-1, msg='公司审核数据提交失败')

    return jsonify(res.data)


@bp.route('/api/v1/checkRecord', methods=["GET", ])
def get_record_info():
    """
    获取审核记录信息
    :return:
    """
    res = ResMsg()
    # 人员ID
    id = request.args.get('id', None)

    if not id:
        res.update(code=-1, msg='字段非法')
        return jsonify(res.data)

    # 查询字段匹配内容
    fields = ToolFunc().static_fields()

    data = {
        "recordInfoData": [],
        "id": id
    }
    db_session_q = DBSessionQuery(id=id)

    # 查询审核记录信息
    record_results = db_session_q.get_update_record_info()
    results = mapping_field(fields=fields, results=record_results)
    data["recordInfoData"] = results

    res.update(data=data)

    return jsonify(res.data)


@bp.route("/api/v1/BackRecord", methods=['GET', ])
def back_record():
    """展示回填回退表"""
    res = ResMsg()
    page_num = int(request.args.get("pageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    apply_num = request.args.get('br_apply_num', None)
    apply_season = request.args.get('br_apply_season', None)
    company = request.args.get('br_company', None)
    identify_person = request.args.get('br_identify_person', None)
    state = request.args.get('br_state', None)
    street_belong = request.args.get("street_belong", None)
    roleName = request.args.get("roleName", None)
    # 定义翻页参数
    page = {
        "pageNum": page_num,
        "pageSize": page_size,
        "total": 0,
    }
    res.add_field(name="page", value=page)
    # 查询字段匹配内容
    fields = ToolFunc().static_fields()
    # 查询回填回退记录表
    back_info = DBSessionQuery().get_back_record_info()
    # 申领季度
    if apply_season and apply_season != 'undefined':
        back_info = back_info.filter(Back_record_info.br_apply_season == apply_season)

    # 公司名称
    if company and company != 'undefined':
        back_info = back_info.filter(Back_record_info.br_company.like('%' + company + '%'))

    # 申领编号
    if apply_num and apply_num != 'undefined':
        back_info = back_info.filter(Back_record_info.br_apply_num == apply_num)
    # 审核人
    if identify_person and identify_person != 'undefined':
        back_info = back_info.filter(Back_record_info.br_identify_person == identify_person)

    # 审核状态
    if state and state != 'undefined':
        back_info = back_info.filter(Back_record_info.br_state == state)

    # 权限筛选
    if roleName and roleName != 'undefined':
        back_info = back_info.filter(CompanyInfo.c_street_belong.like("%" + roleName + "%"))

    # 街道筛选
    if street_belong and street_belong != 'undefined':
        back_info = back_info.filter(CompanyInfo.c_street_belong.like("%" + street_belong + "%"))

    back_info = back_info.filter(Back_record_info.br_person_name == '', Back_record_info.br_person_ID == '')
    # 总数
    total = back_info.count()
    results = back_info.slice((int(page_num) - 1) * int(page_size), int(page_num) * int(page_size)).all()
    data = mapping_field(fields=fields, results=results)

    page["total"] = total
    res.update(data={
        'data': data,
    })
    res.update(data=data)
    return jsonify(res.data)


@bp.route('/api/v1/companyRollback', methods=['get', ])
def company_rollback():
    """企业回退"""
    res = ResMsg()
    apply_num = request.args.get('apply_num', None)
    approval_name = request.args.get('approval_name', None)
    roleName = request.args.get("roleName", None)
    account_type = getAccountAuthority(roleName)
    if account_type == 0:
        pass
    elif account_type == 1:
        pass
    else:
        res.update(code=-1, msg="请用街道账号或者区级账号登录")
        return jsonify(res.data)
    company = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()

    # 区级人员审核完后，街道人员不可以回退
    if company.c_person_result is not None and account_type == 0:
        res.update(code=-1, msg="区级人员已审核，街道人员无权限回退")
        return jsonify(res.data)
    apply_season = company.c_apply_season
    name = company.c_name
    back_company_exist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
                                                                   Back_record_info.br_fill_back == 2,
                                                                   Back_record_info.br_type == account_type,
                                                                   Back_record_info.br_state == '等待').all()
    # 企业回填等待中回退
    back_company_exist1 = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
                                                                    Back_record_info.br_fill_back == 1,
                                                                    Back_record_info.br_type == account_type,
                                                                    Back_record_info.br_state == '等待').all()

    try:
        if back_company_exist1:
            for record in back_company_exist1:
                record.br_state = "失败"
                record.br_detail = "审核异常立即回退"
            if account_type == 0:
                company.c_street_result = None
                company.c_street_author = None
            else:
                company.c_person_result = None
                company.c_identify_person = None
            db.session.commit()
        else:
            if not back_company_exist:
                back_info = Back_record_info()
                back_info.br_apply_season = apply_season
                back_info.br_apply_num = apply_num
                back_info.br_company = name
                back_info.br_fill_back = 2
                back_info.br_type = account_type
                back_info.br_state = '等待'
                back_info.br_identify_person = approval_name
                for record in back_company_exist1:
                    record.br_state = "失败"
                    record.br_detail = "审核异常立即回退"
                if account_type == 0:
                    company.c_street_result = None
                    company.c_street_author = None
                else:
                    company.c_person_result = None
                    company.c_identify_person = None
                db.session.add(back_info)
                db.session.commit()
            else:
                res.update(code=-1, msg='该企业已在回退中')
                return jsonify(res.data)
    except Exception as e:
        logger.exception(e)
        db.session.rollback()
        logger.error('数据存储失败：{}-{}'.format(apply_num, name))
        res.update(code=-1, msg='公司回退数据提交失败')
    return jsonify(res.data)


def switch_date(date_string):
    date = date_string.split('-')
    if len(date) == 3:
        new = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        return new
    else:
        return None


#
# @bp.route('/api/v1/approval_download', methods=['GET'])
# def approval_download():
#     """导出报表"""
#     res = ResMsg()
#     apply_season = request.values.get('apply_season', None)
#     identify_person = request.values.get('identify_person', None)
#     start_date = request.values.get('start_date', None)
#     end_state = request.values.get('end_state', None)
#
#     path = u'/usr/local/lib/file/zygbt.xlsx'
#     workbook = xw.Workbook(path)
#     worksheet = workbook.add_worksheet('招用工补贴')
#     # 表头
#     head_title = workbook.add_format({
#         'align': "center",
#         "valign": 'vcenter',
#         "bold": True,
#         "font_size": 20
#     })
#     head2_title = workbook.add_format({
#         'align': "center",
#         "valign": 'vcenter',
#         "bold": True,
#         "font_size": 12
#     })
#     style_title = workbook.add_format({
#         "align": "center",
#         "valign": "vcenter",
#         "bold": False,
#         "font_size": 12,
#         "text_wrap": 1
#     })
#     # todo：固定表头格式
#     worksheet.merge_range('A1:V1', u'白云区2021-1季度招用工补贴核查情况表', head_title)
#     worksheet.merge_range('A2:A4', u'序号', head2_title)
#     worksheet.merge_range('B2:B4', u'企业名称', head2_title)
#     worksheet.merge_range('C2:C4', u'统一社会信用代码或注册号', head2_title)
#     worksheet.merge_range('D2:D4', u'是否为小微企业', head2_title)
#     worksheet.merge_range('E2:E4', u'所属区域', head2_title)
#     worksheet.merge_range('F2:F4', u'是否属劳务派遣单位', head2_title)
#     worksheet.merge_range('G2:Q2', u'个人资料', head2_title)
#     worksheet.merge_range('G3:G4', u'姓名', head2_title)
#     worksheet.merge_range('H3:H4', u'身份证号', head2_title)
#     worksheet.merge_range('I3:I4', u'人员类别', head2_title)
#     worksheet.merge_range('J3:J4', u'合同起止日期', head2_title)
#     worksheet.merge_range('K3:K4', u'毕业时间', head2_title)
#     worksheet.merge_range('L3:L4', u'是否为毕业2年内高校毕业生', head2_title)
#     worksheet.merge_range('M3:M4', u'失业登记日期', head2_title)
#     worksheet.merge_range('N3:N4', u'就业困难认定日期', head2_title)
#     worksheet.merge_range('O3:O4', u'就业登记起止日期', head2_title)
#     worksheet.merge_range('P3:P4', u'就业困难认定日期/失业登记日期是否早于就业登记日期', head2_title)
#     worksheet.merge_range('Q3:Q4', u'本季度是否有缴纳社保', head2_title)
#     worksheet.merge_range('R2:R4', u'符合补贴标准', head2_title)
#     worksheet.merge_range('S2:S4', u'补贴金额（元）', head2_title)
#     worksheet.merge_range('T2:T4', u'备注', head2_title)
#     worksheet.merge_range('U2:U4', u'审核结果', head2_title)
#     worksheet.merge_range('V2:V4', u'审核人', head2_title)
#     # 台账内容
#     company_obj = DBSessionQuery().getDownLoadExcelData()
#     if identify_person and identify_person != 'undefined':
#         company_obj = company_obj.filter(CompanyInfo.c_identify_person == identify_person)
#     if apply_season and apply_season != 'undefined':
#         company_obj = company_obj.filter(CompanyInfo.c_apply_season == apply_season)
#     num = 0
#     company_obj = company_obj.all()
#     logging.error("审核企业一共有：" + str(len(company_obj)))
#     try:
#         for company in company_obj:
#             xw_company = ''  # 是否为小微企业
#             belong_area = company.c_search_location  # 所属区域
#             lw_company = ''  # 是否属劳务派遣单位
#             # 查询该企业的人员
#             c_apply_num = company.c_apply_num  # 申报年季
#             person_list = db.session.query(PersonInfo.p_start_unemploy_date,
#                                            PersonInfo.p_end_unemploy_date,
#                                            PersonInfo.p_hard_identify_date,
#                                            PersonInfo.p_start_contract_date,
#                                            PersonInfo.p_end_contract_date,
#                                            PersonInfo.p_contract_register_date,
#                                            PersonInfo.p_name,
#                                            PersonInfo.p_ID,
#                                            PersonInfo.p_type,
#                                            PersonInfo.p_contract_start_date,
#                                            PersonInfo.p_contract_end_date,
#                                            PersonInfo.p_graduate_date,
#                                            PersonInfo.p_isgraduate,
#                                            PersonInfo.p_c_apply_num,
#                                            PersonInfo.p_society_total,
#                                            PersonInfo.p_identify_comment,
#                                            PersonInfo.p_person_result).filter(
#                 PersonInfo.p_c_apply_num == c_apply_num).all()
#             if person_list != []:
#                 for person in person_list:
#                     text = [str(num), ]
#                     person_name = person.p_name  # 姓名
#                     person_ID = person.p_ID  # 证件号码
#                     person_type = person.p_type  # 人员类别
#                     employ_date = person.p_contract_start_date + '至' + person.p_contract_end_date  # 合同起止日期
#                     graduate = person.p_graduate_date  # 毕业时间
#                     if person.p_isgraduate == True:
#                         isgraduate = u'是'  # 是否为毕业2年内高校毕业生
#                     elif person.p_isgraduate == False:
#                         isgraduate = u'否'
#                     else:
#                         isgraduate = ''
#
#                     # todo:失业登记查询
#
#                     if person.p_start_unemploy_date != '-' and person.p_end_unemploy_date != '-':
#                         unemploy_date = person.p_start_unemploy_date + '至' + person.p_end_unemploy_date
#                         unemploy_start = person.p_start_unemploy_date
#                     else:
#                         unemploy_info = db.session.query(UnemployInfo).filter(UnemployInfo.e_ID == person_ID).all()
#                         end_time = ''
#                         unemploy_start = ''
#                         unemploy_end = ''
#                         # 失业有效始期
#                         first_start = True  # 是否第一次新办
#                         first_end = True  # 是否第一次退出
#                         for unemploy in unemploy_info:
#                             if unemploy.e_register_type == '新办' and first_start == True:
#                                 unemploy_start = unemploy.e_register_date
#                                 end_time = unemploy.e_end_date
#                                 first_start = False
#                             # 失业有效终期
#                             if unemploy.e_register_type == '退出' and first_end == True:
#                                 unemploy_end = unemploy.e_register_date
#                                 first_end = False
#                         if unemploy_end == '' and first_start == False:
#                             unemploy_end = end_time
#                         unemploy_end = unemploy_end
#                         unemploy_date = unemploy_start + '至' + unemploy_end  # 失业登记日期
#
#                     # todo:就业困难认定
#                     if person.p_hard_identify_date != '-':
#                         unemploy_identify_date = person.p_hard_identify_date
#                     else:
#                         hard_info = db.session.query(HardIdentifyInfo).filter(HardIdentifyInfo.h_ID == person_ID).all()
#                         if hard_info != []:
#                             unemploy_identify_date = hard_info[0].h_identify_date  # 就业困难认定日期
#                         else:
#                             unemploy_identify_date = ''
#
#                     # todo:就业登记起止日期
#
#                     if person.p_start_contract_date != '-':
#                         record_date = person.p_start_contract_date + '至' + person.p_end_contract_date
#                         record_register_date = person.p_contract_register_date
#                     else:
#                         record_date = ''
#                         record_register_date = ''
#                         business_list = db.session.query(RecordInfo).filter(RecordInfo.r_ID == person_ID).all()
#                         for business in business_list:
#                             if business.r_company_name == company.c_name:
#                                 record_date = business.r_contract_start_date + '至' + business.r_contract_end_date  # 就业登记起止日期
#                                 record_register_date = business.r_register_date
#                                 break
#
#                     # todo:判断时间是否符合要求
#                     unemploy_register = switch_date(unemploy_start)  # 失业登记时间
#                     hard_date = switch_date(unemploy_identify_date)  # 就业困难认定时间
#                     record_register_date = switch_date(record_register_date)  # 就业登记日期
#                     result_state = ''
#                     if record_register_date != None and hard_date != None and unemploy_register != None:
#                         if record_register_date >= hard_date and record_register_date >= unemploy_register:
#                             result_state = '是'  # 就业困难认定日期/失业登记日期是否早于就业登记日期
#                         else:
#                             result_state = '否'
#                     # 本季度是否有缴纳社保
#                     society = db.session.query(SocialPayInfo.s_pay_date).filter(SocialPayInfo.s_ID == person_ID,
#                                                                                 SocialPayInfo.s_pay_date.in_(
#                                                                                     DBSessionQuery(
#                                                                                         apply_num=person.p_c_apply_num).get_tb_date())).all()
#                     if len(society) > 0:
#                         isPaysociety = '是'
#                     else:
#                         isPaysociety = '否'
#                     society_success = ''  # 符合补贴标准
#                     society_total = person.p_society_total  # 补贴金额
#                     explain = person.p_identify_comment  # 备注
#                     if person.p_person_result == True:
#                         person_result = '通过'  # 审核结果
#                     else:
#                         person_result = '不通过'
#                     text = text + [company.c_name, company.c_register_num, xw_company,
#                                    belong_area, lw_company, person_name, person_ID, person_type, employ_date,
#                                    graduate, isgraduate, unemploy_date, unemploy_identify_date,
#                                    record_date, result_state, isPaysociety, society_success,
#                                    society_total, explain, person_result, company.c_identify_person]
#                     worksheet.write_row(num + 4, 0, text, cell_format=style_title)
#
#                     num += 1
#             else:
#                 text = []
#     except Exception as e:
#         logging.error("错误信息：" + str(e))
#     workbook.close()
#     return jsonify(res.data)


@bp.route('/api/v1/save_hard_personinfo', methods=['post'])
def save_hard_personinfo():
    """保存客户修改的人员信息"""
    reg = ResMsg()
    obj = request.get_json(force=True)
    apply_num = obj.get('apply_num', '')
    person_ID = obj.get('person_ID', '')
    start_unemploy_date = str(obj.get('start_unemploy_date', '-'))
    end_unemploy_date = str(obj.get('end_unemploy_date', '-'))
    hard_identify_date = str(obj.get('hard_identify_date', '-'))
    start_contract_date = str(obj.get('start_contract_date', '-'))
    end_contract_date = str(obj.get('end_contract_date', '-'))
    contract_register_date = str(obj.get('contract_register_date', '-'))
    if start_unemploy_date != '-':
        start_unemploy_date = start_unemploy_date[:10]
    if end_unemploy_date != '-':
        end_unemploy_date = end_unemploy_date[:10]
    if hard_identify_date != '-':
        hard_identify_date = hard_identify_date[:10]
    if start_contract_date != '-':
        start_contract_date = start_contract_date[:10]
    if end_contract_date != '-':
        end_contract_date = end_contract_date[:10]
    if contract_register_date != '-':
        contract_register_date = contract_register_date[:10]
    if start_unemploy_date == 'None':
        start_unemploy_date = '-'
    if end_unemploy_date == 'None':
        end_unemploy_date = '-'
    if hard_identify_date == 'None':
        hard_identify_date = '-'
    if start_contract_date == 'None':
        start_contract_date = '-'
    if end_contract_date == 'None':
        end_contract_date = '-'
    if contract_register_date == 'None':
        contract_register_date = '-'
    person = db.session.query(PersonInfo).filter(PersonInfo.p_ID == person_ID,
                                                 PersonInfo.p_c_apply_num == apply_num).first()
    try:
        # todo:保存客户提交的修改日期
        person.p_start_unemploy_date = start_unemploy_date
        person.p_end_unemploy_date = end_unemploy_date
        person.p_hard_identify_date = hard_identify_date
        person.p_start_contract_date = start_contract_date
        person.p_end_contract_date = end_contract_date
        person.p_contract_register_date = contract_register_date
        db.session.add(person)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
    return jsonify(reg.data)


@bp.route('/api/v1/export_task', methods=['get'])
def export_task():
    """导出任务报表"""

    # company_list = db.session.query(CompanyInfo).limit(100).all()
    company_list = db.session.query(CompanyInfo).filter(CompanyInfo.isIdentify == 1,
                                                        CompanyInfo.c_apply_num.like('%2021-3%')).order_by(
        CompanyInfo.c_isseason).all()
    list_all = []
    for company in company_list:
        list_ = [company.c_apply_season,
                 company.c_name,
                 company.c_extra_social_count,
                 company.c_hard_employ_count,
                 company.c_graduate_count,
                 company.c_army_count,
                 company.c_season_add_count,
                 company.c_apply_num,
                 "是" if company.c_net_office else "否",
                 "是" if company.c_isprovince else "否",
                 "是" if company.c_isseason else "否",
                 company.c_affect_person_count,
                 company.c_poor_count,
                 company.c_total,
                 company.c_old_insur,
                 company.c_unemploy_insur,
                 company.c_injury_insur,
                 company.c_birth_insur,
                 company.c_medical_insur,
                 company.c_social_total,
                 company.c_general_post_subsidy,
                 ]
        list_all.append(list_)
    list_title = ['申报年季',
                  '单位名称',
                  '企业参保人数',
                  '就业困难人员（人）',
                  '高校毕业生（人）',
                  '随军家属（人）',
                  '本季度新增人数',
                  '申领编号',
                  '是否网办',
                  '是否省投保',
                  '是否本季度新增',
                  '受影响职工（人）',
                  '建档立卡贫困劳动力（人）',
                  '合计（人）',
                  '养老保险（元）',
                  '失业保险（元）',
                  '工伤保险（元）',
                  '生育保险（元）',
                  '医疗保险（元）',
                  '社保补贴合计（元）',
                  '一般性岗位补贴（元）', ]
    data_df = pd.DataFrame(list_all, columns=list_title)
    data_df.to_excel("/usr/local/lib/file/task.xlsx")
    return send_from_directory('/usr/local/lib/file', filename='task.xlsx', as_attachment=True)


# @bp.route('/api/v1/runProcess', methods=['get', 'post'])
# def runProcess():
#     """调用监测机器人流程"""
#     reg = ResMsg()
#     headers = {
#         'key': 'ed803dfa-4900-4984-9c16-dba798a24537'
#     }
#     url = 'https://192.168.210.9:44388/controller/v1.0/api/runProcess'
#     body = {
#         "callbackUrl": "",
#         "inputValues": "",
#         "processId": 1081,
#         "robotUid": ""
#     }
#     res = requests.post(url, headers=headers, data=json.dumps(body), verify=False)
#     data = {
#         'data': res.json()
#     }
#     reg.update(data=data)
#     return jsonify(reg.data)


@bp.route('/api/v1/show_back_Person', methods=['get'])
def show_back_Person():
    """展示回填人员信息"""
    reg = ResMsg()
    cid = request.values.get('br_cid', None)
    apply_num = request.values.get('apply_num', None)
    br_fill_back = request.values.get('br_fill_back', None)
    br_state = request.values.get('br_state', None)
    page_num = int(request.values.get("pageNum", 1))
    page_size = int(request.values.get("pageSize", 10))
    # 定义翻页参数
    page = {
        "pageNum": page_num,
        "pageSize": page_size,
        "total": 0,
    }
    reg.add_field(name="page", value=page)

    back_person_info = db.session.query(Back_record_info.br_person_ID,
                                        Back_record_info.br_person_name,
                                        Back_record_info.br_fill_back,
                                        Back_record_info.br_state,
                                        Back_record_info.br_detail,
                                        Back_record_info.br_create_date,
                                        Back_record_info.br_update_date)
    if br_fill_back != 'undefined' and br_fill_back:
        # todo:找出回填还是回退企业名单
        if int(br_fill_back) == 2:
            back_person_info = back_person_info.filter(Back_record_info.br_fill_back == 2)
        else:
            back_person_info = back_person_info.filter(Back_record_info.br_fill_back == 1)
    if apply_num != 'undefined' and apply_num:
        back_person_info = back_person_info.filter(Back_record_info.br_apply_num == apply_num)

    # todo:找出对应的人员
    back_person_info = back_person_info.filter(Back_record_info.br_person_ID != '',
                                               Back_record_info.br_person_name != '',
                                               Back_record_info.br_cid == cid)
    # 查询字段匹配内容
    fields = ToolFunc().static_fields()
    # 总数
    total = back_person_info.count()
    results = back_person_info.slice((page_num - 1) * page_size, page_num * page_size).all()
    data = mapping_field(fields=fields, results=results)
    page['total'] = total
    reg.update(data=data)
    return jsonify(reg.data)


'''流程监控'''


@bp.route('/api/v1/progressInfo', methods=['get'])
def check_info():
    '''流程进度'''
    company_check = db.session.query(CheckInfo).filter(CheckInfo.check_type == 'company_check').first()
    person_check = db.session.query(CheckInfo).filter(CheckInfo.check_type == 'person_check').first()
    medical_check = db.session.query(CheckInfo).filter(CheckInfo.check_type == 'medical_check').first()
    company_data = {
        'type': company_check.check_type,
        'total': company_check.state.split('/')[1] if '/' in company_check.state else '',
        'done': company_check.state.split('/')[0] if '/' in company_check.state else '',
        'undoe': (int(company_check.state.split('/')[1]) - int(
            company_check.state.split('/')[0])) if '/' in company_check.state else '',
        'update_time': company_check.update_time,
    }
    person_data = {
        'type': person_check.check_type,
        'total': person_check.state.split('/')[1] if '/' in person_check.state else '',
        'done': person_check.state.split('/')[0] if '/' in person_check.state else '',
        'undoe': (int(person_check.state.split('/')[1]) - int(
            person_check.state.split('/')[0])) if '/' in person_check.state else '',
        'update_time': person_check.update_time,
    }
    medical_data = {
        'type': medical_check.check_type,
        'total': medical_check.state.split('/')[1] if '/' in medical_check.state else '',
        'done': medical_check.state.split('/')[0] if '/' in medical_check.state else '',
        'undoe': (int(medical_check.state.split('/')[1]) - int(
            medical_check.state.split('/')[0])) if '/' in medical_check.state else '',
        'update_time': medical_check.update_time,
    }
    data = {'check_data': [
        company_data,
        person_data,
        medical_data,
    ]}

    return jsonify(data)


'''导出进度监控excel表'''


@bp.route('/api/v1/export_progressInfo', methods=['get'])
def export_progressInfo():
    path = u'/usr/local/lib/file/progressInfo.xlsx'
    apply_season = "2021-3"
    if os.path.exists(path):
        os.remove(path)
    workbook = xw.Workbook(path)
    # 表头
    head_title = workbook.add_format({
        'align': "center",
        "valign": 'vcenter',
        "bold": True,
        "font_size": 20
    })
    style_title = workbook.add_format({
        "align": "center",
        "valign": "vcenter",
        "bold": False,
        "font_size": 12,
        "text_wrap": 1
    })

    worksheet = workbook.add_worksheet('可审核企业列表')
    worksheet.write(0, 0, '单位名称', head_title)
    worksheet.write(0, 1, "是否有新增", head_title)
    worksheet.write(0, 2, "新增人数", head_title)
    company_list = db.session.quer(CompanyInfo).filter(CompanyInfo.c_apply_season == apply_season,
                                                       CompanyInfo.isIdentify is True).order_by(
        CompanyInfo.c_isseason.desc())
    num = 1
    for company in company_list:
        worksheet.write_row(num, 0,
                            [company.c_name, "是" if company.c_isseason else "否", str(company.c_season_add_count)],
                            cell_format=style_title)
        num += 1

    workbook.close()
    return send_from_directory('/usr/local/lib/file', filename='progressInfo.xlsx', as_attachment=True)


@bp.route('/api/v1/addDetailPayInfo', methods=['post'])
def addDetailPayInfo():
    reg = ResMsg()
    obj = request.get_json(force=True)
    ID = obj.get("ID", None)
    apply_num = obj.get("apply_num", None)
    # apply_season = DBSessionQuery(apply_num=apply_num).get_tb_date()  # 补贴金额月份

    try:
        # for month in apply_season:
        #     isExist = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == ID,
        #                                                      DetailPayInfo.d_apply_num == apply_num,
        #                                                      DetailPayInfo.d_pay_month == month).first()
        detail_pay_info = DetailPayInfo()
        detail_pay_info.d_ID = ID
        detail_pay_info.d_apply_num = apply_num
        db.session.add(detail_pay_info)
        db.session.commit()
        return jsonify(reg.data)
    except Exception as e:
        logging.error("错误信息：{}".format(e))
        db.session.rollback()
        reg.update(msg="添加失败", code=-1)
        return jsonify(reg.data)


@bp.route('/api/v1/deleteDetailPayInfo', methods=['post'])
def deleteDetailPayInfo():
    reg = ResMsg()
    obj = request.get_json(force=True)
    ID = obj.get("ID")
    pay_month = obj.get("pay_month")
    detail_pay_info = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == ID,
                                                             DetailPayInfo.d_pay_month == pay_month)

    if detail_pay_info:
        try:
            pay_obj = detail_pay_info.first()
            db.session.delete(pay_obj)
            db.session.commit()
            return jsonify(reg.data)
        except Exception as e:
            logging.error("错误日志：{}".format(e))
            db.session.rollback()
            reg.update(msg="删除失败", code=-1)
            return jsonify(reg.data)
    else:
        reg.update(msg="该补贴月份不存在", code=-1)
        return jsonify(reg.data)


@bp.route("/api/v1/saveFile", methods=["post"])
def saveFile():
    reg = ResMsg()
    apply_num = request.values.get("apply_num", None)
    card_ID = request.values.get("ID", None)
    person = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num,
                                                 PersonInfo.p_ID == card_ID).first()
    if not person:
        reg.update(msg="没有此人", code=-1)
        return jsonify(reg.data)
    try:
        file_path_list = eval(person.p_file_path)
        if isinstance(file_path_list, list):
            for file in file_path_list:
                path_list = file.split("/")
                if not os.path.exists("/data/local/lib/zygbt/" + path_list[1]):
                    os.mkdir("/data/local/lib/zygbt/" + path_list[1])
                else:
                    return jsonify(reg.data)
                url = "http://192.168.210.9/zygbt" + file
                logging.error("url:" + url)
                image = requests.get(url).content
                fp = open("/data/local/lib/zygbt" + file, "wb")
                fp.write(image)
                fp.close()
            return jsonify(reg.data)
        else:
            reg.update(msg="", code=-1)
            return jsonify(reg.data)
    except Exception as e:
        logging.error("没有附件" + str(e))
        reg.update(msg="没有附件", code=-1)
        return jsonify(reg.data)


@bp.route("/api/v1/data_controller", methods=["post"])
def data_controller():
    reg = ResMsg()
    obj = request.get_json(force=True)
    pro_num = obj.get("pro_num", None)  # 项目编码
    apply_season = obj.get("apply_season", None)  # 申报年季
    data = None
    if pro_num == "1001":
        # 招用工补贴
        datas = db.session.query(Controller_info).filter(Controller_info.project_ID == pro_num,
                                                         Controller_info.apply_season == apply_season).first()
        data = datas.detail
    elif pro_num == "1002":
        # 毕业生补贴
        pass
    elif pro_num == "1003":
        # 灵活就业补贴
        pass
    elif pro_num == "1004":
        # 创业带动就业补贴
        pass
    elif pro_num == "1005":
        # 创业带动就业补贴
        pass
    else:
        pass
    reg.update(data=data)
    return jsonify(reg.data)


@bp.route("/api/v1/runSendEmail", methods=["POST"])
def sendEmail():
    processId = request.values.get("processId", None)
    url = "https://192.168.210.9:44388/controller/v2.0/api/runProcess"

    payload = json.dumps({
        "callbackUrl": "",
        "inputValues": "",
        "processId": processId,
        "robotUid": []
    })
    headers = {
        'key': 'ed803dfa-4900-4984-9c16-dba798a24537',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    logging.error(response.text)
    return jsonify({"isOk": 1, "text": str(response.text)})


@bp.route("/api/v1/toAutoIdentifyPerson", methods=["GET"])
def toAutoIdentifyPerson():
    reg = ResMsg()
    apply_num = request.values.get("apply_num", None)
    identify_person = request.values.get("identify_person", None)
    roleName = request.values.get("roleName", None)
    account_type = getAccountAuthority(roleName)
    if account_type == 0:
        pass
    elif account_type == 1:
        pass
    else:
        reg.update(code=-1, msg="请用街道账号或者区级账号登录")
        return jsonify(reg.data)

    if not apply_num:
        reg.update(msg="自动审核续期人员接口调用失败", code=-1)
        return jsonify(reg.data)
    person_list = db.session.query(PersonInfo).filter(PersonInfo.p_c_apply_num == apply_num).all()
    if len(person_list) == 0:
        reg.update(msg="自动审核续期人员接口调用失败", code=-1)
        return jsonify(reg.data)
    company_info = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()  # 匹配公司信息，更新状态
    for person in person_list:
        try:
            if person.p_robot_result:
                # 预审结果为通过
                # 人员的审核通过
                # if person.p_street_result is None and account_type == 1:
                #     reg.update(code=-1, msg="街道还未审核该人员")
                #     return jsonify(reg.data)
                if account_type == 0:
                    if person.p_person_result is not None:
                        reg.update(code=-1, msg="区级人员已审核该人员")
                        return jsonify(reg.data)
                    person.p_street_result = True
                    person.p_final_list = 1
                    person.p_street_author = identify_person
                else:
                    person.p_person_result = True
                    person.p_final_list = 1
                    person.p_identify_person = identify_person
            # todo:如果补贴金额都为0，不能提交个人审核
            pay_month_list = DBSessionQuery(apply_num=apply_num).get_tb_date()
            person_bt = db.session.query(DetailPayInfo).filter(DetailPayInfo.d_ID == person.p_ID,
                                                               DetailPayInfo.d_apply_num == person.p_c_apply_num,
                                                               Back_record_info.br_type == account_type,
                                                               DetailPayInfo.d_pay_month.in_(pay_month_list)).all()
            if person_bt != []:
                for bt in person_bt:
                    if bt.d_medical_insur == 0 and bt.d_birth_insur == 0:
                        raise Exception(f'{person.p_ID}医疗保险和生育保险都为0，不可提交审核')
            if person.p_iscarry:
                # 是结转人员（续期）
                # 回填回退表添加人员回填信息
                # todo:查看企业是否需要有回填记录
                back_exist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
                                                                       Back_record_info.br_state == '等待',
                                                                       Back_record_info.br_person_ID == '',
                                                                       Back_record_info.br_type == account_type,
                                                                       or_(Back_record_info.br_fill_back == 0,
                                                                           Back_record_info.br_fill_back == 1)
                                                                       ).all()
                # todo:防止重复审核同一个人
                person_back_exist = db.session.query(Back_record_info).filter(
                    Back_record_info.br_apply_num == apply_num,
                    Back_record_info.br_person_ID == person.p_ID,
                    Back_record_info.br_state == '等待').all()
                # 如果有该企业的回填记录
                if back_exist != []:
                    if person_back_exist == []:
                        # todo:添加回填回退记录
                        back = db.session.query(Back_record_info).filter(Back_record_info.br_state == '等待',
                                                                         Back_record_info.br_apply_num == apply_num,
                                                                         Back_record_info.br_person_ID == '',
                                                                         Back_record_info.br_type == account_type,
                                                                         or_(Back_record_info.br_fill_back == 0,
                                                                             Back_record_info.br_fill_back == 1)
                                                                         ).first()
                        back_record_info = Back_record_info()
                        back_record_info.br_apply_num = apply_num
                        back_record_info.br_company = company_info.c_name
                        back_record_info.br_apply_season = company_info.c_apply_season
                        back_record_info.br_person_ID = person.p_ID
                        back_record_info.br_person_name = person.p_name
                        back_record_info.br_fill_back = 1
                        back_record_info.br_state = '等待'
                        back_record_info.br_type = account_type
                        back_record_info.br_identify_person = identify_person
                        back_record_info.br_cid = back.id
                        db.session.add(back_record_info)
                        db.session.commit()
                else:
                    # todo:添加企业回填记录
                    back_company_info = Back_record_info()
                    back_company_info.br_apply_num = apply_num
                    back_company_info.br_company = company_info.c_name
                    back_company_info.br_apply_season = company_info.c_apply_season
                    back_company_info.br_fill_back = 0
                    back_company_info.br_state = '等待'
                    back_company_info.br_type = account_type
                    back_company_info.br_identify_person = identify_person
                    db.session.add(back_company_info)
                    db.session.commit()

                    # todo:添加个人回填回退记录
                    if person_back_exist == []:
                        back = db.session.query(Back_record_info).filter(Back_record_info.br_state == '等待',
                                                                         Back_record_info.br_apply_num == apply_num,
                                                                         Back_record_info.br_type == account_type,
                                                                         Back_record_info.br_person_ID == '').first()
                        back_record_info = Back_record_info()
                        back_record_info.br_apply_num = apply_num
                        back_record_info.br_company = company_info.c_name
                        back_record_info.br_apply_season = company_info.c_apply_season
                        back_record_info.br_person_ID = person.p_ID
                        back_record_info.br_person_name = person.p_name
                        back_record_info.br_fill_back = 1
                        back_record_info.br_state = '等待'
                        back_record_info.br_type = account_type
                        back_record_info.br_identify_person = identify_person
                        back_record_info.br_cid = back.id
                        db.session.add(back_record_info)
                        db.session.commit()
                db.session.commit()
        except Exception as e:
            logging.error("报错信息:" + str(e))
            db.session.rollback()
            continue
        db.session.commit()
    return jsonify(reg.data)


#
# @bp.route("/api/v1/addPendingBackPersonRecord", methods=["post"])
# def addPendingBackPersonRecord():
#     """增加重新抓取待报批企业"""
#     reg = ResMsg()
#     obj = request.get_json(force=True)
#     # company_name = obj.get("company_name",None)
#     remark = obj.get("remark", None)
#     apply_num = obj.get("apply_num", None)
#     identify_person = obj.get("identify_person", None)
#     if not apply_num or apply_num == "undefined":
#         reg.update(msg="请输入申领编号", code=-1)
#         return jsonify(reg.data)
#     try:
#         company = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()
#
#         if not company:
#             reg.update(msg="企业不存在", code=-1)
#             return jsonify(reg.data)
#         # 判断是否有记录
#         isExists = db.session.query(RecatchDataInfo).filter(RecatchDataInfo.apply_num == apply_num,
#                                                             RecatchDataInfo.company_name == company.c_name,
#                                                             RecatchDataInfo.state == False)
#
#         if isExists.first():
#             reg.update(msg="已增加到列表中，请勿重复提交", code=-1)
#             return jsonify(reg.data)
#
#         # 新增记录
#         rec_info = RecatchDataInfo()
#         rec_info.apply_num = apply_num
#         rec_info.company_name = company.c_name
#         if remark:
#             rec_info.remark = remark
#         else:
#             rec_info.remark = "手动添加"
#         rec_info.register_num = company.c_register_num
#         rec_info.identify_person = identify_person
#         db.session.add(rec_info)
#         db.session.commit()
#
#         return jsonify(reg.data)
#     except Exception as e:
#         logging.error("addPendingBack:" + str(e))
#         db.session.rollback()
#         reg.update(msg="接口有误", code=-1)
#         return jsonify(reg.data)
#
#
# @bp.route("/api/v1/showPendingBackPersonRecord", methods=["post"])
# def showPendingBackPersonRecord():
#     """展示重新抓取待报批企业"""
#     reg = ResMsg()
#     data = {
#         "recatchInfo": []
#     }
#     d_list = db.session.query(RecatchDataInfo).filter()
#     obj = request.get_json(force=True)
#     apply_num = obj.get("apply_num", None)
#     company_name = obj.get("company_name", None)
#     page = obj.get('page', dict())
#     page_num = int(page.get("pageNum", 1))
#     page_size = int(page.get("pageSize", 10))
#     # 定义翻页参数
#     page = {
#         "pageNum": page_num,
#         "pageSize": page_size,
#         "total": 0,
#     }
#     reg.add_field(name="page", value=page)
#     try:
#         if apply_num:
#             d_list = d_list.filter(RecatchDataInfo.apply_num == apply_num)
#         if company_name:
#             d_list = d_list.filter(RecatchDataInfo.company_name == company_name)
#     except Exception as e:
#         logging.error(e)
#     total = d_list.count()
#     data_list = d_list.slice((page_num - 1) * page_size, page_num * page_size).all()
#     for d in data_list:
#         data["recatchInfo"].append(d.to_dict())
#     page["total"] = total
#     reg.update(data=data)
#     return jsonify(reg.data)


# @bp.route("/api/v1/toBackPending", methods=["POST"])
# def toBackPending():
#     """回退到待报批"""
#     reg = ResMsg()
#     obj = request.get_json(force=True)
#     apply_num = obj.get('apply_num', None)
#     approval_name = obj.get('approval_name', None)
#     approval_reason = obj.get("approval_reason", None)
#     company = db.session.query(CompanyInfo).filter(CompanyInfo.c_apply_num == apply_num).first()
#     apply_season = company.c_apply_season
#     name = company.c_name
#     back_company_exist = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
#                                                                    Back_record_info.br_fill_back == 3,
#                                                                    Back_record_info.br_state == '等待').all()
#     # 企业回填等待中回退
#     back_company_exist1 = db.session.query(Back_record_info).filter(Back_record_info.br_apply_num == apply_num,
#                                                                     Back_record_info.br_fill_back == 1,
#                                                                     Back_record_info.br_state == '等待').all()
#
#     try:
#         if back_company_exist1:
#             for record in back_company_exist1:
#                 record.br_state = "失败"
#                 record.br_detail = "审核异常立即回退"
#             company.c_person_result = None
#             company.c_identify_person = None
#             company.c_identify_comment = approval_reason
#             db.session.commit()
#         else:
#             if not back_company_exist:
#                 back_info = Back_record_info()
#                 back_info.br_apply_season = apply_season
#                 back_info.br_apply_num = apply_num
#                 back_info.br_company = name
#                 back_info.br_fill_back = 3
#                 back_info.br_state = '等待'
#                 back_info.br_identify_person = approval_name
#                 company.c_person_result = None
#                 company.c_identify_person = None
#                 company.c_identify_comment = approval_reason
#                 db.session.add(back_info)
#                 db.session.commit()
#             else:
#                 reg.update(code=-1, msg='该企业已在回退中')
#                 return jsonify(reg.data)
#         # 判断是否有记录
#         isExists = db.session.query(RecatchDataInfo).filter(RecatchDataInfo.apply_num == apply_num,
#                                                             RecatchDataInfo.company_name == company.c_name,
#                                                             RecatchDataInfo.state == False)
#
#         if isExists.first():
#             reg.update(msg="已增加到列表中，请勿重复提交", code=-1)
#             return jsonify(reg.data)
#
#         # 新增记录
#         rec_info = RecatchDataInfo()
#         rec_info.apply_num = apply_num
#         rec_info.company_name = company.c_name
#         rec_info.register_num = company.c_register_num
#         rec_info.identify_person = approval_name
#         db.session.add(rec_info)
#         db.session.commit()
#         return jsonify(reg.data)
#     except Exception as e:
#         logger.exception(e)
#         db.session.rollback()
#         logger.error('回退到待报批失败：{}-{}'.format(apply_num, name))
#         reg.update(code=-1, msg='公司回退数据提交失败')


@bp.route("/api/v1/upstreamFile", methods=["post"])
def upstreamFile():
    reg = ResMsg()
    file_list = request.values.get("file_list", None)
    file_list = json.loads(file_list)
    if not file_list:
        reg.update(msg="缺少文件列表", code=-1)
        return jsonify(reg.data)
    for file in file_list:
        if not os.path.exists(os.path.dirname(file["file_path"])):
            os.makedirs(os.path.dirname(file["file_path"]))
        fileRead = request.files.get(file["name"], None)
        try:
            test_img = fileRead.stream.read()
            fp = open(file["file_path"], "wb")
            fp.write(test_img)
            fp.close()
        except Exception as e:
            logging.error(e)
            continue

    return jsonify(reg.data)


def getPersonPartOfInfo(card_num, info_ID):
    """获取人员部分详情信息,调用控制台的重抓人员详情信息流程"""
    processId = 1237  # 重抓人员详情信息
    url = f"https://{SERVER_HOST2}:44388/controller/v2.0/api/runProcess"
    payload = json.dumps({
        "callbackUrl": "",
        "inputValues": json.dumps({"card_ID": card_num, "info_ID": info_ID}),
        "processId": processId,
        "robotUid": []
    })
    headers = {
        'key': CONTROLLER_KEY,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    # logging.error(response.json())


@bp.route("/api/v1/addRecatchPersonPartDetail", methods=["post"])
def addRecatchPersonPartDetail():
    reg = ResMsg()
    obj = request.get_json(force=True)
    card_ID = obj.get("card_ID", None)
    info_ID = obj.get("info_ID", None)
    identify_person = obj.get("identify_person", None)
    if not card_ID:
        reg.update(msg="缺少card_ID参数", code=-1)
    if not info_ID:
        reg.update(msg="缺少info_ID参数", code=-1)
    if not identify_person:
        reg.update(msg="缺少identify_person参数", code=-1)
    executor.submit(getPersonPartOfInfo, card_ID, info_ID)  # 处理耗时任务
    # 添加记录到数据库中
    # 查询是否有记录
    isExists = db.session.query(RecatchPersonDataInfo).filter(RecatchPersonDataInfo.card_ID == card_ID,
                                                              RecatchPersonDataInfo.info_ID == info_ID,
                                                              RecatchPersonDataInfo.state == 0).first()
    if isExists:
        reg.update(msg="正在获取该数据，请勿重新提交", code=-1)
        return jsonify(reg.data)
    try:
        rpdi = RecatchPersonDataInfo()
        rpdi.card_ID = card_ID
        rpdi.info_ID = info_ID
        rpdi.identify_person = identify_person
        db.session.add(rpdi)
        db.session.commit()
        executor.submit(getPersonPartOfInfo, card_ID, info_ID)  # 处理耗时任务
        return jsonify(reg.data)
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        reg.update(msg="添加错误", code=-1)
        return jsonify(reg.data)


@bp.route("/api/v1/showRecatchPersonPartDetail", methods=["post"])
def showRecatchPersonPartDetail():
    """展示重新获取人员信息列表"""
    reg = ResMsg()
    obj = request.get_json(force=True)
    card_ID = obj.get("card_ID", None)
    info_ID = obj.get("info_ID", None)
    page = obj.get("page", None)
    if page:
        pageNum = int(page.get("pageNum", 1))
        pageSize = int(page.get("pageSize", 20))
    else:
        pageNum = 1
        pageSize = 20
    # 定义翻页参数
    page = {
        "pageNum": pageNum,
        "pageSize": pageSize,
        "total": 0,
    }
    reg.add_field(name="page", value=page)
    recatchData = db.session.query(RecatchPersonDataInfo).filter().order_by(RecatchPersonDataInfo.state)
    if card_ID:
        recatchData = recatchData.filter(RecatchPersonDataInfo.card_ID == card_ID)
    if info_ID:
        recatchData = recatchData.filter(RecatchPersonDataInfo.info_ID == info_ID)
    # 总数
    total = recatchData.count()
    results = recatchData.slice((pageNum - 1) * pageSize, pageNum * pageSize).all()
    personData = []
    for result in results:
        personData.append(result.to_dict())
    page["total"] = total
    reg.update(data=personData)
    return jsonify(reg.data)


@bp.route("/api/v1/showCatchScreen", methods=["get"])
def showCatchScreen():
    reg = ResMsg()
    data = {
        "file_list": []
    }
    # 获取访问IP
    addr = request.environ.get('HTTP_X_FORWARDED_FOR', None)  # 捕捉访问IP
    if "192.168" in addr:
        pre_url = f"http://{SERVER_HOST2}/zygbtScreen/"
    else:
        pre_url = f"http://{SERVER_HOST1}/zygbtScreen/"
    apply_num = request.values.get("apply_num", None)
    screen_path = f"{STATIC_FILE_PATH}/zygbtScreen/" + apply_num
    for (dirpath, dirnames, filenames) in os.walk(screen_path):
        for file in filenames:
            dic = {
                "name": file.split(".")[0],
                "path": pre_url + apply_num + "/" + file
            }
            data["file_list"].append(dic)
    reg.update(data=data)
    return jsonify(reg.data)


@bp.route("/api/v1/checkDataIsWrong", methods=["get"])
def checkDataIsWrong():
    reg = ResMsg()
    apply_num = request.values.get("apply_num", None)
    if not apply_num:
        reg.update(msg="没有申领编号", code=-1)
        return jsonify(reg.data)
    # 判断是否有记录
    isExists = db.session.query(RecatchDataInfo).filter(RecatchDataInfo.apply_num == apply_num,
                                                        RecatchDataInfo.state == False).first()
    if isExists:
        reg.update(msg="该企业数据有误", code=-1)
        return jsonify(reg.data)
    else:
        return jsonify(reg.data)


# 返回街道列表
@bp.route("/api/v1/getAllStreetName", methods=["GET"])
def getAllStreetName():
    reg = ResMsg()
    reg.update(data=CONSTANTS["getAllStreetName"]["streets"])
    return jsonify(reg.data)


# todo:====================================通用模块=====================================
def List2Dict(data, fieldList):
    dic = {}
    for i in range(len(fieldList)):
        dic[fieldList[i]] = data[i]
    return dic


# 1.社保查询
@bp.route("/api/general/social/socialQuery", methods=["GET"])
def socialQuery():
    reg = ResMsg()
    ID = request.args.get("ID", None)
    base_query = DBSessionQuery(id=ID).get_socialPay_info().all()
    # base_query1 = base_query.all()
    # logging.error(base_query)
    # logging.error(base_query1)

    fieldList = [
        "s_pay_date", "s_old_base", "s_medical_base", "s_old_insur", "s_unemploy_insur", "s_injury_insur",
        "s_medical_insur",
        "s_c_old_insur", "s_c_unemploy_insur", "s_c_injury_insur", "s_c_medical_insur", "s_c_disease_insur",
        "s_c_birth_insur", "s_social_num", "s_social_c_num", "s_social_c_name", "s_social_credit_num", "s_medical_num",
        "s_medical_c_num", "s_medical_c_name", "s_medical_credit_num",
    ]

    old_insur_total = 0
    injury_insur_total = 0
    unemploy_insur_total = 0
    data_result = []
    for i in base_query:
        data_dic = List2Dict(data=i, fieldList=fieldList)
        if data_dic["s_c_old_insur"] not in ("", "-", "0", 0):
            old_insur_total += 1
        if data_dic["s_c_injury_insur"] not in ("", "-", "0", 0):
            injury_insur_total += 1
        if data_dic["s_unemploy_insur"] not in ("", "-", "0", 0):
            unemploy_insur_total += 1
        data_result.append(data_dic)

    if base_query == "":
        old_insur_total = 0
        injury_insur_total = 0
        unemploy_insur_total = 0
        data = {
            "old_insur_total": old_insur_total,
            "injury_insur_total": injury_insur_total,
            "unemploy_insur_total": unemploy_insur_total,
            "data": data_result
        }
        reg.update(data=data)
    else:
        data = {
            "old_insur_total": old_insur_total,
            "injury_insur_total": injury_insur_total,
            "unemploy_insur_total": unemploy_insur_total,
            "data": data_result
        }
        reg.update(data=data)

    return jsonify(reg.data)


# 2.社保查询上传文件
@bp.route("/api/general/social/socialUpload", methods=["POST"])
def socialUpload():
    reg = ResMsg()
    fname = request.files["file"]  # 获取上传的文件
    t = datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
    file_path = r"/home/sendi/backup/social_excel/" + t + fname.filename

    if fname:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        try:
            fname.save(file_path)
        except Exception as e:
            logging.error(e)
        reg.update(msg="上传成功！")
    else:
        reg.update(msg="文件上传失败", code=-1)
    return jsonify(reg.data)
