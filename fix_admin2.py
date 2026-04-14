content = open('/root/cryptomentor-bot/.env').read()
content = content.replace('ADMIN_IDS=1187119989,7079544380,7675185179', 'ADMIN_IDS=1187119989,7675185179')
open('/root/cryptomentor-bot/.env', 'w').write(content)
import subprocess
result = subprocess.run(['grep', '-i', 'admin', '/root/cryptomentor-bot/.env'], capture_output=True, text=True)
print(result.stdout)
