import re

string = "javascriotns:sadasd('12321412')"
regex = "[0-9]+"
res = re.findall(regex,string)
print(res)