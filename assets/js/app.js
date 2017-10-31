import $ from 'jquery';
import '../img/iota-logo.png';
import '../css/main.scss';
import {postSendToken, postLogin, getNewAddress, postTriggerTransactionExecution} from './api';
import 'materialize-css';
import {showMessageBox, hideMessageBox} from "./common";

$('#send-form').submit(function (event) {
    event.preventDefault();

    hideMessageBox();

    const form = this;
    postSendToken(form)
        .then((jsonResponse) => {
            const messageType = 'error' in jsonResponse ? 'error' : 'info';
            showMessageBox(jsonResponse['message'], messageType);
            form.reset();
        })
        .catch((error) => {
            showMessageBox(`Error ${error}`, 'error');
        });
});

$('#login-form').submit(function (event) {
    event.preventDefault();

    hideMessageBox();

    const form = this;
    postLogin(form, event.target.baseURI)
        .then((jsonResponse) => {
            const messageType = 'error' in jsonResponse ? 'error' : 'info';
            showMessageBox(jsonResponse['message'], messageType);
            form.focus();
        })
        .catch((error) => {
            showMessageBox(`Error ${error}`, 'error');
        });
});

function fetchNewAddress(callback) {
    getNewAddress()
        .then((jsonResponse) => {
            const newAddress = jsonResponse['address'];
            callback(newAddress);
        })
        .catch((error) => {
            // ToDO: Handle this case
        });
}

function triggerTransactionExecution() {
    const url = new URL(window.location);
    const params = new URLSearchParams(url.search);
    postTriggerTransactionExecution(params).then((response) => {
       console.log('Successfully executed transaction: ' + JSON.stringify(response))
    });
}

// global exports
const bundle = {};
bundle.showMessageBox = showMessageBox;
bundle.fetchNewAddress = fetchNewAddress;
bundle.triggerTransactionExecution = triggerTransactionExecution;
window.bundle = bundle;

