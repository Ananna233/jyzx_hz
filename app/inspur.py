import base64
import datetime
import hashlib
import json
import logging
import requests
from flask import Blueprint, make_response, request, jsonify
from sqlalchemy import or_

from app.models import *
from app.utils_cyddjybt import CyLogicalProcessing
from app.utils_gxbys import DBSessionQuery
from app.utils_gxbys import GxbysLogicalProcessing
from app.utils_ycxcybt import YcxDBSessionQuery

gp = Blueprint('inspur', __name__)
logger = logging.getLogger(__name__)


# 1. 获取补贴申报个体列表
@gp.route('/inspur/kfpt/zhsl/getItemObjectList', methods=['post'])
def getItemObjectList():
    obj = request.get_json(force=True)
    itemcode = obj.get("ItemCode", None)  # 事项编号
    searchKey = obj.get('SearchKey', None)  # 查询条件

    roleName = obj.get("roleName", None)  # 账号所属街道
    page = obj.get("page", {"pageNum": 1, "pageSize": 40})  # 页

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        data = GxbysLogicalProcessing(searchKey=searchKey, roleName=roleName, page=page).getItemObjectList()
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(searchKey=searchKey, roleName=roleName, page=page).getItemObjectList()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)
    else:
        return jsonify({"msg": "请求数据有误", "code": -1})


# 2.获取申报时间列表
@gp.route('/inspur/kfpt/zhsl/getApplyDate', methods=['get'])
def getApplyDate():
    itemcode = request.args.get("ItemCode", None)  # 事项编号
    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        data = GxbysLogicalProcessing().getApplyDate()
    elif itemcode == "cyddjybt":
        data = CyLogicalProcessing().getApplyDate()

    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        data = YcxDBSessionQuery(ID=SLID).getFormData()
    if data == 'error' or data == "":
        reg.update(msg='拉取办件详情信息失败', code=-1)
        return jsonify(data)
    else:
        return jsonify(data)


# 3.获取申报对象详情信息
@gp.route('/inspur/kfpt/zhsl/getItemObjectDetail', methods=['post'])
def getItemObjectDetail():
    obj = request.get_json(force=True)
    itemcode = obj.get("ItemCode", None)  # 业务编号 cyddjybt
    apply_num = obj.get("apply_num", None)  # 申领编号
    data = ""
    if itemcode == "11440111007502521J4442111820008":
        # 高校毕业生基层就业补贴
        pass
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(apply_num=apply_num).getItemObjectDetail()
    elif itemcode == "11440111007502521J4440511004002":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 4.获取申报对象人员列表
@gp.route('/inspur/kfpt/zhsl/getObjectPersonList', methods=['POST'])
def getObjectPersonList():
    obj = request.get_json(force=True)
    itemcode = obj.get("ItemCode", None)  # 事项编号 业务编号
    apply_num = obj.get("apply_num", None)  # 申领编号
    final_list = obj.get("final_list", None)  # 列表类型 1为成功列表，2为失败列表，0为待审核列表
    page = obj.get("page", {"pageNum": 1, "pageSize": 40})  # 页
    data = ""

    if itemcode == "11440111007502521J4442111820008":
        # 高校毕业生基层就业补贴
        data = DBSessionQuery(ID=SLID).getFormData()
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(apply_num=apply_num, page=page, final_list=final_list).getObjectPersonList()
    elif itemcode == "11440111007502521J4440511004002":
        # 一次性创业资助
        data = YcxDBSessionQuery(ID=SLID).getFormData()

    if data == 'error' or data == "":
        # data.update(msg='拉取办件详情信息失败', code=-1)
        return jsonify(data)
    else:
        return jsonify(data)


# 5. 获取人员详细信息
@gp.route("/inspur/kfpt/zhsl/getPersonDetail", methods=["POST"])
def getPersonDetail():
    obj = request.get_json(force=True)
    itemcode = obj.get("ItemCode", None)  # 事项编号

    apply_num = obj.get("apply_num", None)  # 申领编号
    card_ID = obj.get("card_ID", None)  # 人员身份证id
    roleName = obj.get("roleName", None)  # 账号所属街道
    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        data = GxbysLogicalProcessing(apply_num=apply_num, card_ID=card_ID, roleName=roleName).getPersonDetail()
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(card_ID=card_ID, apply_num=apply_num).getPersonDetailInfo()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 6.提交人员审核结果请求
@gp.route("/inspur/kfpt/zhsl/approvedPerson", methods=["POST"])
def approvedPerson():
    obj = request.get_json(force=True)
    itemcode = obj.get("ItemCode", None)  # 事项编号
    apply_num = obj.get("apply_num", None)
    card_ID = obj.get("card_ID", None)
    content = obj.get("content", None)
    roleName = obj.get("roleName", None)
    # approved_type = obj.get("approved_type", None)

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        data = GxbysLogicalProcessing(apply_num=apply_num, card_ID=card_ID, content=content,
                                      roleName=roleName).approvedPerson()
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(apply_num=apply_num, card_ID=card_ID, content=content,
                                   roleName=roleName).approvedPerson()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 7.提交公司审核结果请求
@gp.route("/inspur/kfpt/zhsl/approvedCompany", methods=["POST"])
def approvedCompany():
    obj = request.get_json(force=True)
    itemcode = obj.get("ItemCode", None)  # 事项编号
    apply_num = obj.get("apply_num", None)
    content = obj.get("content", None)
    roleName = obj.get("roleName", None)  # 使用街道
    approved_type = obj.get("approved_type", None)  # 审核等级，0为街道，1为区级

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        pass
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(apply_num=apply_num, content=content, roleName=roleName).approvedCompany()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 8.企业回退
@gp.route("/inspur/kfpt/zhsl/companyRollback", methods=["GET"])
def companyRollback():
    itemcode = request.args.get("ItemCode", None)  # 事项编号 业务编号
    apply_num = request.args.get("apply_num", None)  # 申领编号
    auditor = request.args.get("auditor", None)  # 审核人/用户
    roleName = request.args.get("roleName", None)  # 登录账号街道名

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        pass
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(apply_num=apply_num, auditor=auditor, roleName=roleName).companyRollback()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 9.个人回退
@gp.route("/inspur/kfpt/zhsl/personRollback", methods=["GET"])
def personRollback():
    itemcode = request.args.get("ItemCode", None)  # 事项编号 业务编号
    apply_num = request.args.get("apply_num", None)  # 申领编号
    card_ID = request.args.get("card_ID", None)  # 身份证号
    auditor = request.args.get("auditor", None)  # 审核人/用户
    roleName = request.args.get("roleName", None)  # 登录账号街道名

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        data = GxbysLogicalProcessing(apply_num=apply_num, auditor=auditor, roleName=roleName,
                                      card_ID=card_ID).personRollback()
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        pass
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 10.企业/个人回填回退记录
@gp.route("/inspur/kfpt/zhsl/BackRecord", methods=["POST"])
def BackRecord():
    obj = request.get_json(force=True)

    searchKey = obj.get('searchKey', None)  # 查询条件
    itemcode = obj.get("ItemCode", None)  # 事项编号
    roleName = obj.get("roleName", None)  # 登录账号街道名
    page = obj.get("page", {"pageNum": 1, "pageSize": 40})

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        data = GxbysLogicalProcessing(searchKey=searchKey, roleName=roleName, page=page).BackRecord()
        pass
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(searchKey=searchKey, roleName=roleName, page=page).BackRecord()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 11.展示企业下cid的所有用户
@gp.route("/inspur/kfpt/zhsl/personBackInfo", methods=["GET"])
def personBackInfo():
    itemcode = request.args.get("ItemCode", None)  # 事项编号 业务编号
    apply_num = request.args.get("apply_num", None)  # 申领编号
    cid = request.args.get("cid", None)  # 企业回填记录序号cid

    roleName = request.args.get("roleName", None)  # 登录账号街道名
    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        pass
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = CyLogicalProcessing(apply_num=apply_num, cid=cid).personBackInfo()
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)


# 12.自动审核企业续期申报人员
@gp.route("/inspur/kfpt/zhsl/toAutoIdentifyPerson", methods=["GET"])
def toAutoIdentifyPerson():
    itemcode = request.args.get("ItemCode", None)  # 事项编号 业务编号
    apply_num = request.args.get("apply_num", None)  # 申领编号
    identify_person = request.args.get("identify_person", None)  # 审核人/用户
    roleName = request.args.get("roleName", None)  # 登录账号街道名

    data = ""
    if itemcode == "bysjcjybt":
        # 高校毕业生基层就业补贴
        pass
    elif itemcode == "cyddjybt":
        # 创业带动就业补贴
        data = {"code": -1, "msg": "暂不支持该功能。"}
        data = CyLogicalProcessing(apply_num=apply_num, identify_person=identify_person,
                                   roleName=roleName)
    elif itemcode == "ycxcyzz":
        # 一次性创业资助
        pass
    if data != "":
        return jsonify(data)
    pass


# 13.返回街道列表
@gp.route("/inspur/kfpt/zhsl/streetList", methods=["GET"])
def streetList():
    data = ['海珠区', '海珠区赤岗街', '海珠区新港街', '海珠区昌岗街', '海珠区江南中街', '海珠区滨江街', '海珠区素社街', '海珠区海幢街', '海珠区南华西街', '海珠区龙凤街', '海珠区沙园街',
            '海珠区南石头街', '海珠区凤阳街', '海珠区瑞宝街', '海珠区江海街', '海珠区琶洲街', '海珠区南洲街', '海珠区华洲街', '海珠区官洲街']

    return jsonify({"code": 200, "data": data, "error": ""})

# 14.测试创带封装函数
@gp.route("/inspur/kfpt/zhsl/test14", methods=["POST"])
def test14():
    obj = request.get_json(force=True)
    searchKey = obj.get('searchKey', None)  # 查询条件
    itemcode = obj.get("ItemCode", None)  # 事项编号
    roleName = obj.get("roleName", None)  # 登录账号街道名

    new_company_back_info = CyBackRecord_info()
    new_company_back_info.br_apply_num = "002205204083202204"
    new_company_back_info.br_company = "广州海珠区周翔仔制衣厂"
    new_company_back_info.br_person_ID = ""
    new_company_back_info.br_person_name = ""
    new_company_back_info.br_fill_back = 0
    new_company_back_info.br_detail = ""
    new_company_back_info.br_fillBackLink = ""
    new_company_back_info.br_state = "等待"
    new_company_back_info.br_identify_person = "李白"
    new_company_back_info.br_street_name = "海珠区南洲街"
    new_company_back_info.br_type = 0
    new_company_back_info.result = None
    db.session.commit()


@gp.route("/inspur/test", methods=["GET"])
def test():
    """
    测试用
    """
    apply_season = request.args.get("apply_season", None)
    apply_num = request.args.get("apply_num", None)
    card_ID = request.args.get("card_ID", None)

    data = {}
    data1 = db.session.query(
        CyCompanyInfo.id,
        CyCompanyInfo.e_apply_num,
        CyCompanyInfo.e_company_name
    ).filter(
        CyCompanyInfo.e_declaration_period == "2022年3月至2022年4月"
    )
    data["filter"] = data1.filter(CyCompanyInfo.e_company_name == "广州市海珠区云顶茶叶店")

    data['query_num'] = data1.count()
    data['query_num2'] = data1.all().count()
    data['query_type'] = type(data1)

    data['query_all'] = data1.all()
    data['query_all_type'] = type(data1.all())
    data['query_all_1'] = data1.all()[1]

    data['query_first'] = data1.first()
    data['query_first_.name'] = data1.first().e_company_name
    data['query_first_type'] = type(data1.first())

    company = db.session.query(
        CompanyInfo.id,
        CompanyInfo.c_apply_num,
        CompanyInfo.c_company_name
    ).filter(
        CompanyInfo.c_apply_num == "0003051371522021-40"
    ).first()

    data["test"] = company.c_company_name
    data["test2"] = company

    return jsonify(data)


@gp.route("/inspur/test2", methods=["GET"])
def test2():
    """
    测试用
    """
    bys_back_info = BysBackInfo()
    bys_back_info.apply_num = "123"
    bys_back_info.card_ID = "123"
    bys_back_info.fill_back = 1
    bys_back_info.fill_back_link = "123"
    bys_back_info.state = "等待"
    bys_back_info.detail = "wu"
    bys_back_info.identify_person = "张三"
    bys_back_info.br_type = 0
    bys_back_info.br_street_name = "海珠区华洲街"
    db.session.add(bys_back_info)
    db.session.commit()

    return jsonify("ok")


@gp.route("/inspur/test3", methods=["GET"])
def test3():
    """
    测试用
    """
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
    ).filter(
        BysBackInfo.apply_num == "123",
        BysBackInfo.card_ID == "123"
    ).all()

    return jsonify(data)
