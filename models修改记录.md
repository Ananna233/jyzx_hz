---
models修改记录
---

models.py修改后，需要在生产环境下修改：

> 1.linux上的项目models.py文件里修改
>
> 2.云资源的navicat上找到该表，添加该字段
>
> 3.如需展示该字段，则在utils_*.py找到对应代码添加字段
> 
> 4. 本地的代码models.py文件里修改


2021-10-16 毕业生基层补贴 student_info 添加了is_sendEmail字段

2021-10-18 招用工补贴添加了controller_info的表

2021-10-28 招用工失业登记信息（unemploy_info）和就业登记信息(record_info)预增加申报年季字段。
      生产环境数据库   郑子健
    - 涉及到修改的文件：
        制作流程，将新字段的数据补充。  郑子健
        流程：
            招用工补贴-获取人员详情信息   郑子健
            招用工补贴-预审流程        郑子健
            招用工补贴-生成台账。
        web代码
            utils.py
                get_unemploy_info方法
                get_record_info方法
            api.py
                /api/v1/personInfo接口
                ...
            models.py
                招用工失业登记信息表和就业登记信息表
                
2021-11-1 招用工补贴detail_pay_info 添加is_search字段
        
        
        
                
