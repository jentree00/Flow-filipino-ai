@echo off
echo FLOW FILIPINO AI - Wan 2.1 I2V setup
echo.
echo 1) Install/Update ComfyUI.
echo 2) Put these model files in the indicated folders:
echo.
echo diffusion_models\wan2.1_i2v_480p_14B_fp8_scaled.safetensors
echo text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors
echo vae\wan_2.1_vae.safetensors
echo clip_vision\clip_vision_h.safetensors
echo.
echo 3) Start ComfyUI on http://127.0.0.1:8188
echo 4) In this app folder run:
echo    pip install -r requirements.txt
echo    python app.py
echo 5) Open http://127.0.0.1:3000
echo.
echo Model weights are not bundled because they are very large.
pause
