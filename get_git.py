import subprocess

with open('git_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(subprocess.check_output(['git', 'status'], text=True))
    f.write('\n\n--- DIFF STAT ---\n\n')
    f.write(subprocess.check_output(['git', 'diff', '--stat'], text=True))
    f.write('\n\n--- UNTRACKED FILES ---\n\n')
    f.write(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True))
