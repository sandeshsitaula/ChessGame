from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now
import json
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

class HomeWebSocketView(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')  
        query_params = parse_qs(query_string)  
        user_id = query_params.get('user_id', [None])[0]  

        if user_id:
            profile = await self.get_user_by_id(user_id)
            self.scope['profile'] = profile
        await self.accept()

        self.group_name = f'{user_id}'

        print(f"WebSocket connection established for user: {user_id}")
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            profile = self.scope['profile']
            data=json.loads(text_data)
            if data.get('type')=='heartbeat':
                await self.save_profile()
                return

            if data.get('type')=='intialLoad':
                players_list=await self.fetch_players(profile)
                await self.send(json.dumps({"status": "success",'type':"intial_load",'response':{'users':players_list}}))

            if data.get('type')=='players_list':
                players_list=await self.fetch_players(profile)
                await self.send(json.dumps({"status": "success",'type':"players_list",'response':{'users':players_list}}))

            if data.get('type')=='send_challenge':
                challenge_response=await self.handle_send_challenge(data)
                if not challenge_response['status']:
                    await self.send(json.dumps({'type':'error','message':challenge_response['message']}))

                await self.send(json.dumps({'type':"send_challenge","message":challenge_response['message']}))
                await self.channel_layer.group_send(
                    f'{challenge_response['opponent']}',{
                        'type':'send_challenge',
                    }
                )

            if data.get('type')=='pending_challenges':
                pending_challenges=await self.check_pending_challenges(profile)
                await self.send(json.dumps({"status": "success",'type':"pending_challenges",'response':{'challenges':pending_challenges}}))

            if data.get('type')=='game_status':
                active_games=await self.check_active_games(profile)
                await self.send(json.dumps({"status": "success",'type':"game_status",'response':{'games':active_games}}))

            if data.get('type')=="accept_invite":
                accept_invite_response=await self.handle_accept_invite(data)
                await self.send(json.dumps({'type':"accept_invite",'match_id':data.get('match_id')}))
                await self.channel_layer.group_send(
                    f'{accept_invite_response['opponent']}',{
                        'type':'accept_invite',
                        'match_id':data.get('match_id')
                    }
                )

        except Exception as e:
            print(e)
            await self.send(json.dumps({"status": False}))

    async def send_challenge(self,event):
        await self.send(json.dumps({'type':'challenge_received'}))

    async def accept_invite(self,event):
        await self.send(json.dumps({'type':'invite_accepted','match_id':event['match_id']}))

    @database_sync_to_async
    def handle_accept_invite(self,data):
        from .models import Match,Note
        current_user=self.scope['profile'].user
        match_id=data.get('match_id')
        current_match = Match.objects.filter(
            id=match_id,
            status='INVITED'
        ).first()
        
        current_match.status = 'PENDING'
        current_match.save()
        
        # Create note for accepting player
        Note.objects.get_or_create(  
            player=current_user,      
            match=current_match        
        )
        
        return {
            'status': True,
            'match_id': current_match.id  ,
            'opponent':current_match.player1.id
        }


    @database_sync_to_async
    def handle_send_challenge(self,data):
        from django.contrib.auth.models import User
        from django.db.models import Q
        from .models import Match
        user_id=data.get('user_id')
        current_user=self.scope['profile'].user
        target_player = User.objects.get(id=user_id)
        
        active_match = Match.objects.filter(  
            (Q(player1=current_user) | Q(player2=current_user) | 
             Q(player1=target_player) | Q(player2=target_player)) &
            Q(status='ACTIVE')  
        ).first()

        if active_match:
            if active_match.player1 == current_user or active_match.player2 == current_user:
                return {
                    'status': False, 
                    'message': 'Complete your current match before starting a new one',
                    'ongoing': 'Player'
                }
            else:
                return {
                    'status': False, 
                    'message': 'Selected player is currently in another match',
                    'ongoing': 'Opponent'
                }
        
        new_match = Match.objects.create(
            player1=current_user, 
            player2=target_player, 
            status='INVITED'  
        )
        return {
            'status': True,
            'message': 'Challenge sent successfully',
            'opponent':user_id,
            'game_id': new_match.id
        }



    @database_sync_to_async
    def save_profile(self):
        profile=self.scope['profile']
        profile.last_activity = now()
        profile.save()

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        from django.contrib.auth.models import User

        user=User.objects.get(id=user_id).profile
        user.last_activity=now()
        user.save()
        return user

    @database_sync_to_async
    def fetch_players(self,profile):
        from authentication.models import Profile
        from chessapp.models import Match
        from django.contrib.auth.models import User
        user=profile.user
        running_matches = Match.objects.filter(status='ACTIVE')  

        busy_players1 = running_matches.values_list('player1', flat=True)
        busy_players2 = running_matches.values_list('player2', flat=True)

        occupied_users = set(busy_players1).union(set(busy_players2))
        occupied_users.add(user.id)

        timeout_threshold = timezone.now() - timedelta(minutes=2)
        inactive_users = Profile.objects.filter(
            last_activity__lt=timeout_threshold
        ).values_list('user__id', flat=True)

        unavailable_ids = occupied_users.union(set(inactive_users))
        available_players = User.objects.exclude(id__in=unavailable_ids).values('id', 'username')
        return list(available_players)

    @database_sync_to_async
    def check_active_games(self,profile):
        from chessapp.models import Match
        from django.db.models import Q

        active_matches = Match.objects.filter(
            (Q(player1=profile.user)|Q(player2=profile.user)) &
            (Q(status='PENDING') | Q(status='ACTIVE')
        )).values('id')
        return list(active_matches)

    @database_sync_to_async
    def check_pending_challenges(self,profile):
        from chessapp.models import Match
        from django.db.models import Q

        pending_challenges = Match.objects.filter(
            Q(player2=profile.user) &
            Q(status='INVITED') 
              ).values(
        'id', 
        'player1__username'   
    )
        return list(pending_challenges)

##another websocket

class ChessWebSocketView(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')  
        query_params = parse_qs(query_string)  
        user_id = query_params.get('user_id', [None])[0]  
        self.match_id = query_params.get('match_id', [None])[0]  
        self.group_name = f'match_{self.match_id}'

        if user_id:
            profile = await self.get_user_by_id(user_id)
            self.scope['profile'] = profile

        await self.accept()

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"[GameConsumer] WebSocket connection closed for match {self.match_id}")



    async def receive(self, text_data):
        try:
            incoming_data=json.loads(text_data)
            if incoming_data.get('type')=="chess_move":
                move_response=await self.handle_chess_move(incoming_data)

                if (not move_response['status']):
                    await self.send(text_data=json.dumps({'type':'error','message':move_response['message']}))
                    return
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chess_move',
                        'data':move_response,
                    }
                )

            elif incoming_data.get('type')=='intialBoard':
                intial_board_response=await self.handle_intial_board()
                await self.send(text_data=json.dumps({
                    'type': 'chess_move',
                    'board_state':intial_board_response['board_state'],
                    'current_turn': intial_board_response['current_turn'],
                    'is_game_over': intial_board_response['is_game_over'],
                    'winner':intial_board_response['winner']
                    }))

            elif incoming_data.get('type')=="forfeit_match":
                response=await  self.handle_forfeit_match()
                if not response['status']:
                    await self.send(json.dumps({'type':'error','message':response['message']}))
                print("response",response )
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type':'forfeit_match',
                        'forfeit_username':response['username']
                    }
                )

        except Exception as e:
            print(e)
            await self.send(json.dumps({"status": False}))

    async def forfeit_match(self,event):
        await self.send(text_data=json.dumps({'type':'forfeit_match','username':event['forfeit_username']}))



    @database_sync_to_async
    def handle_forfeit_match(self):
        from .models import Match
        current_user=self.scope['profile'].user
        match_id=self.match_id
        current_match = Match.objects.get(id=match_id)
        if not current_match.is_active:
            return {
                'status':False,
                'message':"Game is already over"
            }
        current_match.is_active = False
        current_match.status = 'ENDED'

        # Set result and winner based on who resigned
        if current_user == current_match.player1:
            current_match.result = 'LOSS'
            current_match.winner = current_match.player2
        else:
            current_match.result = 'WIN'
            current_match.winner = current_match.player1
        current_match.save()
        return {
            'status':True,
            'username':current_user.username, 
        }

    @database_sync_to_async
    def handle_intial_board(self):
        from .models import Match
        from .utils.game_logic import ChessEngine
        match_id=self.match_id
        current_match = Match.objects.get(id=match_id)

        match_engine = ChessEngine(current_match)  
        current_player = current_match.player1.username if current_match.moves_count % 2 == 0 else current_match.player2.username
        winner=""
        if current_match.winner:
            winner=current_match.winner
        return{
                'status': True,
                'is_game_over': not current_match.is_active,
                'winner': winner,
                'board_state':match_engine.get_board_position(),
                'current_turn':current_player,
            }

    @database_sync_to_async
    def handle_chess_move(self,data):
        from .utils.game_logic import ChessEngine
        from chessapp.models import Match

        from_pos = data['from']
        to_pos = data['to']
        current_match = Match.objects.get(id=self.match_id)  
        match_engine = ChessEngine(current_match)  
        
        if not current_match.is_active:
            return {'status': False, 'message': 'This match has ended'}
        
        if match_engine.validate_move(from_pos, to_pos):
            match_engine.execute_move(from_pos, to_pos)
            
            winner=""
            if match_engine.is_match_over():
                current_match.is_active = False
                result = match_engine.get_match_result()
                if result == '1-0':
                    current_match.status = 'ENDED'
                    current_match.result = 'WIN' 
                    current_match.winner = current_match.player1
                elif result == '0-1':
                    current_match.status = 'ENDED'
                    current_match.result = 'LOSS'
                    current_match.winner = current_match.player2
                else:
                    current_match.status = 'ENDED'
                    current_match.result = 'DRAW'
                    current_match.winner = None
                current_match.save()
                winner=current_match.winner.username
            current_player = current_match.player1.username if current_match.moves_count % 2 == 0 else current_match.player2.username

            
            return{
                'status': True,
                'is_game_over': not current_match.is_active,
                'winner': winner,
                'board_state':match_engine.get_board_position(),
                'current_turn':current_player,
            }
        return{'status':False,
               'message':"Illegal move"}


    
    async def chess_move(self,event):
        print('sending group response for chess movement')
        print(event,'event here during chess move')
        await self.send(text_data=json.dumps({
            'type': 'chess_move',
            'board_state':event['data']['board_state'],
            'current_turn': event['data']['current_turn'],
            'is_game_over': event['data']['is_game_over'],
            'winner':event['data']['winner']
        }))

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        from django.contrib.auth.models import User
        return User.objects.get(id=user_id).profile
