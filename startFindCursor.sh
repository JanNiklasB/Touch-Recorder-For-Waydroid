SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
num=$(qdbus org.kde.KWin /Scripting loadScript $(realpath ./KWinPosScript.js))
qdbus org.kde.KWin /Scripting/Script$num run > /dev/null
echo $num