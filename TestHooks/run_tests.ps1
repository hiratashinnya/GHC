
$scripts = @(
    "workspace_utils",
    "tool_input",
    "hook_payload",
    "debug_logging",
    "check_phase_gate",
    "post_tool_dashboard_sync",
    "tool_input_spy"
)

$summary = @()
$totalPassed = 0
$totalFailed = 0

foreach ($s in $scripts) {
    Set-Location "$PSScriptRoot\$s"
    $out = python -m unittest "test_$s" -v 2>&1 | Out-String

    if ($out -match "Ran (\d+) test") {
        $count = [int]$Matches[1]
    } else {
        $count = 0
    }

    if ($out -match "\nOK") {
        $status = "PASS"
        $totalPassed += $count
    } else {
        $status = "FAIL"
        $totalFailed += $count
        Write-Host $out
    }

    $summary += [PSCustomObject]@{
        Script  = $s
        Tests   = $count
        Status  = $status
    }
}

Set-Location $PSScriptRoot

Write-Host "`n===== SUMMARY ====="
$summary | Format-Table -AutoSize

$total = $totalPassed + $totalFailed
Write-Host "Result: $totalPassed / $total PASS"

if ($totalFailed -gt 0) { exit 1 } else { exit 0 }
