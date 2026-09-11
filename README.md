# FLOW FILIPINO AI v4 — Mobile + Multi-Engine

Android-ready mobile controller for the existing Flow Filipino AI PC/GPU backend.

## Video engines
1. Wan 2.1 I2V — local ComfyUI/Wan generation. No app credit counter; requires the PC/GPU setup.
2. Gemini Omni 1.1 Flash — Google Gemini API adapter. Supports text/image-to-video and 720p/1080p output.
3. Veo 3.1 / Veo 3.1 Fast — Google Vertex AI adapter. Supports 720p/1080p; authentication uses Google Cloud access credentials.

## Important
The Android APK is a controller/editor. The heavy Wan 14B generation remains on the PC/GPU. Cloud engines use their provider accounts and may incur provider charges.

## Android build
Open `android/` in Android Studio and Build > Build APK(s). This environment does not contain the Android SDK/Gradle toolchain, so a compiled binary APK is not included; the complete Android source project is included.

## Mobile connection
Run `python app.py` on the PC, make sure Windows Firewall allows port 3000, put phone and PC on the same Wi-Fi, then enter the PC LAN address in the Android app, for example `http://192.168.1.100:3000`.

## Cloud configuration
Omni: set `GEMINI_API_KEY` on the backend, or enter a Gemini API key in the app's Engine settings.
Veo: set `GOOGLE_CLOUD_PROJECT`, authenticate with `gcloud auth login`, and set `VEO_OUTPUT_STORAGE_URI` for automatic output storage.


## v5 Upgrade — Auto Best Engine
- AUTO engine chooses Wan local when ComfyUI is online, prefers Veo for native audio/1080p when Google Cloud is configured, and falls back to Gemini when configured.
- Per-scene automatic engine selection can be enabled.
- Updated Veo model IDs: `veo-3.1-generate-001`, `veo-3.1-fast-generate-001`, `veo-3.1-lite-generate-001`.
- Native synchronized audio/dialogue is requested for Veo when enabled.

Veo 3.1 supports text-to-video, image-to-video, reference images, native sound generation, and 720p/1080p output; the documented Vertex model IDs are the `-001` versions.
