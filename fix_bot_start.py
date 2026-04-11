import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('147.93.156.165', port=22, username='root', password='<REDACTED_PASSWORD>', timeout=10)

print('🔍 Checking requirements.txt...')
stdin, stdout, stderr = ssh.exec_command('cat /root/cryptomentor-bot/Bismillah/requirements.txt')
requirements = stdout.read().decode()
print('Requirements:')
print(requirements)

print()
print('🔍 Checking if virtualenv exists...')
stdin, stdout, stderr = ssh.exec_command('ls -la /root/cryptomentor-bot/Bismillah/venv 2>/dev/null || echo "No venv"')
venv_check = stdout.read().decode()
print('Venv check:')
print(venv_check)

print()
print('🔄 Installing dependencies...')
# First try to create venv if it doesn't exist
stdin, stdout, stderr = ssh.exec_command('cd /root/cryptomentor-bot/Bismillah && python3 -m venv venv 2>/dev/null || echo "venv exists or failed"')
venv_create = stdout.read().decode()
print('Venv create result:')
print(venv_create)

# Install requirements
stdin, stdout, stderr = ssh.exec_command('cd /root/cryptomentor-bot/Bismillah && source venv/bin/activate && pip install -r requirements.txt')
install_result = stdout.read().decode()
install_error = stderr.read().decode()
print('Install result:')
print(install_result)
if install_error:
    print('Install errors:')
    print(install_error)

print()
print('🔄 Starting bot with venv...')
cmd = 'cd /root/cryptomentor-bot/Bismillah && source venv/bin/activate && nohup python bot.py > bot.log 2>&1 &'
print(f'Command: {cmd}')
stdin, stdout, stderr = ssh.exec_command(cmd)
exit_code = stdout.channel.recv_exit_status()
print(f'Start exit code: {exit_code}')

time.sleep(5)

print()
print('🔍 Checking bot status...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep python | grep -v grep')
processes = stdout.read().decode()
bot_lines = [line for line in processes.split('\n') if 'Bismillah' in line or 'bot.py' in line]
print('Bot processes:')
for line in bot_lines:
    print(f'  {line}')

print()
print('🔍 Checking bot log...')
stdin, stdout, stderr = ssh.exec_command('tail -30 /root/cryptomentor-bot/Bismillah/bot.log')
log = stdout.read().decode()
print('Bot log:')
print(log if log else '  (empty)')

ssh.close()