function goBack() {
    if (document.referrer.indexOf(window.location.host) !== -1) {
        history.go(-1);
        return false;
    }
}
