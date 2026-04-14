content = open('/root/cryptomentor-bot/.env').read()
content = content.replace('ADMIN2=\n', 'ADMIN2=7675185179\n')
content = content.replace('ADMIN_IDS=1187119989,7079544380', 'ADMIN_IDS=1187119989,7079544380,7675185179')
open('/root/cryptomentor-bot/.env', 'w').write(content)
print('Done')
import subprocess
result = subprocess.run(['grep', '-i', 'admin', '/root/cryptomentor-bot/.env'], capture_output=True, text=True)
print(result.stdout)
