# Fadebender — User Onboarding (Early Access)

This guide is for non‑technical users to get Fadebender working with Ableton Live on their computer.

What you need
- Ableton Live 11/12 (Standard or Suite)
- macOS or Windows
- A Fadebender account (cloud)

What you install (local)
- Fadebender Agent app (coming soon): signs in and connects to the cloud
- Ableton Remote Script (Fadebender): installed automatically by the Agent

Until the Agent is ready (developer preview)
- You can use the web app locally with a UDP stub (no Live)
- Or install the Remote Script manually (see docs/ABLETON_SETUP.md)

Step‑by‑step (future Agent flow)
1) Download and install the Fadebender Agent
2) Open the Agent and sign in
3) Click “Install Ableton Script”
   - The Agent detects your Live versions and installs the script automatically
4) Restart Ableton Live
5) Click “Verify” in the Agent
   - The Agent runs a quick test: ping/status and a test fader move
6) Open the Fadebender web app and start controlling your project

Troubleshooting
- Live not detected
  - Ensure Ableton Live is installed; restart the Agent and Live
- Verification failed
  - Close and reopen Live; ensure no firewall is blocking local (127.0.0.1) traffic
- Multiple Live versions
  - The Agent will install the script into each detected version; you can pick which one to verify

Standard vs Suite
- Live Standard works fine for core features (mixer, sends, common devices like EQ Eight, Compressor, Reverb)
- Suite adds more instruments/effects — Fadebender will degrade gracefully if a device isn’t available

Notes
- The Agent connects outbound to the cloud over TLS (no inbound ports required)
- All control messages to Live happen locally on your machine via the Remote Script
