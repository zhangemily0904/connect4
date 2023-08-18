from ast import parse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import HttpResponse, Http404

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from connect4.forms import LoginForm, RegisterForm, ProfileForm, TokenForm
from connect4.models import Profile, Room

import json


def home_action(request):
    return render(request, 'connect4/home.html', { })

@login_required
def global_action(request):
    try: 
        new_profile = get_object_or_404(Profile, user=request.user) 

    except Http404:
        profile_picture = request.user.social_auth.get(provider='google-oauth2').extra_data['picture']
        nickname = request.user.social_auth.get(provider='google-oauth2').extra_data['fullname']
        new_profile = Profile(user=request.user, profile_picture=profile_picture, nickname=nickname)
        new_profile.save()

    if new_profile.room != None:
        # if user is already in a room, disable joining other rooms
        return render(request, 'connect4/global.html', {'rooms': [], 'game_status': "Resume game"})

    challenge_requests = []
    for room in Room.objects.all():
        if room.turn != -1 and room.player_2 == None and room.challenge == request.user:
            challenge_requests.append(room)    
 
    active_rooms = []
    for room in Room.objects.all():
        if room.turn != -1 and room.player_2 == None and room.challenge == None:
            active_rooms.append(room)

    return render(request, 'connect4/global.html', {'rooms': active_rooms, 'challenge_requests': challenge_requests, 'has_requests': len(challenge_requests)!=0, 'game_status': "Start a new game"})

@login_required
def join_room_action(request, room_id):
    
    room = get_object_or_404(Room, room_id=room_id)
    room.timeLeft = 120

    if room.player_2 != None:
        # if player_2 already joined room and refreshed 
        board = parse_board(room.board)
        radius = 38
        spacing = 12
        for r in range(6):
            for c in range(7):
                cx = c * 100 + radius + spacing
                cy = r * 100 + radius + spacing
                board[r][c] = {"token":board[r][c], "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy}

        context = {
            "room": room,
            "board": board,
            "player_1_pfp": Profile.objects.get(user=room.player_1).profile_picture,
            "player_2_pfp": Profile.objects.get(user=room.player_2).profile_picture,
            "endgame_p2": True,
        }
        return render(request, 'connect4/gameplay.html', context)

    board = []
    radius = 38
    spacing = 12
    for r in range(6):
        row = []
        for c in range(7):
            cx = c * 100 + radius + spacing
            cy = r * 100 + radius + spacing
            row.append({"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy})
        board.append(row)

    room.player_2 = request.user
    room.turn = 1
    room.status = "Player 1's turn"
    room.save()

    user_profile = get_object_or_404(Profile, user=request.user)
    user_profile.room = room
    
    user_profile.save()
    
    context = {
        "room": room,
        "board": board,
        "player_1_pfp": Profile.objects.get(user=room.player_1).profile_picture,
        "player_2_pfp": Profile.objects.get(user=room.player_2).profile_picture,
        "endgame_p2": True,
    }
    return render(request, 'connect4/gameplay.html', context)

@login_required
def create_room_action(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    
    if user_profile.room != None:  
    # when player_1 refreshes or when player is already in a game, redirect to current game
        room = user_profile.room

        slots = []
        radius = 38
        spacing = 12
        for r in range(6):
            row = []
            for c in range(7):
                cx = c * 100 + radius + spacing
                cy = r * 100 + radius + spacing
                row.append({"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy})
            slots.append(row)

        context = {
            "room":room,
            "board":slots,
            "player_1_pfp": Profile.objects.get(user=request.user).profile_picture,
        }
        if request.user == room.player_1:
            context["endgame_p1"] = True
        else:
            context["endgame_p2"] = True
        return render(request, 'connect4/gameplay.html', context)
    
    board = []
    radius = 38
    spacing = 12
    for r in range(6):
        row = []
        for c in range(7):
            cx = c * 100 + radius + spacing
            cy = r * 100 + radius + spacing
            row.append({"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy})
        board.append(row)
    
    room = Room(room_id=len(Room.objects.all()), 
                player_1=request.user,
                player_2=None,
                turn=0,
                board=","*41,
                status = "Waiting for opponent...")
    room.save()
    
    user_profile.room = room
    
    user_profile.save()

    context = {
        "room":room,
        "board":board,
        "player_1_pfp": Profile.objects.get(user=request.user).profile_picture,
        "endgame_p1": True,
    }
    return render(request, 'connect4/gameplay.html', context)

def _my_json_error_response(message, status=200):
    response_json = '{ "error": "' + message + '" }'
    return HttpResponse(response_json, content_type='application/json', status=status)

def get_all_json_dumps_serializer(request, room):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    if not room:
        return HttpResponse(json.dumps({}), content_type='application/json')

    player_2_username = "waiting!"
    if room.player_2 != None:
        player_2_username = room.player_2.username 
    
    player_1_profile = get_object_or_404(Profile, user=room.player_1)
    player_2_profile = get_object_or_404(Profile, user=room.player_2)

    if player_1_profile.token_picture.name != "":
        player_1_token_name = "/static/media/" + player_1_profile.token_picture.name
    else:
        player_1_token_name = "/static/red_token.png"
        
    
    if player_2_profile.token_picture.name != "":
        player_2_token_name = "/static/media/" + player_2_profile.token_picture.name
    else:
        player_2_token_name = "/static/yellow_token.jpeg"

    player_1_pfp = player_1_profile.profile_picture.name

    player_2_pfp = player_2_profile.profile_picture.name

    response_data = {
        "room_id": room.room_id,
        "board": room.board,
        "player_1_username": room.player_1.username,
        "player_2_username": player_2_username,
        "status": room.status,
        "turn": room.turn,
        "timeLeft": room.timeLeft,
        "player_1_token": player_1_token_name,
        "player_2_token": player_2_token_name,
        "player_1_pfp": player_1_pfp,
        "player_2_pfp": player_2_pfp,
    }

    response_json = json.dumps(response_data)

    return HttpResponse(response_json, content_type='application/json')

@login_required 
def get_global(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)
        
    user_profile = get_object_or_404(Profile, user=request.user) 
    
    if user_profile.room != None:
        # user is already in a game
        rooms_data = []
        challenge_requests = []
        game_status = "Resume game"
    else:
        active_rooms = [] 
        challenges = []
        for room in Room.objects.all():
            if room.turn != -1 and room.player_2 == None:
                if room.challenge == None:
                    active_rooms.append(room)
                else:
                    challenges.append(room)
            
        rooms_data = []
        challenge_requests = []

        for room in active_rooms:
            rooms_data.append(
                {"room_id": room.room_id,
                "player_1_username": room.player_1.username}
            )

        for room in challenges:
            challenge_requests.append(
                {"room_id": room.room_id,
                "player_1_username": room.player_1.username}
            )
        game_status = "Start a new game"
    
    response_data = {"rooms":rooms_data, "challenge_requests":challenge_requests, 'has_requests': len(challenge_requests)!=0, "game_status":game_status}

    response_json = json.dumps(response_data)

    return HttpResponse(response_json, content_type='application/json')

@login_required
def get_gameplay(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    # check if game has ended, unlink current player from room
    user_profile = get_object_or_404(Profile, user=request.user) 
    room = user_profile.room
    if room != None and room.turn == -1:
        user_profile.room = None
        user_profile.save()
    
    if room!= None and room.timeLeft > 0:
        room.timeLeft -= 1
        room.save()
        user_profile.save()
    

    return get_all_json_dumps_serializer(request, profile.room)

@login_required
def end_game(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    profile = get_object_or_404(Profile, user=request.user)
    room = profile.room
    role = ""

    if room.turn == -1:
        board = parse_board(room.board)
        radius = 38
        spacing = 12
        for r in range(6):
            for c in range(7):
                cx = c * 100 + radius + spacing
                cy = r * 100 + radius + spacing
                board[r][c] = {"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy}
        context = {
            "room":room,
            "board":board,
            "player_1_pfp": Profile.objects.get(user=request.user).profile_picture,
        }
        if room.player_2:
            context["player_2_pfp"] = Profile.objects.get(user=room.player_2).profile_picture
        return render(request, 'connect4/gameplay.html', context)

    if (room.player_1.id == request.user.id):
        role = "1"
        if room.player_2:
            winner = Profile.objects.get(user=room.player_2)
            winner.wins += 1
            winner.save()
    elif (room.player_2.id == request.user.id):
        role = "2"
        winner = Profile.objects.get(user=room.player_1)
        winner.wins += 1
        winner.save()
    else:
        # TODO: change error handling to display message to user
        raise Exception("This player is not supposed to make a move")

    board = parse_board(room.board)
    radius = 38
    spacing = 12
    for r in range(6):
        for c in range(7):
            cx = c * 100 + radius + spacing
            cy = r * 100 + radius + spacing
            board[r][c] = {"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy}
    
    room.turn = -1 #indicates game/room is no longer active
    room.status = f"Game over! (Player {role} forfeit)"
    
    room.save()

    context = {
        "room":room,
        "board":board,
        "player_1_pfp": Profile.objects.get(user=request.user).profile_picture,
    }
    if room.player_2:
        context["player_2_pfp"] = Profile.objects.get(user=room.player_2).profile_picture,
    return render(request, 'connect4/gameplay.html', context)

@login_required
def time_out(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    profile = get_object_or_404(Profile, user=request.user)
    room = profile.room
    context = {}
    if room:
        if (room.turn == 1):
            if room.player_2:
                winner = Profile.objects.get(user=room.player_2)
                winner.wins += 1
                winner.save()
                room.status = "Player 2 wins! (timeout)"
        elif (room.turn == 2):
            winner = Profile.objects.get(user=room.player_1)
            winner.wins += 1
            winner.save()
            room.status = "Player 1 wins! (timeout)"
        else:
            # TODO: change error handling to display message to user
            raise Exception("This player is not supposed to make a move")

        board = parse_board(room.board)
        radius = 38
        spacing = 12
        for r in range(6):
            for c in range(7):
                cx = c * 100 + radius + spacing
                cy = r * 100 + radius + spacing
                board[r][c] = {"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy}
        
        room.turn = -1 #indicates game/room is no longer active    
        room.save()

        context = {
            "room":room,
            "board":board,
            "player_1_pfp": Profile.objects.get(user=request.user).profile_picture,
        }
        if room.player_2:
            context["player_2_pfp"] = Profile.objects.get(user=room.player_2).profile_picture,
    return render(request, 'connect4/gameplay.html', context)

@login_required
def drop_token(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    if not 'column' in request.POST or not request.POST['column']:
        return _my_json_error_response("You must have a column to drop token.", status=400)

    if request.method != 'POST':
        return _my_json_error_response("You must use a POST request for this operation", status=405)

    profile = get_object_or_404(Profile, user=request.user)
    room = profile.room
    role = ""

    if (room.player_1.id == request.user.id) and room.turn == 1:
        role = "1"
    elif (room.player_2.id == request.user.id) and room.turn == 2:
        role = "2"
    else:
        # TODO: change error handling to display message to user
        raise Exception("This player is not supposed to make a move")

    room_id = room.room_id
    column = int(request.POST["column"])

    board = parse_board(room.board)

    saved_row = -1
    for row in range(6):
        if row == 5: #bottom row (column is empty)
            board[row][column] = role
            saved_row = row
            break
        elif board[row+1][column] != "":
            board[row][column] = role
            saved_row = row
            break
    
    board_str = assemble_board(board)
    room.board = board_str

    if (check_horizontal(board, saved_row) or check_vertical(board, column) or check_diagonal(board, saved_row, column)):
        # then current player wins
        room.turn = -1 #indicates game/room is no longer active
        if role == "1":
            player_1 = Profile.objects.get(user=room.player_1)
            player_1.wins += 1
            player_1.save()
            room.status = "Player 1 wins!"
        else:
            player_2 = Profile.objects.get(user=room.player_2)
            player_2.wins += 1
            player_2.save()
            room.status = "Player 2 wins!"

    else:
        if room.turn == 1:
            room.turn = 2
            room.status = "Player 2's turn"
        elif room.turn == 2:
            room.turn = 1
            room.status = "Player 1's turn"
        room.timeLeft = 120
    
    room.save()

    return get_all_json_dumps_serializer(request, room)

def check_horizontal(board, row):
    for col in range(4):
        if (check_same_player(board[row][col], board[row][col+1], board[row][col+2], board[row][col+3])):
            return True
    return False


def check_vertical(board, col):
    for row in range(3):
        if (check_same_player(board[row][col], board[row+1][col], board[row+2][col], board[row+3][col])):
            return True
    return False

# check both diagonals
def check_diagonal(board, row, col):

    if row < col:
        start_col = col-row
        start_row = 0
    else:
        start_row = row-col
        start_col = 0
    
    while start_col < 4 and start_row < 3:
        if check_same_player(board[start_row][start_col], board[start_row+1][start_col+1], board[start_row+2][start_col+2], board[start_row+3][start_col+3]):
            return True
        start_col += 1
        start_row += 1
    

    start_row = max(row+col - 6, 0)
    start_col = min(row+col, 6)

    while start_col > 2 and start_row < 3:
        if check_same_player(board[start_row][start_col], board[start_row+1][start_col-1], board[start_row+2][start_col-2], board[start_row+3][start_col-3]):
            return True
        start_row += 1
        start_col -= 1

    return False

def check_same_player(c1, c2, c3, c4):
    return c1 == c2 and c2 == c3 and c3 == c4 and c1 != ""

def parse_board(board):
    split_board = board.split(",")
    assert(len(split_board) == 42)

    board_2d = []
    counter = 0
    for row in range(6):
        board_row = []
        for col in range(7):
            board_row.append(split_board[counter])
            counter += 1
        board_2d.append(board_row)
    
    return board_2d

def assemble_board(board_2d):
    flattened_board = []
    for row in board_2d:
        flattened_board.extend(row)
    
    board = ",".join(flattened_board)

    return board


@login_required
def leaderboard_action(request):
    profiles = Profile.objects.all().order_by('-wins')
    profile_data = []

    for i, profile in enumerate(profiles):
        profile_data.append(
            {"nickname": profile.nickname,
            "wins": profile.wins,
            "pfp": profile.profile_picture,
            "rank": i+1,
            "user_id": profile.user.id
            }
        )
    return render(request, 'connect4/leaderboard.html', {'profiles' : profile_data})

@login_required
def profile_action(request):
    if request.method == 'GET':
        context = {
            'profile': request.user.profile,
            'form': ProfileForm(initial={'bio': request.user.profile.bio})
        }
        context = {
            'profile': request.user.profile, 
            'profile_form': ProfileForm(initial={'bio': request.user.profile.bio, 'nickname': request.user.profile.nickname}),
            'token_form': TokenForm(initial={'token': request.user.profile.token_picture})}
        return render(request, 'connect4/profile.html', context)
    
    profile = get_object_or_404(Profile, user=request.user)

    profile_form = ProfileForm(request.POST, request.FILES)
    token_form = TokenForm(request.POST, request.FILES)

    profile = request.user.profile

    if profile_form.is_valid():
        bio_text = profile_form.cleaned_data['bio']
        nickname_text = profile_form.cleaned_data['nickname']

        profile.bio = bio_text
        profile.nickname = nickname_text
    else:
        profile_form = ProfileForm(initial={'bio': request.user.profile.bio, 'nickname': request.user.profile.nickname})
    
    if token_form.is_valid():
        token_pic = token_form.cleaned_data['token_picture']
        
        if token_pic is not None:
            profile.token_picture = token_pic
            profile.content_type = token_pic.content_type
    else:
        profile_form = TokenForm(initial={'token': request.user.profile.token_picture})
    
    profile.save()

    context = {'profile': profile, 'profile_form': profile_form, 'token_form': token_form}
    return render(request, 'connect4/profile.html', context)

@login_required
def friend_profile_action(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'connect4/friend_profile.html', {'profile': user.profile})


@login_required
def get_token_photo(request, user_id):
    profile = get_object_or_404(Profile, id=user_id)
    return HttpResponse(profile.token_picture, content_type=profile.content_type)

@login_required
def unfriend(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)

    if request.method != 'POST':
        return redirect("/friend_profile/"+user_id)
        
    request.user.profile.following.remove(user_to_unfollow)
    request.user.profile.save()
    user_to_unfollow.profile.following.remove(request.user)
    user_to_unfollow.profile.save()
    return redirect("/friend_profile/"+str(user_id))

@login_required
def friend(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)

    if request.method != 'POST':
        return redirect("/friend_profile/"+user_id)

    request.user.profile.following.add(user_to_follow)
    request.user.profile.save()
    return redirect("/friend_profile/"+str(user_id))

@login_required
def challenge(request, user_id):
    user_to_challenge = get_object_or_404(User, id=user_id)
    user_profile = request.user.profile

    if user_profile.room != None:  
        return redirect('/friends')
    
    board = []
    radius = 38
    spacing = 12
    for r in range(6):
        row = []
        for c in range(7):
            cx = c * 100 + radius + spacing
            cy = r * 100 + radius + spacing
            row.append({"token":"", "id": f"slot_{r}_{c}", "radius": radius, "cx": cx, "cy": cy})
        board.append(row)
    
    room = Room(room_id=len(Room.objects.all()), 
                player_1=request.user,
                player_2=None,
                turn=0,
                board=","*41,
                status = "Waiting for opponent...")
    room.challenge = user_to_challenge
    room.save()
    
    user_profile.room = room
    
    user_profile.save()

    context = {
        "room":room,
        "board":board,
        "player_1_pfp": Profile.objects.get(user=request.user).profile_picture,
        "endgame_p1": True,
    }

    return redirect('/friends')

@login_required
def decline_challenge(request, room_id):
    room = Room.objects.get(room_id=room_id)
    room.turn = -1
    room.save()
    profile = Profile.objects.get(id=room.player_1.id)
    profile.room = None
    profile.save()
    return redirect('/global')

@login_required
def cancel_challenge(request, room_id):
    room = Room.objects.get(room_id=room_id)
    room.turn = -1
    room.save()
    profile = Profile.objects.get(id=request.user.id)
    profile.room = None
    profile.save()
    return redirect('/friends')


@login_required
def friends_action(request):
    profiles = []
    request_user = Profile.objects.get(user=request.user)
    for user in request_user.following.all():
        if request.user in user.profile.following.all():
            profiles.append(Profile.objects.get(user=user))
    profile_data = []

    for i, profile in enumerate(profiles):
        profile_data.append(
            {"nickname": profile.nickname,
            "wins": profile.wins,
            "pfp": profile.profile_picture,
            "rank": i+1,
            "user_id": profile.user.id,
            }
        )
        
    
    requests = []
    request_user = Profile.objects.get(user=request.user)
    for request_profile in Profile.objects.all():
        if request.user in request_profile.following.all() and request_profile.user not in request.user.profile.following.all():
            requests.append(request_profile)
    
    requests_data = []

    for i, r in enumerate(requests):
        requests_data.append(
            {"nickname": r.nickname,
            "pfp": r.profile_picture,
            "rank": i+1,
            "user_id": r.user.id,
            }
        )
 
    return render(request, 'connect4/friends.html', {'profiles' : profile_data, 'requests': requests_data, 'has_requests': len(requests_data)!=0, 'room': request_user.room})

    
    