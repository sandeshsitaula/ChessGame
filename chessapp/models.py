from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Match(models.Model):  # Changed from Game
    GAME_STATUS = [
        ('INVITED', 'Invited'),
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('ENDED', 'Ended'),
        ('CANCELLED', 'Cancelled'),
    ]
    RESULT_STATUS = [
        ('WIN', 'Win'),
        ('LOSS', 'Loss'),
        ('DRAW', 'Draw'),
        ('NONE', 'None'),
    ]
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_player1')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_player2')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won')
    moves_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=GAME_STATUS, default='INVITED')
    result = models.CharField(max_length=20, choices=RESULT_STATUS, default='NONE')
    started_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    board_state = models.TextField(default='')
    delete_status=models.CharField(max_length=20,default="")
    
    def __str__(self):
        return f"Match between {self.player1.username} and {self.player2.username}"

class Note(models.Model):  
    text = models.TextField(blank=True)
    match = models.ForeignKey(Match, related_name='match_notes', on_delete=models.CASCADE, blank=True, null=True)
    player = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"Note by {self.player.username} - Match {self.match.id}"
