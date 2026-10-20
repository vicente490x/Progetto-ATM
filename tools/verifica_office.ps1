$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$wordApp = $null
$excelApp = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $projectDir 'Consegna_esame') -Filter '*.docx') {
        $doc = $wordApp.Documents.Open($file.FullName, $false, $true)
        $doc.Repaginate()
        $pages = $doc.ComputeStatistics(2)
        Write-Output ($file.Name + ': pagine=' + $pages + ', collegamenti=' + $doc.Hyperlinks.Count)
        for ($page = 1; $page -le $pages; $page++) {
            $range = $doc.GoTo(1, 1, $page)
            $start = $range.Start
            if ($page -lt $pages) { $end = $doc.GoTo(1, 1, ($page + 1)).Start } else { $end = $doc.Content.End }
            $pageText = $doc.Range($start, $end).Text
            Write-Output ('  Pagina ' + $page + ': ' + $pageText.Substring(0, [Math]::Min(100, $pageText.Length)).Replace("`r", ' | '))
        }
        $doc.Close(0)
    }
} finally {
    if ($null -ne $wordApp) { $wordApp.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) }
}
try {
    $excelApp = New-Object -ComObject Excel.Application
    $excelApp.Visible = $false
    $excelApp.DisplayAlerts = $false
    $book = $excelApp.Workbooks.Open((Join-Path $projectDir 'Consegna_esame\Casi_di_test_ATM.xlsx'), 0, $true)
    $excelApp.CalculateFull()
    $tests = $book.Worksheets.Item(1)
    $guide = $book.Worksheets.Item(2)
    Write-Output ('Excel: fogli=' + $book.Worksheets.Count + ', tabelle=' + $tests.ListObjects.Count)
    Write-Output ('Totale casi=' + $guide.Range('B16').Value2 + ', da eseguire=' + $guide.Range('B17').Value2)
    if ($guide.Range('B16').Value2 -ne 29 -or $guide.Range('B17').Value2 -ne 29) { throw 'Conteggi iniziali errati' }
    Write-Output ('Convalida esiti=' + $tests.Range('H5').Validation.Formula1)
    $tests.Range('H5').Value2 = 'Superato'
    $excelApp.CalculateFull()
    if ($guide.Range('B17').Value2 -ne 28 -or $guide.Range('B18').Value2 -ne 1) { throw 'Formule degli esiti non aggiornate' }
    Write-Output 'Formule riepilogo: aggiornamento verificato, modifica di prova non salvata.'
    $book.Close($false)
} finally {
    if ($null -ne $excelApp) { $excelApp.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excelApp) }
}
