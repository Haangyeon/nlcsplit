param([Parameter(Mandatory=$true)][string]$PdfPath)
# Close the Acrobat document that holds $PdfPath, but only when the foreground
# window's title names that same file. The title check is the interlock: Ctrl+W
# must never reach a different document the user has open.
$ErrorActionPreference = "Stop"
$leaf = Split-Path $PdfPath -Leaf
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
"@
function TitleOf([IntPtr]$h) {
  $sb = New-Object System.Text.StringBuilder 512
  [void][W]::GetWindowText($h, $sb, $sb.Capacity)
  return $sb.ToString()
}
$proc = Get-Process Acrobat -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $proc) { Write-Output "NOT_ACTIVE_DOC"; exit 3 }
$h = $proc.MainWindowHandle
[void][W]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 350
if ([W]::GetForegroundWindow() -ne $h) { Write-Output "NOT_FOREGROUND"; exit 4 }
Add-Type -AssemblyName System.Windows.Forms
# The target may sit in a background tab: cycle tabs in the foreground window
# and send Ctrl+W only once the title names the target. Stop after one full loop.
$matched = $false
for ($i = 0; $i -lt 10; $i++) {
  if ((TitleOf $h) -like "*$leaf*") { $matched = $true; break }
  [System.Windows.Forms.SendKeys]::SendWait("^{TAB}")
  Start-Sleep -Milliseconds 450
}
if (-not $matched) { Write-Output "NOT_FOUND"; exit 6 }
if ([W]::GetForegroundWindow() -ne $h) { Write-Output "FOCUS_LOST"; exit 7 }
if (-not ((TitleOf $h) -like "*$leaf*")) { Write-Output "TITLE_CHANGED"; exit 5 }
# The tab title lags the switch, so the first Ctrl+W may land on the previous tab.
# Re-read the title before every attempt, and try at most twice.
for ($k = 0; $k -lt 2; $k++) {
  if (-not ((TitleOf $h) -like "*$leaf*")) { break }
  [System.Windows.Forms.SendKeys]::SendWait("^w")
  Start-Sleep -Milliseconds 800
}
Write-Output ("CLOSED:" + $leaf)
exit 0
