"use strict;"

// Set the parameters for the stimuli
// 24-inch monitor; 1920 x 1080 resolution
// 1 pixel: 0.277 mm

// Radius of each dot: 0.15 deg: 5.6 pixels
const dotRadius = 6; //Radius of each dot in pixels
const socialRadius = 20;

// Radius of the aperture: 5.0 deg
// Radius of the outer circle: 5.3 deg 
const apertureRadius = 190;
const outerRadius = 200;
const optionSize = 20;
const optionDodge = 40;

const backgroundColor = "black"; //Color of the background
const outerCenterX = window.innerWidth / 2; // The x-coordinate of center of the aperture on the screen, in pixels
const outerCenterY = window.innerHeight / 2; // The y-coordinate of center of the aperture on the screen, in pixels

// Fixation Cross Parameters
const fixationCrossSize = 40;  //The width of the fixation cross in pixels; 0.5 degs
const fixationCrossColor = "white"; //The color of the fixation cross
const fixationCrossThickness = 2; //The thickness of the fixation cross, must be positive number above 1

// Task parameters from Python code
const phase = js_vars.phase;
const fps = js_vars.fps;
const colorPos = js_vars.color_pos;
const nDots = js_vars.n_dots; //Number of dots
const answer = js_vars.answer;
const nBlueList = JSON.parse(js_vars.n_blue);
const nRedList = JSON.parse(js_vars.n_red);
const interval = Math.round(1000 / fps);
const iti = 1000;
const seed = js_vars.seed;

// Setting a random seed
Math.seedrandom(seed);

// Time-limit
const timeLimit = 10; // seconds
const feedbackDuration = 500; // milliseconds

//////////////////////////////////////
//--------Set up Canvas begin-------//
//////////////////////////////////////

//Create a canvas element and append it to the DOM
let canvas = document.createElement("canvas");
document.body.appendChild(canvas);
let body = document.body

//Remove the margins and paddings of the display_element
body.style.margin = 0;
body.style.padding = 0;
body.style.backgroundColor = backgroundColor; //Match the background of the display element to the background color of the canvas so that the removal of the canvas at the end of the trial is not noticed

//Remove the margins and padding of the canvas
canvas.style.margin = 0;
canvas.style.padding = 0;
// use absolute positioning in top left corner to get rid of scroll bars
canvas.style.position = "absolute";
canvas.style.top = 0;
canvas.style.left = 0;
canvas.style.cursor = "none";

//Get the context of the canvas so that it can be painted on.
let ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = true;

//Declare variables for width and height, and also set the canvas width and height to the window width and height
const canvasWidth = canvas.width = window.innerWidth;
const canvasHeight = canvas.height = window.innerHeight;

//Set the canvas background color
canvas.style.backgroundColor = backgroundColor;


/////////////////////////////////////// 
// Define the data set for the trial //
///////////////////////////////////////

//Initialize object to store the response data. Default values of -1 are used if the trial times out and the subject has not pressed a valid key
let response = {
    phase: phase,
    answer: answer,
    choice_self: "miss",
    rt_self: -1,
    frame_self: -1,
    choice_other: "miss",
    rt_other: -1,
    frame_other: -1,
    type: "data",
    time_start: "0"
}

// Timer to measure response time in the trial
let startTime;
let endTime;
let socialInfoTime;

////////////////////////////////////////////////////
// Define the functions for stimulus presentation //
////////////////////////////////////////////////////

//Generates a random number (with decimals) between 2 values
function randomNumberBetween(lowerBound, upperBound) {
    return lowerBound + Math.random() * (upperBound - lowerBound);
}

// Functions for the keyboard

// Detect key press during the trial.
// If the keypress is detected, kill the trial
let doneSelf = false;
let doneOther;
if (phase === "second") {
    doneOther = false;
} else {
    doneOther = true;
}

function doneBoth() {
    if (doneSelf && doneOther) {
        setTimeout(endTrial, feedbackDuration);
    }
}

function onKeyPress(keyPressed) {
    endTime = performance.now();
    if (keyPressed === "left") {
        if (colorPos === "redblue") {
            response.choice_self = "red";
        } else {
            response.choice_self = "blue";
        }
    } else {
        if (colorPos === "redblue") {
            response.choice_self = "blue";
        } else {
            response.choice_self = "red";
        }
    }
    response.rt_self = endTime - startTime;
    response.frame_self = nFrame;
    if (phase === "second") {
        liveSend(response);
    }
    drawResponse(keyPressed, response.choice_self);
    doneSelf = true;
    doneBoth();
    drawTimer(startTime, performance.now());
}

function keyPressEvent(e) {
    if (e.code === "ArrowLeft" && keyHeld === false && doneSelf === false) {
        keyPressed = "left";
        onKeyPress("left");
    } else if (e.code === "ArrowRight" && keyHeld === false && doneSelf === false) {
        keyPressed = "right";
        onKeyPress("right");
    }
    return false; 
}

function keyUpEvent(e) {
    if (e.code === "ArrowLeft" || e.code === "ArrowRight") {
        keyHeld = false;
    }
    return false; 
}

function keyHeldEvent(e) {
    if (e.code === "ArrowLeft" || e.code === "ArrowRight") {
        keyHeld = true;
    }
    return false; 
}

function drawFixationCross(lineWidth = 6) {
    
    //Horizontal line
    ctx.beginPath();
    ctx.strokeStyle = "white";
    ctx.lineWidth = fixationCrossThickness;
    ctx.moveTo(canvasWidth / 2 - fixationCrossSize / 2, canvasHeight / 2);
    ctx.lineTo(canvasWidth / 2 + fixationCrossSize / 2, canvasHeight / 2);
    ctx.stroke();
    
    //Vertical line
    ctx.beginPath();
    ctx.strokeStyle = "white";
    ctx.lineWidth = fixationCrossThickness;
    ctx.moveTo(canvasWidth / 2, canvasHeight / 2 - fixationCrossSize / 2);
    ctx.lineTo(canvasWidth / 2, canvasHeight / 2 + fixationCrossSize / 2);
    ctx.stroke();
}

function drawOuterCircle(color = "white", lineWidth = 2) {
    ctx.beginPath();
    ctx.arc(outerCenterX, outerCenterY, outerRadius, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
}

function drawOptions() {
    xpos_left = outerCenterX - outerRadius - optionDodge;
    xpos_right = outerCenterX + outerRadius + optionDodge;
    ypos = outerCenterY;
    ctx.beginPath();
    if (colorPos === "redblue") {
        ctx.arc(xpos_left, ypos, optionSize, 0, Math.PI * 2);
        ctx.strokeStyle = "red";
        ctx.stroke();
        if (doneOther && phase === "second" && response.choice_other === "red") {
            ctx.fillStyle = "red";
            ctx.fill()
        }
        ctx.beginPath();
        ctx.arc(xpos_right, ypos, optionSize, 0, Math.PI * 2);
        ctx.strokeStyle = "rgb(0, 57, 255)";
        ctx.stroke()
        if (doneOther && phase === "second" && response.choice_other === "blue") {
            ctx.fillStyle = "rgb(0, 57, 255)";
            ctx.fill()
        }
    } else {
        ctx.arc(xpos_left, ypos, optionSize, 0, Math.PI * 2);
        ctx.strokeStyle = "rgb(0, 57, 255)";
        ctx.stroke();
        if (doneOther && phase === "second" && response.choice_other === "blue") {
            ctx.fillStyle = "rgb(0, 57, 255)";
            ctx.fill()
        }
        ctx.beginPath();
        ctx.arc(xpos_right, ypos, optionSize, 0, Math.PI * 2);
        ctx.strokeStyle = "red";
        ctx.stroke()
        if (doneOther && phase === "second" && response.choice_other === "red") {
            ctx.fillStyle = "red";
            ctx.fill()
        }
    }
}

function drawResponse(keyPressed, color = "white") {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    xpos_left = outerCenterX - outerRadius - optionDodge - optionSize - 5;
    xpos_right = outerCenterX + outerRadius + optionDodge - optionSize - 5;
    ypos = outerCenterY - optionSize - 5;
    ctx.beginPath();
    ctx.strokeStyle = "white"
    if (colorPos === "redblue") {
        if (response.choice_self === "red") {
            ctx.lineWidth = 2;
            ctx.strokeRect(xpos_left, ypos, optionSize * 2 + 10, optionSize * 2 + 10);
            ctx.stroke();
        } else {
            ctx.lineWidth = 2;
            ctx.strokeRect(xpos_right, ypos, optionSize * 2 + 10, optionSize * 2 + 10);
            ctx.stroke();
        }
    } else {
        if (response.choice_self === "red") {
            ctx.lineWidth = 2;
            ctx.strokeRect(xpos_right, ypos, optionSize * 2 + 10, optionSize * 2 + 10);
            ctx.stroke();
        } else {
            ctx.lineWidth = 2;
            ctx.strokeRect(xpos_left, ypos, optionSize * 2 + 10, optionSize * 2 + 10);
            ctx.stroke();
        }
    }
    drawOuterCircle();
    drawOptions();
    if (nowTime - startTime < timeLimit * 1000) {
        drawFixationCross();
    }
}

function drawSocial() {
    xpos_left = outerCenterX - outerRadius - optionDodge;
    xpos_right = outerCenterX + outerRadius + optionDodge;
    ypos = outerCenterY;
    ctx.beginPath();
    if (colorPos === "redblue") {
        if (response.choice_other === "red") {
            ctx.arc(xpos_left, ypos, optionSize, 0, Math.PI * 2);
            ctx.fillStyle = "red";
            ctx.fill();
        } else {
            ctx.arc(xpos_right, ypos, optionSize, 0, Math.PI * 2);
            ctx.fillStyle = "rgb(0, 57, 255)";
            ctx.fill();
        }
    } else {
        if (response.choice_other === "red") {
            ctx.arc(xpos_right, ypos, optionSize, 0, Math.PI * 2);
            ctx.fillStyle = "red";
            ctx.fill();
        } else {
            ctx.arc(xpos_left, ypos, optionSize, 0, Math.PI * 2);
            ctx.fillStyle = "rgb(0, 57, 255)";
            ctx.fill();
        }
    }
}

function drawTimer(startTime, nowTime) {
    ctx.fillStyle = "white";
    ctx.font = "36pt Roboto";
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    if (nowTime - startTime > timeLimit * 1000) {
        ctx.fillText(String(Math.ceil(((timeLimit + 3) * 1000 + startTime - nowTime) / 1000)), outerCenterX, outerCenterY);
    }
}

function drawDots(n = nDots) {
    dotX = [];
    dotY = [];
    for (var i = 0; i < n; i++) {
        while (true) {
            r = randomNumberBetween(fixationCrossSize / 2 + dotRadius, apertureRadius);
            theta = randomNumberBetween(0, Math.PI * 2);
            x = Math.round(r * Math.cos(theta) + outerCenterX);
            y = Math.round(r * Math.sin(theta) + outerCenterY);
            if (i === 0) {
                dotX.push(x);
                dotY.push(y);
                break
            }
            let flgOverlap = true;
            for (let j = 0; j < dotX.length; j++) {
                distance = Math.sqrt((dotX[j] - x) ** 2 + (dotY[j] - y) ** 2);
                if (distance < dotRadius * 2) {
                    flgOverlap = false;
                }
            }
            if (flgOverlap) {
                dotX.push(x);
                dotY.push(y);
                break
            }
        }
        if (doneSelf === false) {
            // Drawdot
            ctx.beginPath();
            ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
            if (i < nBlueList[nFrame]) {
                ctx.fillStyle = "rgb(0, 57, 255)";
            } else {
                ctx.fillStyle = "red";
            }
            ctx.fill();
        }
    }
    nFrame += 1;
}

function drawNothing() {
    ctx.beginPath();
    ctx.arc(0, 0, 0, 0, Math.PI * 2);
    ctx.stroke();
}

let requestID;
function drawAnimation() {
    if (nLoop % (60 / fps) === 0 && nLoop < timeLimit * 60) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        requestID = requestAnimationFrame(drawAnimation);
        if (nLoop < timeLimit * 60) {
            drawFixationCross();
            drawDots();
        }
        drawOuterCircle(color = "white", lineWidth = 2);
        drawOptions();
        if (doneOther && phase == "second") {
            drawSocial();
        }
        if (doneSelf) {
            drawResponse(keyPressed, color = response.choice_self);
        }
        // drawTimer(startTime, performance.now());
        if (nLoop === 0) {
            body.removeEventListener("keydown", keyHeldEvent);
            body.addEventListener("keyup", keyUpEvent);
            body.addEventListener("keydown", keyPressEvent);
            startTime = performance.now();
            startTimeGlobal = Date.now();
            startTimeGlobal = startTimeGlobal.toString(16);
        }
    } else if (nLoop % (60 / fps) !== 0 && nLoop < timeLimit * 60) {
        requestID = requestAnimationFrame(drawAnimation);
        drawNothing();
    }
    nowTime = performance.now();
    if (nLoop >= timeLimit * 60 && nLoop < timeLimit * 60 + 3 * 60) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        requestID = requestAnimationFrame(drawAnimation);
        drawOuterCircle(color = "white", lineWidth = 2);
        drawOptions();
        if (doneOther && phase == "second") {
            drawSocial();
        }
        if (doneSelf) {
            drawResponse(keyPressed, color = response.choice_self);
        }
        drawTimer(startTime, nowTime);
    }
    if (nLoop === timeLimit * 60 + 3 * 60) {
        endTrial();
    }
    nLoop += 1;
}

function liveRecv(data) {
    doneOther = true;
    socialInfoTime = performance.now();
    response.choice_other = data.response.choice_self;
    drawSocial();
    response.rt_other = socialInfoTime - startTime;
    response.frame_other = nFrame;
    doneBoth();
}

function recordData(response) {
    $("<input>").attr({
        type: "hidden",
        name: "taskdata",
        value: JSON.stringify(response)
    }).appendTo("#form");
    $("#form").submit();
}

function endTrial() {
    response.time_start = startTimeGlobal;
    recordData(response);
    body.removeEventListener("keyup", keyUpEvent);
    body.removeEventListener("keydown", keyPressEvent);
    body.innerHTML = "";
}

// Run the trial
body.addEventListener("keydown", keyHeldEvent);
let keyHeld = false;
let keyPressed;
let nLoop = 0;
let nFrame = 0;
let flgSync1 = true;
let flgSync2 = true;
let startTimeGlobal = 0;
drawFixationCross();
setTimeout(drawAnimation, iti);
