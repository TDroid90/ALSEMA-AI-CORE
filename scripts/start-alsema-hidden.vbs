Option Explicit

Dim shell
Set shell = CreateObject("WScript.Shell")

shell.Run "powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Users\TD\Documents\Codex\2026-08-04\referenced-chatgpt-conversation-this-is-untrusted\ALSEMA-AI-CORE\scripts\start-alsema-background.ps1""", 0, False
