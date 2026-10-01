$ErrorActionPreference = 'Stop'
$t = (Get-Clipboard) -replace "`r|`n", ""
$out = "E:\tmp\nlcsplit_pat.tmp"
if ($t -match '^ghp_[A-Za-z0-9]{36}$') {
    Set-Content -Path $out -Value $t -NoNewline -Encoding ascii
    Write-Output ("OK len=" + $t.Length + " file=" + $out)
} else {
    Write-Output ("NO_TOKEN_MATCH clipboardlen=" + $t.Length + " prefix=" + $t.Substring(0, [Math]::Min(4, $t.Length)))
}
