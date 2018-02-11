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

function postTriggerWithdrawExecution(form) {
    return fetch('/withdraw', {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
    }).then(logging)
        .then(checkStatus)
        .then(parseJSON)
        .then(clientSideRedirect)
}

function getDepositAddress() {
    return fetch('/new_address', {
        method: 'GET',
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(parseJSON)
}


function getDashboardTransactions(page, cached) {
    return fetch(`/dashboard_transactions_ajax?page=${page}&cached=${cached}`, {
        method: 'GET',
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(extractText)
}

function getBalance() {
    return fetch('/balance', {
        method: 'GET',
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)
        .then(parseJSON)
}

function postFeedback(form) {
    return fetch('/feedback', {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
    }).then(checkStatus)
        .then(logging)

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
        let new_url = response['redirect_url'];
        if ('replace' in response && response['replace'])
            window.location.replace(new_url);
        else
            window.location.href = new_url;
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
    return response.json();
}

function extractText(response) {
    return response.text();
}

export {
    postSendToken,
    postLogin,
    getDepositAddress,
    getDashboardTransactions,
    postTriggerTransactionExecution,
    postTriggerWithdrawExecution,
    getBalance,
    postFeedback
}