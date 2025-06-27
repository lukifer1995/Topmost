@echo off
chcp 65001 > nul
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"


set "REPORT=temp_summary.txt"

:: Lấy đường dẫn Desktop của người dùng hiện tại
set "DESKTOP=%USERPROFILE%\Desktop"
set "LOG=%DESKTOP%\signature_result.txt"


> "%LOG%" echo === KẾT QUẢ KIỂM TRA CHỮ KÝ SỐ ===

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
        echo ⚠️ Lỗi khi kiểm tra file này >> "%LOG%"
    )
) else (
    echo ❌ Không tìm thấy file >> "%LOG%"
)
exit /b

:AnalyzeResult
set /a Signed=0
set /a Failed=0
> "%REPORT%" echo === BÁO CÁO TỔNG HỢP ===

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
echo Tổng số file kiểm tra: %Total% >> "%REPORT%"
echo ✅ Verified: %Signed% file >> "%REPORT%"
echo ❌ Không xác định / Lỗi: %Failed% file >> "%REPORT%"

type "%REPORT%" >> "%LOG%"
del "%REPORT%"
exit /b

:End
echo.
echo === KIỂM TRA HOÀN TẤT ===
pause
