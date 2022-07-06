import requests
import time
import json
from hashlib import md5,sha256
import datetime
import random
class Get_GDInfo(object):
    def __init__(self,TYXYDM):
        self.TYXYDM = TYXYDM
    def get_timestamp(self):
        dtime = datetime.datetime.now()
        ans_time = time.mktime(dtime.timetuple())
        return str(int(ans_time))

    def get_orgSign(self,orgCode, orgSecret, curTime, sequence):
        m = md5()
        m.update(f"{orgCode}_{orgSecret}_{curTime}_{sequence}".encode("utf-8"))
        secret = m.hexdigest().upper()
        return secret

    def get_signature(self,timestamp,passToken,nonce):
        string = str(timestamp) + passToken + nonce + str(timestamp)
        s = sha256()
        s.update(string.encode("utf-8"))
        return s.hexdigest().upper()

    def get_province_data(self):
        url = "http://10.128.185.91:9102/middle/intfc_invoke"
        curTime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        timestamp = self.get_timestamp()
        nonce = str(random.random()*random.random())
        data = {
            "curTime": curTime,
            "orgCode": "8952639f2",
            "resourceId": "1443486923129843712",
            "orgSign": "",
            "param": {
                "x-tif-signature": "xxxx",
                "x-tif-timestamp": timestamp,
                "system_id": "C90-44000290",
                "query": {
                    "TYSHXYDM": self.TYXYDM  # 统一信用代码
                },
                "x-tif-serviceId": "C1611889640589",
                "query_timestamp": timestamp,
                "x-tif-paasid": "C90-44000290",
                "x-tif-nonce": nonce,
                "audit_info": {
                    "query_object_id": "1",
                    "operator_name": "1",
                    "item_code": "1",
                    "item_id": "1",
                    "operator_id": "1",
                    "terminal_info": "1",
                    "query_timestamp": "1",
                    "item_sequence": "1",
                    "query_object_id_type": "1"
                }
            },
            "sequence": "112233abc"
        }
        data["orgSign"] = self.get_orgSign(data["orgCode"],"c3bcfe6069aa8624496237b13b2ad6e3",curTime,data["sequence"])
        data["param"]["x-tif-signature"] = self.get_signature(timestamp,"7e42571222dc4a99827207ce9a139ec3",nonce)
        payload = json.dumps(data)
        headers = {
            'X-Forwarded-For': '10.128.23.131',
            'Content-Type': 'application/json;charset=utf-8'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        res_data = response.json()
        return res_data["data"]["data"]

import datetime as dt
def isExist_GD(gd, nd_list):
    for nd in nd_list:
        if nd["gd"] == gd:
            return nd_list.index(nd)
    return -1

def get_info(dic_list):
    nd = []
    for dic in dic_list:
        if not dic["SJSJC"]:
            update_date = dt.datetime.strptime(dic["TJSJC"][:19],"%Y-%m-%dT%H:%M:%S")
        else:
            update_date = dt.datetime.strptime(dic["SJSJC"], '%Y/%m/%d %H:%M:%S')
        gd = dic["GDFQRMC"]  # 股东/发起人名称
        zjlx = dic["ZJLX"]  # 证件类型 10为身份证号码
        index = isExist_GD(gd, nd)
        if index != -1:
            # 有数据
            if update_date >= nd[index]["update_date"]:
                nd[index] = {
                    "update_date": update_date,
                    "gd": gd,
                    "zjlx": zjlx
                }
        else:
            # 没有数据
            nd.append({
                "update_date": update_date,
                "gd": gd,
                "zjlx": zjlx
            })
    return nd


def get_gd_predit_info(nd_list):
    gd_list = []  # 股东信息数组
    new_date = None
    nd_list.sort(key=lambda item: item["update_date"], reverse=True)
    for nd in nd_list:
        if not new_date:
            new_date = nd["update_date"]
        if new_date != nd["update_date"]:
            break
        if isExist_GD(nd["gd"], gd_list) == -1:
            gd_list.append(nd)
    return gd_list
if __name__ == '__main__':
    company_info = [
        {
            "name": "壹度国际货运代理（广州）有限公司",
            "social_num": "91440101MA5CHYDD1A"
        },
    ]
    for company in company_info:
        print(f"==================================={company['name']}===================================")
        data = Get_GDInfo(TYXYDM=company["social_num"]).get_province_data()
        nd_list = get_info(data)
        predit_list = get_gd_predit_info(nd_list)
        for predit in predit_list:
            print(predit)
        print("=========================================================================")
