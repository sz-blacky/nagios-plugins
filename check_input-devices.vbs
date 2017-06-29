' Check that at least one keyboard and one mouse is connected to the computer
'
' The script returns CRIT if a working keyboard or mouse was not found and
' lists the devices.

Set objWMI = GetObject("winmgmts:")
hadErrors = false

Set keyboards = objWMI.ExecQuery("SELECT ConfigManagerErrorCode, Caption FROM Win32_Keyboard WHERE ConfigManagerErrorCode=0")
If keyboards.Count = 0 Then
	WScript.Echo "No working keyboard found"
	hadErrors = true
Else
	For Each keyboard In keyboards
		WScript.Echo keyboard.Caption
	Next
End If

Set mice = objWMI.ExecQuery("SELECT ConfigManagerErrorCode, Caption FROM Win32_PointingDevice WHERE ConfigManagerErrorCode=0")
If mice.Count = 0 Then
	WScript.Echo "No working mouse found"
	hadErrors = true
Else
	For Each mouse In mice
			WScript.Echo mouse.Caption
	Next
End If

If hadErrors Then
	WScript.Quit 1
Else
	WScript.Quit 0
End If
