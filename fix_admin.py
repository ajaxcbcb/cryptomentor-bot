content = open('/root/cryptomentor-bot/.env').read()
content = content.replace('ADMIN2=\n', 'ADMIN2=<REDACTED_ADMIN_ID>\n')
content = content.replace('ADMIN_IDS=1234500009,7079544380', 'ADMIN_IDS=1234500009,7079544380,1234500014')
open('/root/cryptomentor-bot/.env', 'w').write(content)
print('Done')
import subprocess
result = subprocess.run(['grep', '-i', 'admin', '/root/cryptomentor-bot/.env'], capture_output=True, text=True)
print(result.stdout)
