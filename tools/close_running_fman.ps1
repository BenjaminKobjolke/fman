# freeze() cannot replace target\fman while a process is running from it.
# Ask Windows to close its window so fman can save its session normally.
param(
    [Parameter(Mandatory = $true)][string]$Directory,
    [int]$TimeoutSeconds = 15
)

$prefix = [IO.Path]::GetFullPath($Directory).TrimEnd('\') + '\'
$running = @(Get-Process | Where-Object {
    $_.Path -and $_.Path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
})
if ($running.Count -eq 0) { exit 0 }

foreach ($process in $running) {
    Write-Host "Closing $($process.ProcessName) (PID $($process.Id))..."
    # Never kill it: a file operation may still be in progress.
    [void]$process.CloseMainWindow()
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline -and ($running | Where-Object { -not $_.HasExited })) {
    Start-Sleep -Milliseconds 200
}

$left = @($running | Where-Object { -not $_.HasExited })
if ($left.Count -gt 0) {
    foreach ($process in $left) {
        Write-Host "ERROR: $($process.ProcessName) (PID $($process.Id)) is still running from $prefix"
    }
    Write-Host "Close it by hand (a dialog may be waiting for an answer), then build again."
    exit 1
}
exit 0
