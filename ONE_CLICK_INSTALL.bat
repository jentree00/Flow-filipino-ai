@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title FLOW FILIPINO AI - One Click Installer
color 0A

echo ============================================================
echo   FLOW FILIPINO AI - ONE CLICK WINDOWS INSTALLER
echo   Wan 2.1 I2V 720p + 1080p upscale + Video Editor
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo Git not found. Installing Git via winget...
  winget install --id Git.Git -e --source winget
  if errorlevel 1 goto FAIL
)
where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Installing Python 3.12 via winget...
  winget install --id Python.Python.3.12 -e --source winget
  if errorlevel 1 goto FAIL
)

set "ROOT=%~dp0"
set "COMFY=%ROOT%ComfyUI"
if not exist "%COMFY%\main.py" (
  echo [1/7] Downloading ComfyUI...
  git clone https://github.com/comfyanonymous/ComfyUI.git "%COMFY%" || goto FAIL
)

echo [2/7] Creating Python environment...
if not exist "%COMFY%\.venv\Scripts\python.exe" (
  python -m venv "%COMFY%\.venv" || goto FAIL
)
call "%COMFY%\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r "%COMFY%\requirements.txt" || goto FAIL
python -m pip install -r "%ROOT%requirements.txt" || goto FAIL

if not exist "%COMFY%\models\diffusion_models" mkdir "%COMFY%\models\diffusion_models"
if not exist "%COMFY%\models\text_encoders" mkdir "%COMFY%\models\text_encoders"
if not exist "%COMFY%\models\vae" mkdir "%COMFY%\models\vae"
if not exist "%COMFY%\models\clip_vision" mkdir "%COMFY%\models\clip_vision"

echo [3/7] Downloading Wan 2.1 I2V 720p FP8 model (about 16.4 GB)...
call :download "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors?download=true" "%COMFY%\models\diffusion_models\wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" || goto FAIL

echo [4/7] Downloading UMT5 FP8 text encoder (about 6.74 GB)...
call :download "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors?download=true" "%COMFY%\models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors" || goto FAIL

echo [5/7] Downloading VAE and CLIP Vision...
call :download "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors?download=true" "%COMFY%\models\vae\wan_2.1_vae.safetensors" || goto FAIL
call :download "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors?download=true" "%COMFY%\models\clip_vision\clip_vision_h.safetensors" || goto FAIL

echo [6/7] Checking FFmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo FFmpeg not found. Trying winget...
  winget install --id Gyan.FFmpeg.Shared -e --source winget
  echo If FFmpeg is still not found after this installer, restart Windows and run again.
)

echo [7/7] Starting ComfyUI and Flow Filipino AI...
start "ComfyUI" cmd /k "cd /d "%COMFY%" && call .venv\Scripts\activate.bat && python main.py --listen 0.0.0.0 --port 8188"
timeout /t 8 /nobreak >nul
start "Flow Filipino AI" cmd /k "cd /d "%ROOT%" && call "%COMFY%\.venv\Scripts\activate.bat" && set COMFYUI_URL=http://127.0.0.1:8188 && python app.py"

echo.
echo ============================================================
echo INSTALL COMPLETE
echo Open: http://127.0.0.1:3000
echo For phone on same Wi-Fi: http://YOUR-PC-IP:3000
 echo.
echo NOTE: Wan 2.1 I2V officially supports 720p. The app's 1080p
echo mode generates at 720p and performs a high-quality FFmpeg upscale.
echo ============================================================
pause
exit /b 0

:download
set "URL=%~1"
set "DEST=%~2"
if exist "%DEST%" (
  echo Already exists: %DEST%
  exit /b 0
)
where curl.exe >nul 2>nul
if errorlevel 1 (
  echo curl.exe is required. Windows 10/11 normally includes it.
  exit /b 1
)
curl.exe -L --fail --retry 5 --retry-delay 3 -C - "%URL%" -o "%DEST%"
exit /b %errorlevel%

:FAIL
echo.
echo INSTALL FAILED. Check the error above, then run ONE_CLICK_INSTALL.bat again.
pause
exit /b 1
