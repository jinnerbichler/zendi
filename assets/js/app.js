import $ from 'jquery'
import {toast} from 'materialize-css'
import '../css/main.scss';
import {postSendToken} from './api-service';
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

