@echo off
chcp 65001 > nul
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

set "REPORT=temp_summary.txt"

:: Get current user's Desktop path
set "DESKTOP=%USERPROFILE%\Desktop"
set "LOG=%DESKTOP%\signature_result.txt"

> "%LOG%" echo === DIGITAL SIGNATURE VERIFICATION RESULT ===


call :CheckFile "C:\Windows\System32\dashost.exe"
call :CheckFile "C:\Windows\System32\svchost.exe"
call :CheckFile "C:\Windows\System32\services.exe"
call :CheckFile "C:\Windows\System32\lsass.exe"
call :CheckFile "C:\Windows\System32\wininit.exe"
call :CheckFile "C:\Windows\System32\csrss.exe"
call :CheckFile "C:\Windows\System32\winlogon.exe"
call :CheckFile "C:\Windows\System32\smss.exe"
call :CheckFile "C:\Windows\explorer.exe"
call :CheckFile "C:\Windows\System32\taskhostw.exe"

call :AnalyzeResult

goto End

:CheckFile
set "FILE=%~1"
echo. >> "%LOG%"
echo ----- %FILE% ----- >> "%LOG%"
if exist "%FILE%" (
    sigcheck64.exe -nobanner -q -v "%FILE%" >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo ⚠️ Error occurred during file verification >> "%LOG%"
    )
) else (
    echo ❌ File not found >> "%LOG%"
)
exit /b

:AnalyzeResult
set /a Signed=0
set /a Failed=0
> "%REPORT%" echo === SUMMARY REPORT ===

for /f "tokens=1,* delims=:" %%A in ('findstr /I /C:"Verified:" "%LOG%"') do (
    set "status=%%B"
    set "status=!status:~1!"
    if /I "!status!"=="Signed" (
        set /a Signed+=1
    ) else (
        set /a Failed+=1
        echo ❌ %%A: !status! >> "%REPORT%"
    )
)

for /f %%C in ('findstr /C:"----- " "%LOG%" ^| find /C /V ""') do set Total=%%C

echo. >> "%REPORT%"
echo. 

echo Total files checked: %Total% >> "%REPORT%"
echo Total files checked: %Total%

echo [OK] Verified: %Signed% file(s) >> "%REPORT%"
echo [OK] Verified: %Signed% file(s)

echo [X]  Unverified / Error: %Failed% file(s) >> "%REPORT%"
echo [X]  Unverified / Error: %Failed% file(s)


type "%REPORT%" >> "%LOG%"
del "%REPORT%"
exit /b

:End
echo.
echo === VERIFICATION COMPLETED ===
:: start notepad.exe "%LOG%"
pause