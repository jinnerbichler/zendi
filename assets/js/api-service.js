function postSendToken(form) {
    return fetch('/send-tokens', {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin'
    }).then(checkStatus)
        .then(parseJSON)
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

export {postSendToken}