# Minimize every visible top-level window, so a demo records against a bare
# desktop.
#
# Two separate reasons, both fatal to a take: the recorder grabs screen PIXELS
# of fman's window rect, so anything drawn over it is burned into every frame -
# and demo mode pins DEMO_OPACITY at 0.8, so whatever is BEHIND fman shows
# through it as well. A leftover window puts its contents, file names included,
# on camera without ever covering fman.
#
# This replaces `(New-Object -ComObject Shell.Application).MinimizeAll()`, which
# is the Win+D shortcut: it toggles rather than minimizes, and the shell ignores
# it outright in some states. It returned success while leaving windows on
# screen. Enumerating the windows and minimizing each one is deterministic.

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class FmanDemoWindows {
	public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
	[DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
	[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
	[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
	[DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
	[DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, StringBuilder name, int max);
	[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$SW_MINIMIZE = 6

# The desktop itself and the taskbar are windows too, and minimizing them would
# black out the screen rather than clear it.
$shellClasses = @('Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd',
                  'Button', 'NotifyIconOverflowWindow', 'Windows.UI.Core.CoreWindow')

$minimized = 0
$callback = [FmanDemoWindows+EnumWindowsProc] {
	param($hWnd, $lParam)
	if ([FmanDemoWindows]::IsWindowVisible($hWnd) -and -not [FmanDemoWindows]::IsIconic($hWnd)) {
		# A top-level window with no title is a helper/tool window, not
		# something the user can see content in.
		if ([FmanDemoWindows]::GetWindowTextLength($hWnd) -gt 0) {
			$name = New-Object System.Text.StringBuilder 256
			[void][FmanDemoWindows]::GetClassName($hWnd, $name, $name.Capacity)
			if ($shellClasses -notcontains $name.ToString()) {
				[void][FmanDemoWindows]::ShowWindow($hWnd, $SW_MINIMIZE)
				$script:minimized++
			}
		}
	}
	return $true
}
[void][FmanDemoWindows]::EnumWindows($callback, [IntPtr]::Zero)

Write-Host "Minimized $minimized window(s) before recording."

# ShowWindow returns while the shell is still animating the windows away. fman
# is launched immediately after this script, so give the desktop time to
# actually clear before its window is mapped over it.
Start-Sleep -Milliseconds 1200
