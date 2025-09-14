# Fadebender Bridge

Build a tiny macOS app in Xcode that:
- Opens a WebSocket server on 127.0.0.1:17890
- Creates a CoreMIDI virtual destination named "Fadebender Out"
- Accepts { op:"emit_cc", payload:[{cc,channel,value}] } and sends MIDI CC
