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


function getDashboardTransactions() {
    return fetch('/dashboard_transactions_ajax', {
        method: 'GET',
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(extractText)
}

// #####################################################################
// ###################### Response Callbacks ###########################
// #####################################################################
function logging(response) {
    console.log(`Response => URL: ${response.url}, Status: ${response.status}, Text: ${response.statusText}`);
    return response;
}

function clientSideRedirect(jsonObj) {
    if ('redirect_url' in jsonObj) {
        window.location.href = jsonObj['redirect_url'];
        // dummy to stop execution until redirect
        return new Promise(function (resolve) {
            setTimeout(() => {
                throw new Error('Should never be executed ERROR!!');
            }, 10000)
        });
    }
    return jsonObj;
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
    return response.json();
}

function extractText(response) {
    return response.text();
}

export {postSendToken, postLogin, getNewAddress, getDashboardTransactions}