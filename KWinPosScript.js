function init() {
	workspace.cursorPosChanged.connect(sendCursorPos);
}

function sendCursorPos(){
	callDBus(
		"org.pythonmacro.Cursor", "/", "local.py.main.CursorReceiver", "Send", workspace.cursorPos.x, workspace.cursorPos.y
	);
}

init();
