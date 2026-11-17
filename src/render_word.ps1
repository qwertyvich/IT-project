param(
  [Parameter(Mandatory=$true)][string]$InputDocx,
  [Parameter(Mandatory=$true)][string]$OutputPdf,
  [switch]$Update
)
$ErrorActionPreference = 'Stop'
$word = $null
$doc = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $word.AutomationSecurity = 3
  $word.Options.UpdateLinksAtOpen = $false
  $doc = $word.Documents.Open($InputDocx, $false, (-not $Update.IsPresent), $false)
  if ($Update.IsPresent) {
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  }
  $doc.Repaginate()
  if ($Update.IsPresent) {
    foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() }
    $doc.Save()
  }
  # Keep a navigable heading outline for PDF readers, including Preview on Mac.
  $doc.ExportAsFixedFormat($OutputPdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
  [PSCustomObject]@{Pages=$doc.ComputeStatistics(2); Pdf=$OutputPdf} | ConvertTo-Json -Compress
  $doc.Close(0)
  $doc = $null
} finally {
  if ($doc) { $doc.Close(0) }
  if ($word) { $word.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null }
}
