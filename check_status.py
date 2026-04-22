from vps_ssh_utils import connect_ssh

ssh = connect_ssh()

# Check venv
stdin, stdout, stderr = ssh.exec_command('ls -la /root/cryptomentor-bot/Bismillah/venv/ 2>/dev/null || echo "No venv"')
print('Venv check:', stdout.read().decode().strip())

# Check bot processes
stdin, stdout, stderr = ssh.exec_command('ps aux | grep python | grep -v grep')
processes = stdout.read().decode()
bot_lines = [line for line in processes.split('\n') if 'Bismillah' in line or 'bot.py' in line]
print('Bot processes:')
for line in bot_lines:
    print(f'  {line}')

ssh.close()
