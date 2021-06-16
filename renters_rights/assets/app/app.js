export function toggleVisibility(x, revert=false, timeout=0) {
    let element = document.getElementById(x);
	if (element.style.display == 'none' || element.classList.contains('hidden')) {
		element.style.display = '';
		element.classList.remove('hidden');
	} else {
		element.classList.add('hidden');
	}
	if (revert && timeout) {
	    setTimeout(window.app.toggleVisibility, timeout, x);
	}
}

export function toggleRotate(x, degrees) {
    let element = document.getElementById(x);
    let rotation = `rotate(${degrees}deg)`;
    if (element.style.transform == rotation) {
	    element.style.transform = '';
	} else {
	    element.style.transform = rotation;
	}
}

export function copyTextToClipboard(x) {
    let element = document.getElementById(x);
    let text = element.value;
    if (!navigator.clipboard) {
        var textArea = document.createElement("textarea");
        textArea.value = text;

        // Avoid scrolling to bottom
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            var successful = document.execCommand('copy');
            var msg = successful ? 'successful' : 'unsuccessful';
            console.log('Fallback: Copying text command was ' + msg);
        } catch (err) {
            console.error('Fallback: Oops, unable to copy', err);
        }

        document.body.removeChild(textArea);
        return;
    }
    navigator.clipboard.writeText(text).then(function() {
        console.log('Async: Copying to clipboard was successful!');
    }, function(err) {
        console.error('Async: Could not copy text: ', err);
    });
}