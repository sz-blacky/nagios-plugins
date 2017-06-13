Option Explicit

' Check if an up to date and actively running anti virus program is installed on the host.
'
' This script uses the SecurityCenter2 WMI namespace (available since Windows Vista) to check
' if an up to date anti virus application is installed and running on the host.
' The script will return
'	* UNKNOWN if the SecurityCenter2 namespace is not supported
'	* CRITICAL if no anti-virus is found on the target system or any of them is installed but inactive
'	* WARNING if any of the anti-virus is not up to date
'	* OK otherwise
'
' Please note that the script filters the objects returned by WMI for actual Anti-virus software -
' thus, software identifing as anything else is not taken into account.
'
' For more information about the meaning of various fields, see
' https://gallery.technet.microsoft.com/scriptcenter/Get-the-status-of-4b748f25

Function GetBit(lngValue, BitNum)
     Dim BitMask
     If BitNum < 32 Then BitMask = 2 ^ (BitNum - 1) Else BitMask = "&H80000000"
	GetBit = CBool(lngValue AND BitMask)
End Function

Function ntoa(nNum, iBase)
	ntoa = "0"
	If nNum Then
		ntoa = Mid( "-", Sgn( nNum ) + 2 ) + ntoaPos( Abs( nNum ), iBase )
	End If
End Function

Function ntoaPos(nNum, iBase)
	If nNum >= 1 Then
		Dim nD : nD = Fix(nNum / iBase)
		Dim nM : nM = nNum - nD * iBase
		ntoaPos =  ntoaPos(nD, iBase) & Mid("0123456789ABCDEFGHIJKLMNOPQRSTUV", 1 + nM, 1)
  End If
End Function

Function LPad(s, l, c)
	Dim n : n = 0
	If l > Len(s) Then
		n = l - Len(s)
	End If
	LPad = String(n, c) & s
End Function

Function GetSecurityCenter2NameSpace()
	On Error Resume Next
	Set GetSecurityCenter2NameSpace = Nothing
	Set GetSecurityCenter2NameSpace = GetObject( "winmgmts:\\" & strComputer & "\root\SecurityCenter2")
End Function

Dim oWMI, colItems, objItem, strComputer, exitStatus
Dim signatureStatusText, productStateText, antiVirusFound
Dim productStateString, providerType, productState, signatureStatus
Dim output
Dim outputText
outputText = Array("OK", "WARNING", "CRITICAL", "UNKNOWN")
strComputer = "."
Set oWMI = GetSecurityCenter2NameSpace
If oWMI Is Nothing Then
	output = "Host does not support the SecurityCenter2 namespace"
	exitStatus = 3
Else
	Set colItems = oWMI.ExecQuery("Select * from AntiVirusProduct")
	exitStatus = 0
	antiVirusFound = false
	output = ""
	For Each objItem in colItems
		productStateString = LPad(ntoa(objItem.productState, 16), 6, "0")
		providerType = Left(productStateString, 2)
		productState = Right(Left(productStateString, 4), 2)
		signatureStatus = Right(Left(productStateString, 6), 2)
			
		If GetBit(CInt(providerType), 3) Then 
			antiVirusFound = true
			If signatureStatus = "00" Then
				signatureStatusText = "is up to date"
			Else
				signatureStatusText = "is not up to date"
				exitStatus = 1
			End If
				
			If productState = "10" Then
				productStateText = "is enabled"
			Else
				productStateText = "is not running"
				exitStatus = 2
			End If
			output = output & objItem.displayName & " " & productStateText & " and " & signatureStatusText & vbCrLf
		End If
	Next

	If Not antiVirusFound Then
		output = "No anti-virus product found"
		exitStatus = 2
	End If
End If
WScript.Echo outputText(exitStatus) & ": " & output
WScript.Quit exitStatus
:install

"C:\Program Files\NSClient++\nscp.exe" settings --set "Check Anti-virus" --path /settings/scheduler/schedules/check_antivirus --key alias
"C:\Program Files\NSClient++\nscp.exe" settings --set check_antivirus --path /settings/scheduler/schedules/check_antivirus --key command
"C:\Program Files\NSClient++\nscp.exe" settings --set "30m" --path /settings/scheduler/schedules/check_antivirus --key interval
"C:\Program Files\NSClient++\nscp.exe" settings --set "NRDP" --path /settings/scheduler/schedules/check_antivirus --key channel
"C:\Program Files\NSClient++\nscp.exe" settings --set "scripts\\check_antivirus.vbs" --path "/settings/external scripts/wrapped scripts" --key "check_antivirus"

net stop nscp
net start nscp
