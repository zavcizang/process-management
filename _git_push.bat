@echo off
cd /d D:\python\OS上机作业
echo === git status ===
git status
echo === git add ===
git add -A
echo === git commit ===
git commit -m "fix: fork命名、Stride调度公平性、COW初始内存分配"

echo === git remote ===
git remote -v

echo === git push ===
git push
echo === DONE ===
pause
