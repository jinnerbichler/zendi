function form2Dict(form) {
    const result = {};
    $.each(form.serializeArray(), function () {
        result[this.name] = this.value;
    });
    return result;
}

function showMessageBox(text, type = 'info') {

    const messageBox = $('#message-box');

    // set proper CSS classes
    messageBox.removeClass('info error');
    messageBox.addClass(type);

    messageBox.find('.close').click(function () {
        hideMessageBox();
    });

    // set text and show
    messageBox.find('.content').text(text);
    messageBox.fadeIn();
}

function hideMessageBox() {

    const messageBox = $('#message-box');
    messageBox.hide();
}


export {form2Dict, showMessageBox, hideMessageBox}