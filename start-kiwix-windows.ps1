param([string]$Library='D:\Offline Library')
$ErrorActionPreference='Stop'
$kiwixExe=Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'kiwix-tools') -Recurse -Filter kiwix-serve.exe | Select-Object -First 1
if(-not $kiwixExe){throw 'Portable Kiwix Server is missing.'}
$archives=Get-ChildItem -LiteralPath $Library -Recurse -File -Filter '*.zim'
if(-not $archives){throw 'No completed ZIM archives found.'}
$kiwixArgs=@('--address=127.0.0.1','--port=8080','--urlRootLocation=/kiwix')+@($archives | ForEach-Object {'"'+$_.FullName+'"'})
Start-Process -FilePath $kiwixExe.FullName -ArgumentList $kiwixArgs -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'data/kiwix.log') -RedirectStandardError (Join-Path $PSScriptRoot 'data/kiwix-errors.log') -PassThru | Select-Object Id
