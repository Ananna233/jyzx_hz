from flask import jsonify

from app.models import *
import hashlib
import logging
import datetime


class YcxDBSessionQuery(object):
    def __init__(self, **kwargs):
        self.ZJHM = kwargs.get('ZJHM', None)  # 证件号码
        self.ID = kwargs.get('ID', None)  # 申领编号

    def get_businessInfo(self):
        person = db.session.query(YcxPersonInfo).filter(YcxPersonInfo.apply_num == self.ID).first()
        data = ""
        if not person:
            return data
        # 拼接材料信息
        if person.diploma_path:
            '材料信息'
            filepath_ls = eval(person.diploma_path)
            filepath_ls = eval(filepath_ls)
            DeclareMaterial = []
            for i in range(len(filepath_ls)):
                file_road = filepath_ls[i].split('/')[1:]
                file_path = hashlib.sha1(file_road[0].encode("utf-8")).hexdigest()
                file_detail = file_road[1].split('.')
                file_name = hashlib.sha1(file_detail[0].encode("utf-8")).hexdigest()  # 文件名字
                file_type = file_detail[1]  # 文件类型
                if i == 0:
                    dic = {
                        'DocumentID': '306aeaba7d1042a18b966f4d3377c275',
                        'DocumentName': '附件',
                        "FileList": [
                            {
                                'FileID': i,
                                "FileName": file_name + '.' + file_type,
                                'FilePath': 'http://192.168.210.7:19998/ycxcyzz/' + file_path + '/' + file_name + '.' + file_type,
                                "FileType": 1
                            }
                        ]
                    }
                    DeclareMaterial.append(dic)
                else:
                    dic = {
                        'DocumentID': '',
                        'DocumentName': '其他附件',
                        "FileList": [
                            {
                                'FileID': i,
                                "FileName": file_name + '.' + file_type,
                                'FilePath': 'http://192.168.210.7:19998/ycxcyzz/' + file_path + '/' + file_name + '.' + file_type,
                                "FileType": 1
                            }
                        ]
                    }
                    DeclareMaterial.append(dic)
        else:
            DeclareMaterial = []

        # 拼接申报时间
        now = person.create_time
        submitTime = str(now.year) + '-' + str(now.month) + '-' + str(now.day)

        data = {
            "ItemsData": {
                "ItemCode": "11440111007502521J4440511004002",
                "InnerCode": "",
                "ItemName": "一次性创业资助申领"
            },
            "BusinessDetails": {
                "ApplySubject": f"关于{person.name}申报的一次性创业资助申领",  # 业务主题
                "Name": "一次性创业资助申领",  # 业务名称
                "ObjectType": "1",  # 服务对象类型
                "ServiceObject": {
                    'identityType': '',
                    'idcardNo': '',
                    'name': '',
                    'sex': '',
                    'nation': '',
                    'politicalStatus': '',
                    'nativePlace': '',
                    'education': '',
                    'birthday': '',
                    'country': '',
                    'homeAddress': '',
                    'linkPhone': '',
                    'linkAddress': '',
                    'postCode': '',
                    'province': '',
                    'city': '',
                    'county': '',
                    'email': '',
                }  # 服务对象详细信息
            },
            "ApplicantInformation": {
                "ApplicantName": person.name,  # 申请人名称
                "ApplicantID": person.card_ID,  # 申请人身份证号码
                "ApplicantMobile": person.company_phone,  # 申请人手机号
                "ApplicantAddress": person.registered_office  # 申请人地址
            },
            "DeclareMaterial": DeclareMaterial,
            "PreliminaryExamination": {
                "SubmitTime": submitTime,  # 申报时间
                "ApplyFrom": '网办' if person.is_net == '是' else '非网办',  # 业务来源
                "AreaCode": "",  # 受理行政区划编码
                "AreaName": "",  # 受理行政区划名称
                "AcceptUserName": "",  # 收件人姓名
                "AcceptUserCode": "",  # 收件人编号
                "ReceiveNumber": self.ID  # 受理编号
            }
        }
        return data

    def get_formdata(self):
        """基本信息: 社保缴纳信息表，失业登记信息表，困难认定信息表"""
        person_info = db.session.query(YcxPersonInfo).filter(YcxPersonInfo.apply_num == self.ID).first()
        unemployment_info = db.session.query(YcxUnemployInfo).filter(YcxUnemployInfo.e_ID == person_info.card_ID).all()
        hardIdentify_info = db.session.query(YcxHardIdentifyInfo).filter(
            YcxHardIdentifyInfo.h_ID == person_info.card_ID).all()
        social_info = db.session.query(YcxSocialSecurity).filter(YcxSocialSecurity.card_ID == person_info.card_ID).all()
        back_info = db.session.query(YcxbackInfo).filter(YcxbackInfo.apply_num == self.ID).all()
        audit_info = db.session.query(YcxaduditInfo).filter(YcxaduditInfo.apply_num == self.ID).all()
        base_data = ""
        if not person_info:
            return base_data

        base_data = {
            'MAIN_TBL_PK': self.ID,
            'person_info': person_info,  # 创业人员信息
            "unemployment_info": unemployment_info,  # 失业登记信息
            "hardIdentify_info": hardIdentify_info,  # 困难认定信息
            "social_info": social_info,  # 社保缴纳信息
            "back_info": back_info,  # 回填回退信息
            "audit_info": audit_info,  # 审核记录信息
            "predit_info": person_info.detail,  # 预审结果
        }
        return base_data

    def getFormData(self):
        '基本信息: 失业登记信息，困难认定信息，社保缴纳信息，预审结果'
        base_data = self.get_formdata()

        # todo:转成字典类型
        predit_info = base_data['predit_info']
        person_info = base_data['person_info']

        social_info = base_data['social_info']
        social_info_list = []
        for social in social_info:
            social_info_list.append(social.to_dict())

        unemployment_info = base_data['unemployment_info']
        unemployment_info_list = []
        for employment in unemployment_info:
            unemployment_info_list.append(employment.to_dict())

        back_info = base_data['back_info']
        back_info_list = []
        for back in back_info:
            back_info_list.append(back.to_dict())

        audit_info = base_data['audit_info']
        audit_info_list = []
        for update_audit in audit_info:
            audit_info_list.append(update_audit.to_dict())

        hardIdentify_info = base_data['hardIdentify_info']
        hardIdentify_info_list = []
        for hardIdentify in hardIdentify_info:
            hardIdentify_info_list.append(hardIdentify.to_dict())
        data = {
            "MAIN_TBL_CONTENT": "",
            'MAIN_TBL_PK': self.ID,
            'yw_j_ycxperson_info': person_info.to_dict(),  # 创业人员信息
            'ycxsocial_security': social_info_list,  # 社保信息
            'yw_j_ycxunemploy_info': unemployment_info_list,  # 失业登记信息
            'yw_j_ycxback_info': back_info_list,  # 回填、回退表
            'yw_j_update_audit_info': audit_info_list,  # 审核记录信息表
            'yw_j_ycxhardidentify_info': hardIdentify_info_list,  # 困难认定信息
            'pre_audit_info': predit_info,  # 预审详情
            'state': "200",
        }
        return data

