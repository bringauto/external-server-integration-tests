import json


s = json.dumps("\022\tUndefined")
print(s)
j = json.loads(s)
print(j)