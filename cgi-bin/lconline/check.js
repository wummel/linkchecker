// check url validity
function isValid (thisForm) {
    if (thisForm.url.value=="" || thisForm.url.value=="http://") {
        alert(gettext("Empty URL was given."));
        thisForm.url.select();
        thisForm.url.focus();
        return false;
    }
    if (!checkSyntax(thisForm.url.value)) {
        alert(gettext("Invalid URL was given."));
        thisForm.url.select();
        thisForm.url.focus();
        return false;
    }
    return true;
}

// check url syntax
function checkSyntax (url) {
    var syntax = /^https?:\/\/[-_a-zA-Z0-9.\/=%?~]+$/;
    return syntax.test(url);
}
