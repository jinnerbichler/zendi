import $ from 'jquery';
import '../img/stellar-rocket-300.png'
import '../img/logo_white.png'

import '../css/main.scss';
import {
    postSendToken,
    postLogin,
    getDepositAddress,
    getDashboardTransactions,
    postTriggerTransactionExecution,
    postTriggerWithdrawExecution,
    getBalance
} from './api';
import 'materialize-css';
import {showMessageBox, hideMessageBox} from "./common";
import * as EmailValidator from 'email-validator';

$(document).ready(function () {
    $('select').material_select();
});

$('#send-form').submit(function (event) {
    event.preventDefault();

    // validate form
    const form = this;
    const formData = new FormData(form);
    const amount = formData.get('amount');
    if (EmailValidator.validate(formData.get('sender_mail')) === false) {
        showMessageBox(`Sender's mail address is invalid`, 'error');
        return false;
    }
    if (EmailValidator.validate(formData.get('receiver_mail')) === false) {
        showMessageBox(`Receiver's mail address is invalid`, 'error');
        return false;
    }
    if (!amount || amount === '0') {
        showMessageBox(`Invalid amount`, 'error');
        return false;
    }

    // hide message box after validation
    hideMessageBox();

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

$('#withdraw-form').submit(function (event) {
    event.preventDefault();

    const form = this;

    hideMessageBox();
    $('#send-tokens').hide();
    $('.progress').show();

    postTriggerWithdrawExecution(form)
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


function initPriceConversion() {

    function updateFiat(price_usd) {
        const stellar_amount = Number($('#id_amount').val());
        const usd_value = stellar_amount * price_usd;
        $('#fiat_amount').val(Math.round(usd_value * 100) / 100 + ' USD');
    }

    $.getJSON('https://api.coinmarketcap.com/v1/ticker/stellar/', function (json_ticker) {

        const price_usd = json_ticker[0].price_usd;
        console.log('Fetched Lumen ticker price: ' + price_usd + ' USD/XLM');

        $('#id_amount').on('input propertychange paste', function () {
            updateFiat(price_usd);
        });
    });
}


// global exports
const bundle = {};
bundle.showMessageBox = showMessageBox;
bundle.fetchDepositAddress = fetchDepositAddress;
bundle.triggerTransactionExecution = triggerTransactionExecution;
bundle.fetchDashboardTransactions = fetchDashboardTransactions;
bundle.fetchBalance = fetchBalance;
bundle.initCollapsible = initCollapsible;
bundle.initPriceConversion = initPriceConversion;
window.bundle = bundle;

