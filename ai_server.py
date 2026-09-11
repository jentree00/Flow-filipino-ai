from flask import Flask, jsonify, request
import os
import requests

app = Flask(__name__)

# =========================================================
# FLOW FILIPINO AI SERVER
# Version 6.1
# Local-first AI video generation
# =========================================================

COMFYUI_URL = os.getenv(
    "COMFYUI_URL",
    "http://127.0.0.1:8188"
).rstrip("/")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "3000"))


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/health")
def health():

    comfy_online = check_comfyui()

    return jsonify({
        "ok": True,
        "service": "FLOW FILIPINO AI SERVER",
        "version": "6.1",

        "local_no_credit_engine": "WAN 2.1 + ComfyUI",

        "comfyui": {
            "online": comfy_online,
            "url": COMFYUI_URL
        },

        "engine_priority": [
            "wan-local",
            "gemini-omni",
            "veo"
        ]
    })


# =========================================================
# COMFYUI CHECK
# =========================================================

def check_comfyui():

    try:

        response = requests.get(
            COMFYUI_URL + "/system_stats",
            timeout=3
        )

        return response.ok

    except Exception:

        return False


# =========================================================
# ENGINE STATUS
# =========================================================

@app.get("/api/engine/status")
def engine_status():

    wan_available = check_comfyui()

    gemini_available = bool(
        os.getenv("GEMINI_API_KEY")
    )

    veo_available = bool(
        os.getenv("GOOGLE_CLOUD_PROJECT")
    )

    return jsonify({

        "ok": True,

        "engines": {

            "wan_local": {

                "id": "wan-local",

                "name": "WAN 2.1 + ComfyUI",

                "label": "WAN LOCAL — NO CREDIT REQUIRED",

                "type": "local",

                "available": wan_available,

                "cloud_credits_required": False
            },

            "gemini_omni": {

                "id": "gemini-omni",

                "name": "Gemini Omni",

                "label": "GEMINI OMNI — CLOUD",

                "type": "cloud",

                "available": gemini_available,

                "cloud_credits_required": True
            },

            "veo": {

                "id": "veo",

                "name": "Google Veo",

                "label": "VEO — CLOUD",

                "type": "cloud",

                "available": veo_available,

                "cloud_credits_required": True
            }
        },

        "default_priority": [
            "wan-local",
            "gemini-omni",
            "veo"
        ]
    })


# =========================================================
# STORY PLAN
# =========================================================

@app.post("/api/story/plan")
def story_plan():

    data = request.get_json(
        silent=True
    ) or {}

    title = data.get(
        "title",
        "Untitled Filipino Story"
    )

    genres = data.get(
        "genres",
        ["Horror"]
    )

    if isinstance(genres, str):

        genres = [genres]

    return jsonify({

        "ok": True,

        "story": {

            "title": title,

            "genres": genres,

            "episodes": 5,

            "scenes_per_episode": 3,

            "total_scenes": 15,

            "seconds_per_episode": 90,

            "total_seconds": 450,

            "aspect_ratio": "9:16",

            "resolution": {
                "native": "720p",
                "upscale": "1080p"
            }
        },

        "character_system": {

            "enabled": True,

            "identity_lock": True,

            "master_reference": True
        },

        "audio": {

            "background_music": False,

            "dialogue": True,

            "environmental_sfx": True
        },

        "generation": {

            "local_first": True,

            "engine_priority": [

                "wan-local",

                "gemini-omni",

                "veo"
            ]
        }
    })


# =========================================================
# ENGINE SELECTOR
# =========================================================

@app.post("/api/engine/select")
def select_engine():

    data = request.get_json(
        silent=True
    ) or {}

    requested = data.get(
        "engine",
        "auto"
    )

    # Explicit local Wan request
    if requested == "wan-local":

        if check_comfyui():

            return jsonify({

                "ok": True,

                "selected_engine":
                    "wan-local",

                "label":
                    "WAN LOCAL — NO CREDIT REQUIRED",

                "reason":
                    "ComfyUI is online."
            })

        return jsonify({

            "ok": False,

            "error":
                "WAN LOCAL unavailable. "
                "ComfyUI is offline."
        }), 503


    # Explicit Gemini request
    if requested == "gemini-omni":

        if os.getenv("GEMINI_API_KEY"):

            return jsonify({

                "ok": True,

                "selected_engine":
                    "gemini-omni",

                "label":
                    "GEMINI OMNI — CLOUD"
            })

        return jsonify({

            "ok": False,

            "error":
                "GEMINI_API_KEY is not configured."
        }), 503


    # Explicit Veo request
    if requested == "veo":

        if os.getenv("GOOGLE_CLOUD_PROJECT"):

            return jsonify({

                "ok": True,

                "selected_engine":
                    "veo",

                "label":
                    "VEO — CLOUD"
            })

        return jsonify({

            "ok": False,

            "error":
                "GOOGLE_CLOUD_PROJECT is not configured."
        }), 503


    # =====================================================
    # AUTO = LOCAL FIRST
    # =====================================================

    if check_comfyui():

        return jsonify({

            "ok": True,

            "selected_engine":
                "wan-local",

            "label":
                "WAN LOCAL — NO CREDIT REQUIRED",

            "reason":
                "Local Wan is available and is preferred."
        })


    if os.getenv("GEMINI_API_KEY"):

        return jsonify({

            "ok": True,

            "selected_engine":
                "gemini-omni",

            "label":
                "GEMINI OMNI — CLOUD",

            "reason":
                "Local Wan unavailable."
        })


    if os.getenv("GOOGLE_CLOUD_PROJECT"):

        return jsonify({

            "ok": True,

            "selected_engine":
                "veo",

            "label":
                "VEO — CLOUD",

            "reason":
                "Local Wan and Gemini unavailable."
        })


    return jsonify({

        "ok": False,

        "error":
            "No video generation engine is available.",

        "setup": [

            "Install ComfyUI + Wan 2.1",

            "or configure GEMINI_API_KEY",

            "or configure GOOGLE_CLOUD_PROJECT"
        ]
    }), 503


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return jsonify({

        "name":
            "FLOW FILIPINO AI SERVER",

        "version":
            "6.1",

        "status":
            "online",

        "local_engine":
            "WAN 2.1 + ComfyUI",

        "local_generation":
            "NO CLOUD CREDIT REQUIRED",

        "routes": [

            "/api/health",

            "/api/engine/status",

            "/api/engine/select",

            "/api/story/plan"
        ]
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("")
    print("==============================================")
    print(" FLOW FILIPINO AI SERVER")
    print("==============================================")
    print("")
    print("Server:")
    print(f"http://{HOST}:{PORT}")
    print("")
    print("ComfyUI:")
    print(COMFYUI_URL)
    print("")
    print("Engine priority:")
    print("1. WAN LOCAL — NO CREDIT REQUIRED")
    print("2. GEMINI OMNI — CLOUD")
    print("3. VEO — CLOUD")
    print("")
    print("==============================================")
    print("")

    app.run(
        host=HOST,
        port=PORT,
        debug=False
    )
