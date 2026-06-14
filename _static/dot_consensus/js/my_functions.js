"use strict";
console.log("a");
const duration_feedback = 1500;

function move_to_next() {
    $('<input>').attr({
        type: 'hidden',
        name: 'next_trial',
        value: JSON.stringify("a")
    }).appendTo('#form');
    $('#form').submit();
}

function next_after(delay) {
    setTimeout(move_to_next, delay);
}

let iframe = window.document.querySelector("iframe");

function isSafari() {
    let ua = navigator.userAgent.toLowerCase();
    return ((ua.indexOf("safari") != -1) && (ua.indexOf("chrome") === -1));
}

function setIframeFocus() {
    iframe.focus();
    if(isSafari()) {
    window.setTimeout(function() {
        iframe.contentWindow.focus();
    }, 100)
    }
}

iframe.onload = setIframeFocus;
