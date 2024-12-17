from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Case, When, Value, CharField
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from authentication.models import Profile
from chessapp.models import Match, Note
from django.contrib.auth.models import User
from .utils.game_logic import ChessEngine
import json

# Core imports remain same...
def health_check(request):
    return JsonResponse({'status':"successfull"},status=200)

def about_page(request):
    return render(request, 'chess/about.html')

def rules_page(request):
    return render(request, 'chess/rules.html')

def history_page(request):
    return render(request, 'chess/history.html')

@login_required
def game_lobby(request):
    available_opponents = User.objects.exclude(id=request.user.id)
    player_matches = Match.objects.filter(player1=request.user)  
    
    page_context = {
        'users': available_opponents,
        'game_history': player_matches,
    }
    
    return render(request, 'chess/home.html', page_context)



@login_required
def fetch_matches(request):
    match_history = Match.objects.filter(  
        (Q(player1=request.user) | Q(player2=request.user)
         ) & ~(
        (Q(player1=request.user) & Q(delete_status="player1")) |
        (Q(player2=request.user) & Q(delete_status="player2"))
         )).exclude(
        status__in=['PENDING', 'INVITED', 'CANCELLED']  
    ).annotate(
        opponent_name=Case(
            When(player1=request.user, then=F('player2__username')),
            default=F('player1__username'),
            output_field=CharField()
        ),
        user_outcome=Case(
            When(result='DRAW', then=Value('DRAW')),  
            When(Q(player1=request.user, result='WIN') | Q(player2=request.user, result='LOSS'), 
                 then=Value('WIN')),
            When(Q(player1=request.user, result='LOSS') | Q(player2=request.user, result='WIN'), 
                 then=Value('LOSS')),
            default=F('result'),
            output_field=CharField()
        )
    ).values(
        'id', 'opponent_name', 'moves_count', 'user_outcome', 'player1__username', 
        'player2__username', 'result','status',
    ).order_by('-id')

    return JsonResponse({'game_history': list(match_history)})


@login_required
@csrf_exempt
def update_match(request, game_id):
    try:
        current_match = get_object_or_404(Match, id=game_id)  
        player_note = get_object_or_404(Note, match=current_match, player=request.user)
        
        if request.method == 'POST':
            payload = json.loads(request.body)
            player_note.text = payload.get('journal', '')  
            player_note.save()
            return JsonResponse({
                'status': True, 
                'message': 'Notes updated successfully'  
            })

        return render(request, 'chess/update-match.html', {'journal': player_note})  
    except Exception as e:
        return JsonResponse({
            'status': False, 
            'message': f'Failed to update notes: {str(e)}'
        }, status=400)

@login_required
def remove_game(request, game_id):  
    try:
        print(game_id,'removegame')
        target_game = get_object_or_404(Match, id=game_id)
        if target_game.delete_status!="":
            target_game.delete()

            return JsonResponse({'status': True, 'message': 'Game deleted successfully'})


        if target_game.player1==request.user:
            target_game.delete_status="player1"
        else:
            target_game.delete_status='player2'

        target_game.save()

        return JsonResponse({'status': True, 'message': 'Game deleted successfully'})
    except Exception as e:
        print(e)
        return JsonResponse({'status': False, 'message': 'Failed to delete game'})


@login_required
def match_detail(request, game_id):  
    current_match = get_object_or_404(Match, id=game_id)
    if request.user != current_match.player1 and request.user != current_match.player2:
        return redirect('game_lobby')
    player_journal = Note.objects.get(player=request.user, match=current_match)
    return render(request, 'chess/chessboard.html', {'game': current_match, 'note': player_journal})



@login_required
def start_match(request, game_id):
    current_match = Match.objects.filter(id=game_id).first()  
    # Update status from PENDING to ACTIVE
    current_match.status = 'ACTIVE'
    current_match.save()
    # Create note for the starting player (player1)
    Note.objects.get_or_create(  
        player=current_match.player1,
        match=current_match
    )
    return JsonResponse({
        'status': True,
        'message': 'Match has started'  
    })


def cancel_match(request, game_id):
    try:
        current_match = Match.objects.filter(id=game_id).first() 
        if current_match:
            current_match.status = 'CANCELLED'  
            current_match.is_active = False    
            current_match.save()
            return JsonResponse({
                'status': True, 
                'message': 'Match cancelled successfully'  
            })
        else:
            return JsonResponse({
                'status': False,
                'message': 'Match not found'
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': False, 
            'message': 'Failed to cancel match' 
        }, status=400)



