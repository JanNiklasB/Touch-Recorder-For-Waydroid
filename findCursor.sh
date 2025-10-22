num=$(qdbus org.kde.KWin /Scripting loadScript /home/jnb/Documents/PythonMacro/KWinPosScript.js)
qdbus org.kde.KWin /Scripting/Script$num run > /dev/null
journalctl --user --since $(date +"%H:%M:%S") -f --output=cat --grep "Position: _" -n 1&
JOURNAL_PID=$!
sleep 0.01
qdbus org.kde.KWin /Scripting/Script$num stop > /dev/null
kill $JOURNAL_PID
