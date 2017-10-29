import $ from 'jquery';
import '../img/iota-logo.png';
import '../css/main.scss';
import {postSendToken, postLogin} from './api-service';
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
            form.reset();
        })
        .catch((error) => {
            showMessageBox(`Error ${error}`, 'error');
        });
});

// global exports
window.showMessageBox = showMessageBox;

