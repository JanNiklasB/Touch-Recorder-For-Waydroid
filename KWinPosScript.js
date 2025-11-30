function init() {
	workspace.cursorPosChanged.connect(sendCursorPos);
}

function sendCursorPos(){
	callDBus(
		"org.pythonmacro.Cursor", "/", "", "Send", workspace.cursorPos.x, workspace.cursorPos.y
	);
}

init();
