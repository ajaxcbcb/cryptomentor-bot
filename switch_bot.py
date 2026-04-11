import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('147.93.156.165', port=22, username='root', password='<REDACTED_PASSWORD>', timeout=10)

print('🔄 Killing old bot process...')
stdin, stdout, stderr = ssh.exec_command('pkill -f "whitelabel-1.*bot.py"')
kill_result = stdout.read().decode()
print('Kill result:', kill_result)

time.sleep(2)

print('🔄 Starting new bot with venv...')
cmd = 'cd /root/cryptomentor-bot/Bismillah && source venv/bin/activate && nohup python bot.py > bot.log 2>&1 &'
print(f'Command: {cmd}')
stdin, stdout, stderr = ssh.exec_command(cmd)
exit_code = stdout.channel.recv_exit_status()
print(f'Start exit code: {exit_code}')

time.sleep(3)

print('🔍 Checking bot status...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep python | grep -v grep')
processes = stdout.read().decode()
bot_lines = [line for line in processes.split('\n') if 'Bismillah' in line or 'bot.py' in line]
print('Bot processes:')
for line in bot_lines:
    print(f'  {line}')

print('🔍 Checking bot log...')
stdin, stdout, stderr = ssh.exec_command('tail -20 /root/cryptomentor-bot/Bismillah/bot.log')
log = stdout.read().decode()
print('Bot log:')
print(log if log else '  (empty)')

ssh.close()