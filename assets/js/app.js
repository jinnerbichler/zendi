import $ from 'jquery';
import '../img/stellar-rocket-300.png'

import '../css/main.scss';
import {
    postSendToken,
    postLogin,
    getDepositAddress,
    getDashboardTransactions,
    postTriggerTransactionExecution,
    getBalance
} from './api';
import 'materialize-css';
import {showMessageBox, hideMessageBox} from "./common";

$(document).ready(function () {
    $('select').material_select();
});

$('#send-form').submit(function (event) {
    event.preventDefault();

    hideMessageBox();

    const form = this;
    postSendToken(form)
        .then((jsonResponse) => {
            const messageType = 'error' in jsonResponse ? 'error' : 'info';
            showMessageBox(jsonResponse['message'], messageType);

            if ('error' in jsonResponse === false)
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

function fetchDepositAddress(callback) {
    getDepositAddress()
        .then((jsonResponse) => {
            const newAddress = jsonResponse['address'];
            callback(newAddress, null);
        })
        .catch((error) => {
            callback(null, error);
        });
}

function triggerTransactionExecution() {
    const url = new URL(window.location);
    const params = new URLSearchParams(url.search);
    postTriggerTransactionExecution(params).then((response) => {
        console.log('Successfully executed transaction: ' + JSON.stringify(response))
    });
}

function fetchDashboardTransactions(page, cached, callback) {
    console.log(`Fetching recent transactions (page=${page})...`);
    getDashboardTransactions(page, cached)
        .then((transactionsHtml) => {
            callback(transactionsHtml, null);
        })
        .catch((error) => {
            callback(null, error);
        });
}

function fetchBalance(callback) {
    console.log('Fetching users balance...');
    getBalance()
        .then((transactionsHtml) => {
            callback(transactionsHtml, null);
        })
        .catch((error) => {
            callback(null, error);
        });
}

function initCollapsible() {
    $('.collapsible').collapsible();
}

// global exports
const bundle = {};
bundle.showMessageBox = showMessageBox;
bundle.fetchDepositAddress = fetchDepositAddress;
bundle.triggerTransactionExecution = triggerTransactionExecution;
bundle.fetchDashboardTransactions = fetchDashboardTransactions;
bundle.fetchBalance = fetchBalance;
bundle.initCollapsible = initCollapsible;
window.bundle = bundle;

