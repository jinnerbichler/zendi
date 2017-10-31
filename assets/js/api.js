// #####################################################################
// ###################### Send Token Request ###########################
// #####################################################################
function postSendToken(form) {
    return fetch('/send-tokens', {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(parseJSON)
        .then(clientSideRedirect)
}

function postTriggerTransactionExecution(params) {
    return fetch('/send-tokens-exec', {
        method: 'POST',
        body: params,
        credentials: 'same-origin',
    }).then(logging)
        .then(checkStatus)
        .then(parseJSON)
        .then(clientSideRedirect)
}


function postLogin(form, url) {
    return fetch(url, {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(parseJSON)
        .then(clientSideRedirect)
}


function getNewAddress() {
    return fetch('/new_address', {
        method: 'GET',
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(parseJSON)
}

// #####################################################################
// ###################### Response Callbacks ###########################
// #####################################################################
function logging(response) {
    console.log(`Response => URL: ${response.url}, Status: ${response.status}, Text: ${response.statusText}`);
    return response;
}

function clientSideRedirect(response) {
    if ('redirect_url' in response) {
        window.location.href = response['redirect_url'];
        // dummy to stop execution until redirect
        return new Promise(function (resolve) {
            setTimeout(() => {
                throw new Error('Should never be executed ERROR!!');
            }, 10000)
        });
    }
    return response;
}

function checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
        return response
    } else {
        const error = new Error(response.statusText);
        error.response = response;
        throw error
    }
}

function parseJSON(response) {
    return response.json()
}

export {postSendToken, postLogin, getNewAddress, postTriggerTransactionExecution}