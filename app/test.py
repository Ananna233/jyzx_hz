import requests

url = "http://www.gdhrss.nwmh/gdyltcyw/techcomp/ria/commonProcessor!commonMethod.action"

payload = "{header:{\"code\":0,\"message\":{\"title\":\"\",\"detail\":\"\"}},body:{dataStores:{},parameters:{\"aac001\":1030001064635426,\"_parameters\":\"aac001\",\"_parameterTypes\":\"string\",\"_statement\":\"queryPersonAec7\",\"_statementRef\":\"employee/person/queryPersonAec7\",\"_dcId\":\"SI_Basicinfo_app\",\"_statementPageNumber\":\"''\",\"_statementPageSize\":\"''\",\"_pageNumber\":1,\"_pageSize\":30,\"_calcRecordCount\":true,\"nom\":\"queryAec7\",\"BUSINESS_ID\":\"UCA002\",\"MENUID\":\"\",\"$ATTACHMENTIDS$\":\"\",\"$WORKITEM_ID$\":null,\"$SI_APP_ID$\":\"\",\"$CATAGORY$\":\"\",\"$PAGE_PASS_TIME$\":6379}}}"
headers = {
    'Cookie': 'JSESSIONID=SANGFOR_15750318_Z51Nt48ZE0q6yP1zTuRQSksXmqqz4qV3lQSSuSaLrG0UXnRlD1zq!582953923; systemSort=%7B%22162799499%22%3A%7B%22819623%22%3A2%2C%22819627%22%3A2%2C%22819628%22%3A1%2C%22819633%22%3A2%7D%7D',
    'Host': 'www.gdhrss.nwmh',
    'Origin': 'http://www.gdhrss.nwmh',
    'Referer': 'http://www.gdhrss.nwmh/gdyltcyw/SI_BIZ_Comp/SI_Basicinfo_app/common/query/person/allPersonInfoDialog-view.jsp?menuid=&SIDialogMode=true',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3883.400 QQBrowser/10.8.4582.400',
    'Content-Type': 'text/plain'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)


"""
参数1： 
aac001     1030001064635426  
"""