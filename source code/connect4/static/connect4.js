'use strict'

function getGlobal() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) return
        updateGlobal(xhr)
    }

    xhr.open("GET", "/get-global", true)
    xhr.send()
}

function getGameplay() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) return
        updatePage(xhr)
    }

    xhr.open("GET", "/get-gameplay", true)
    xhr.send()
}

function dropToken(column) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) return
        updatePage(xhr)
    }

    xhr.open("POST", dropTokenURL, true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("column="+column+"&csrfmiddlewaretoken="+getCSRFToken());
}

function updateGlobal(xhr) {
    if (xhr.status == 200) {
        let response = JSON.parse(xhr.responseText)
        changeGlobal(response)
        return
    }

    if (xhr.status == 0) {
        displayError("Cannot connect to server")
        return
    }


    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }

    displayError(response)
}

function updatePage(xhr) {
    if (xhr.status == 200) {
        let response = JSON.parse(xhr.responseText)
        changeColor(response)
        changeGameInfo(response)
        return
    }

    if (xhr.status == 0) {
        displayError("Cannot connect to server")
        return
    }


    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }

    displayError(response)
}

function parseBoard(board) {
    let splitBoard = board.split(",")

    let board_2d = []
    let counter = 0
    for (let r = 0; r < 6; r++) {
        let boardRow = []
        for (let c = 0; c < 7; c++) {
            boardRow.push(splitBoard[counter])
            counter += 1
        }
        board_2d.push(boardRow)
    }
    
    return board_2d
}

function changeColor(response) {
    let board = response['board']
    let player_1_token = response["player_1_token"]
    let player_2_token = response["player_2_token"]

    board = parseBoard(board)

    let radius = 38
    let spacing = 12

    let svg_div = document.getElementById("id_game_board")
    svg_div.innerHTML = ""
    let background = `<rect width="700" height="600" style="fill:rgb(0,0,255)"></rect>`

    svg_div.innerHTML += background

    for (let r = 0; r < 6; r++) {
        for (let c = 0; c < 7; c++) {
            let x = c * 100 + spacing
            let y = r * 100 + spacing
            
            let clipID = `id_clip_${r}_${c}`
            let clipCircle = 
                `<defs>
                    <clipPath id=${clipID}>
                        <circle cx=${x+radius} cy=${y+radius} r=${radius} fill="rgb(0,0,255)" />
                    </clipPath>
                </defs>`
            svg_div.innerHTML += clipCircle

            let padding = 4
            let width = 2*radius + padding
            let height = 2*radius + padding
            let token_x = x - padding/2
            let token_y = y - padding/2
            if (board[r][c] == "1") {
                let new_token = `<g><image href=${player_1_token} clip-path="url(#${clipID})" class="tokens" style="width: ${width}; height: ${height}; x:${token_x}; y:${token_y}" /></g>`
                svg_div.innerHTML += new_token

            } else if (board[r][c] == "2") {
                let new_token = `<g><image href=${player_2_token} clip-path="url(#${clipID})" class="tokens" style="width: ${width}; height: ${height}; x:${token_x}; y:${token_y}" /></g>`
                svg_div.innerHTML += new_token
            } else {
                let new_token = `<g><image href="/static/blank_token.png" clip-path="url(#${clipID})" class="tokens" style="width: ${width}; height: ${height}; x:${token_x}; y:${token_y}" /></g>`
                svg_div.innerHTML += new_token
            }
        }
    }

}

function changeGameInfo(response) {
    let player_1_username = response['player_1_username']
    let player_2_username = response['player_2_username']
    let status = response['status']

    let player_1_pfp = response['player_1_pfp']
    let player_2_pfp = response['player_2_pfp']
    
    let timeLeft = response['timeLeft']

    console.log(status)
    console.log(timeLeft)
    if (status.includes("wins") || status.includes("forfeit")) {
        if (document.getElementById("player_1_surrender_button") != null) {
            document.getElementById("player_1_surrender_button").innerHTML = "<div class='endplaceholder' id='player_1_end_game'></div>"
            
        }
        if (document.getElementById("player_2_surrender_button") != null){
            document.getElementById("player_2_surrender_button").innerHTML = "<div class='endplaceholder' id='player_2_end_game'></div>"
        }
    }

    if (timeLeft == 0) {
        document.getElementById("timer_test").innerHTML = "TIMEOUT"
        let xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return
            updateGlobal(xhr)
        }

        xhr.open("GET", "/time-out", true)
        xhr.send()
    }

    document.getElementById("id_player_2_info").innerHTML = player_2_username
    document.getElementById("id_player_1_info").innerHTML = player_1_username

    document.getElementById("id_player_1_pfp").innerHTML = `<img src=${player_1_pfp} alt="nopfp" width="65" height="65">`
    document.getElementById("id_player_2_pfp").innerHTML = `<img src=${player_2_pfp} alt="nopfp" width="65" height="65">`

    document.getElementById("id_status").innerHTML = status

    document.getElementById("timer_test").innerHTML = Math.floor(timeLeft/2) + " secs"

}

function changeGlobal(response) {
    let active_rooms = response["rooms"]
    let challenges = response["challenge_requests"]
    let game_status = response["game_status"]
    let has_requests = response["has_requests"]

    document.getElementById("id_start_new_game_button").innerHTML = game_status

    let rooms_list = document.getElementById("id_active_room_list")

    if (active_rooms.length == 0 && challenges.length == 0) {
        rooms_list.innerHTML = ""
    }

    const roomTable = document.createElement("table")
    roomTable.setAttribute("id", "id_active_rooms_table")
    for (let i = 0; i < active_rooms.length; i++) {
        let room_id = active_rooms[i].room_id
        let room_player_1_username = active_rooms[i].player_1_username
        let room_row = document.createElement("tr")

        room_row.innerHTML = `<td class="pad">` + `<a href="/join-room/${room_id}">`+
            `<button class="joingame" id="id_join_room_button">Room ${room_id}: ${room_player_1_username}</button></a></td>`

        roomTable.appendChild(room_row)
    }

    const challengeTable = document.createElement("table")
    challengeTable.setAttribute("id", "id_friends_challenge_table")
    for (let i = 0; i < challenges.length; i++) {
        let room_id = challenges[i].room_id
        let room_player_1_username = challenges[i].player_1_username
        let room_row = document.createElement("tr")

        room_row.innerHTML = `<td class="pad">` + 
            `<button class="friend-request" id="id_join_room_button">` +
            `Challenge request from:${room_player_1_username}` +
            `<a href="/join-room/${room_id}" class="challenge_button accept">Accept</a>` +
            `<a href="decline_challenge/${room_id}" class="challenge_button reject">Decline</a></button></td>`
        challengeTable.appendChild(room_row)
    }

    let linebreak = document.createElement("br");

    rooms_list.innerHTML = ""
    rooms_list.appendChild(challengeTable)
    if (has_requests) {
        for (let i=0; i<3; i++){
            rooms_list.appendChild(linebreak)
        }
    }

    rooms_list.appendChild(roomTable)
   
}

function displayError(message) {
    let errorElement = document.getElementById("error")
    errorElement.innerHTML = message
}

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}