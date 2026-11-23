param(
  [Parameter(Mandatory=$true)][string]$InputDocx,
  [Parameter(Mandatory=$true)][string]$OutputPdf,
  [switch]$Update,
  [string]$TableMapPath,
  [switch]$FirstSplitOnly,
  [switch]$SkipPdf
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
  if ($TableMapPath) {
    $tableMap = @()
    for ($tableNumber = 1; $tableNumber -le $doc.Tables.Count; $tableNumber++) {
      $table = $doc.Tables.Item($tableNumber)
      if ($FirstSplitOnly.IsPresent) {
        $rangeStart = $table.Range.Duplicate
        $rangeStart.Collapse(1)
        $rangeEnd = $table.Range.Duplicate
        $rangeEnd.End = $rangeEnd.End - 1
        $rangeEnd.Collapse(0)
        if ($rangeStart.Information(3) -eq $rangeEnd.Information(3)) { continue }
      }
      $rowMap = @()
      for ($rowNumber = 1; $rowNumber -le $table.Rows.Count; $rowNumber++) {
        $rowRange = $table.Rows.Item($rowNumber).Range.Duplicate
        $startRange = $rowRange.Duplicate
        $startRange.Collapse(1)
        $endRange = $rowRange.Duplicate
        $endRange.End = $endRange.End - 1
        $endRange.Collapse(0)
        $rowMap += [PSCustomObject]@{row=$rowNumber; start=$startRange.Information(3); end=$endRange.Information(3)}
      }
      $tableMap += [PSCustomObject]@{table=$tableNumber; rows=$rowMap}
      if ($FirstSplitOnly.IsPresent) { break }
    }
    $mapObject = if ($FirstSplitOnly.IsPresent) {
      [PSCustomObject]@{table_count=$doc.Tables.Count; first_only=$true; records=@($tableMap)}
    } else { @($tableMap) }
    $jsonMap = ConvertTo-Json -InputObject $mapObject -Depth 6
    [System.IO.File]::WriteAllText($TableMapPath, $jsonMap, (New-Object System.Text.UTF8Encoding($false)))
  }
  # PDF/A embeds both Latin and Cyrillic font resources; bookmarks work in Preview.
  if (-not $SkipPdf.IsPresent) {
    $doc.ExportAsFixedFormat($OutputPdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $true)
  }
  [PSCustomObject]@{Pages=$doc.ComputeStatistics(2); Pdf=$OutputPdf} | ConvertTo-Json -Compress
  $doc.Close(0)
  $doc = $null
} finally {
  if ($doc) { $doc.Close(0) }
  if ($word) { $word.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null }
}
