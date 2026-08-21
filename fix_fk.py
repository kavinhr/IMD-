import re

with open('app/models.py', 'r') as f:
    content = f.read()

content = re.sub(r"db\.ForeignKey\('stations\.station_id'\)", r"db.ForeignKey('core.stations.station_id')", content)
content = re.sub(r"db\.ForeignKey\('parameters\.parameter_id'\)", r"db.ForeignKey('core.parameters.parameter_id')", content)
content = re.sub(r"db\.ForeignKey\('roles\.role_id'\)", r"db.ForeignKey('security.roles.role_id')", content)

with open('app/models.py', 'w') as f:
    f.write(content)
print("Foreign keys updated.")
