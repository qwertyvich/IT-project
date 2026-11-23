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
    foreach ($toc in $doc.TablesOfContents) {
      $toc.Update()
      $toc.Range.Font.Name = 'Times New Roman'
      $toc.Range.Font.Size = 12
      $toc.Range.Font.Bold = 0
      $toc.Range.Font.Color = 0
    }
    if ($doc.TablesOfContents.Count -gt 0) {
      foreach ($styleId in @(-20, -21)) {
        $style = $doc.Styles.Item($styleId)
        $style.Font.Name = 'Times New Roman'
        $style.Font.Size = 12
        $style.Font.Bold = 0
        $style.ParagraphFormat.LineSpacingRule = 4
        $style.ParagraphFormat.LineSpacing = 13.8
        $style.ParagraphFormat.SpaceAfter = 4
      }
      # Word places the field-ending paragraph on a separate page when the
      # following heading owns another page break. Keep that paragraph with
      # the heading and put their shared break on the empty paragraph itself.
      $paragraphCount = $doc.Paragraphs.Count
      for ($i = 2; $i -le $paragraphCount; $i++) {
        $paragraph = $doc.Paragraphs.Item($i)
        if ($paragraph.Range.Text.Trim() -ceq 'ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ') {
          $previous = $doc.Paragraphs.Item($i - 1)
          if ($previous.Range.Text.Trim().Length -le 1) {
            $paragraph.Format.PageBreakBefore = 0
            $previous.Format.PageBreakBefore = -1
            $previous.Format.KeepWithNext = -1
            $previous.Format.LineSpacingRule = 4
            $previous.Format.LineSpacing = 1
            $previous.Format.SpaceBefore = 0
            $previous.Format.SpaceAfter = 0
            $previous.Range.Font.Size = 1
          }
          break
        }
      }
    }
  }
  $doc.Repaginate()
  if ($Update.IsPresent) {
    foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() }
    foreach ($field in $doc.Fields) {
      if ($field.Code.Text -match '^\s*NUMPAGES\b') { $field.Update() | Out-Null }
    }
    $doc.Save()
  }
  # PDF/A embeds both Latin and Cyrillic font resources; bookmarks work in Preview.
  $doc.ExportAsFixedFormat($OutputPdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $true)
  [PSCustomObject]@{Pages=$doc.ComputeStatistics(2); Pdf=$OutputPdf} | ConvertTo-Json -Compress
  $doc.Close(0)
  $doc = $null
} finally {
  if ($doc) { $doc.Close(0) }
  if ($word) { $word.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null }
}
