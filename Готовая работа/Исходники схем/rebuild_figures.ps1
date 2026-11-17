$ErrorActionPreference = 'Stop'
$runtimeRoot = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies'
$diagramPython = Join-Path $runtimeRoot 'python\python.exe'
$diagramNode = Join-Path $runtimeRoot 'node\bin\node.exe'
if (-not (Test-Path -LiteralPath $diagramPython) -or -not (Test-Path -LiteralPath $diagramNode)) {
    throw 'Codex runtime was not found. See README.md for standalone setup.'
}
$env:PYTHONIOENCODING = 'utf-8'
Push-Location $PSScriptRoot
try {
    & $diagramPython (Join-Path $PSScriptRoot 'draw_figures.py')
    if ($LASTEXITCODE -ne 0) { throw 'SVG generation failed' }
    & $diagramNode (Join-Path $PSScriptRoot 'render_figures.mjs') (Join-Path $PSScriptRoot 'figures')
    if ($LASTEXITCODE -ne 0) { throw 'PNG conversion failed' }
} finally { Pop-Location }
